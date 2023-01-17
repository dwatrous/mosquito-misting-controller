# Copyright MosquitoMax 2022, all rights reserved

import logging
import atexit
import datetime
import constants
from math import floor
import sched, time
import multiprocessing
import json
from environment import environment
from firebase_admin import firestore
import cloud

import sys, os
if sys.platform == 'linux':
    if os.uname().nodename == 'raspberrypi':
        onpi = True
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)             # choose BCM or BOARD
        GPIO.setup(constants.GPIO_CHEMICAL_VALVE, GPIO.OUT)
        GPIO.setup(constants.GPIO_WATER_VALVE, GPIO.OUT)
        GPIO.setup(constants.GPIO_COMPRESSOR, GPIO.OUT)
        atexit.register(GPIO.cleanup)
else:
    onpi = False
    GPIO = object

logging.info("On Raspberry Pi: ", onpi)

class zone:
    ms_in_second = 1000
    valve_scheduler = sched.scheduler()

    def __init__(self, zonedefinition=None) -> None:
        self.env = environment()
        self.spraydata = {}

        if zonedefinition == None:
            self.name = "Default"
            self.reset_to_defaults()
            return

        # if a JSON was passed directly, change it to a dict
        if type(zonedefinition) is not dict:
            zonedefinition = json.loads(zonedefinition)
    
        # hydrate based on zonedefinition
        self.name = zonedefinition["name"]
        self.nozzlecount = zonedefinition["nozzlecount"]
        self.chemicalclass = zonedefinition["chemicalclass"]
        self.sprayduration_ms = zonedefinition["sprayduration_ms"]
        self.sprayoccurrences = zonedefinition["sprayoccurrences"]
        self.valve_first_open_offset_ms = zonedefinition["valve_first_open_offset_ms"]
        self.valve_activation_interval_ms = zonedefinition["valve_activation_interval_ms"]
        self.low_temp_threshold_f = zonedefinition["low_temp_threshold_f"]
        self.rain_threshold_in = zonedefinition["rain_threshold_in"]


    def get_zonedefinition(self):
        zonedefinition = {
            "name": self.name,
            "nozzlecount": self.nozzlecount,
            "chemicalclass": self.chemicalclass,
            "sprayduration_ms": self.sprayduration_ms,
            "sprayoccurrences": self.sprayoccurrences,
            "valve_first_open_offset_ms": self.valve_first_open_offset_ms,
            "valve_activation_interval_ms": self.valve_activation_interval_ms,
            "low_temp_threshold_f": self.low_temp_threshold_f,
            "rain_threshold_in": self.rain_threshold_in
        }
        return zonedefinition

    def get_zonedefinition_json(self):
        return json.dumps(self.get_zonedefinition())

    def calculate_valve_openings(self):
        # return array of open times and duration [(open_time_ms, open_duration_ms), ...]
        valve_openings = []
        # get milliseconds to open based on chemical class and nozzle quantity
        valve_open_duration_ms = constants.VALVE_OPEN_DURATION[self.chemicalclass][self.nozzlecount]
        # add first open time and duration
        valve_openings.append({"open_at": self.valve_first_open_offset_ms, "open_for": valve_open_duration_ms})
        # add remaining times based on 
        number_valve_openings = floor(self.sprayduration_ms/self.valve_activation_interval_ms)
        for opening in range(1, number_valve_openings):
            valve_opening = {
                "open_at": self.valve_activation_interval_ms * opening + self.valve_first_open_offset_ms,
                "open_for": valve_open_duration_ms
            }
            valve_openings.append(valve_opening) 
        return valve_openings

    def open_valve(self, valve, close_after_ms=700):
        # record start time in ms
        open_time = time.time()*self.ms_in_second
        try:
            # open valve
            if valve == constants.VALVE_WATER and onpi:
                GPIO.output(constants.GPIO_WATER_VALVE, 0)
            elif valve == constants.VALVE_CHEMICAL and onpi:
                GPIO.output(constants.GPIO_CHEMICAL_VALVE, 0)
            else:
                if onpi:
                    logging.error("Invalid valve: %d" % valve)
                else:
                    logging.info("Opened valve %d (not on pi)" % valve)
            
            # leave valve open for close_after_ms
            time.sleep(close_after_ms/self.ms_in_second)

            if valve == constants.VALVE_WATER and onpi:
                GPIO.output(constants.GPIO_WATER_VALVE, 1)
            elif valve == constants.VALVE_CHEMICAL and onpi:
                GPIO.output(constants.GPIO_CHEMICAL_VALVE, 1)
            else:
                if onpi:
                    logging.error("Invalid valve: %d" % valve)
                else:
                    logging.info("Closed valve %d (not on pi)" % valve)
        except:
            GPIO.output(constants.GPIO_WATER_VALVE, 1)
            GPIO.output(constants.GPIO_CHEMICAL_VALVE, 1)

        # record close time in ms
        close_time = time.time()*self.ms_in_second
        valve_opening = {
            "valve": valve,
            "open_time": open_time,
            "close_time": close_time,
            "total_valve_time": close_time-open_time
        }
        self.spraydata["valve_executions"].append(valve_opening)
        logging.info(valve_opening)

    def run_compressor(self, close_after_ms):
        compressor_start_time = time.time()*self.ms_in_second

        try:
            if onpi: GPIO.output(constants.GPIO_COMPRESSOR, 0)
            time.sleep(close_after_ms/self.ms_in_second)
            if onpi: GPIO.output(constants.GPIO_COMPRESSOR, 1)
        except:
            if onpi: GPIO.output(constants.GPIO_COMPRESSOR, 1)

        compressor_shutoff_time = time.time()*self.ms_in_second
        self.spraydata["compressor_timing"] = {
            "compressor_start_time": compressor_start_time,
            "compressor_shutoff_time": compressor_shutoff_time,
            "total_compressor_run_time": compressor_shutoff_time-compressor_start_time
        }
        logging.info(self.spraydata["compressor_timing"])

    # execute spray
    @cloud.write_to_cloud
    def execute_spray(self):
        # clear and begin capturing data
        self.spraydata = {
            "start_time": firestore.SERVER_TIMESTAMP,
            "valve_executions": []
        }
        # decide whether to spray at all
        low_temp_last_24hr = self.env.get_low_temp_last_24hr()
        low_temp_next_24hr = self.env.get_low_temp_next_24hr()
        rain_prediction_next_24hr = self.env.get_rain_prediction_next_24hr()["inches"]
        self.spraydata["low_temp_last_24hr"] = low_temp_last_24hr
        self.spraydata["low_temp_next_24hr"] = low_temp_next_24hr
        self.spraydata["rain_prediction_next_24hr"] = rain_prediction_next_24hr
        if low_temp_last_24hr < self.low_temp_threshold_f or low_temp_next_24hr < self.low_temp_threshold_f:
            # handle temperature skip
            self.spraydata["skip_temperature"] = True
            logging.info("SKIP: Temperature")
            logging.info(self.spraydata["low_temp_last_24hr"])
            logging.info(self.spraydata["low_temp_next_24hr"])
            return
        if rain_prediction_next_24hr > self.rain_threshold_in:
            # handle rain skip
            self.spraydata["skip_rain"] = True
            logging.info("SKIP: Rain")
            logging.info(self.spraydata["rain_prediction_next_24hr"])
            return
        if False:   # TODO implement wind skip
            # handle wind skip
            pass

        # calculate valve openings
        valve_openings = self.calculate_valve_openings()
        self.spraydata["valve_openings"] = valve_openings
        # start compressor
        spray_start_time = time.time()*self.ms_in_second
        activate_compressor = multiprocessing.Process(target=self.run_compressor, kwargs={"close_after_ms": self.sprayduration_ms})
        activate_watervalve = multiprocessing.Process(target=self.open_valve, kwargs={"valve": constants.VALVE_WATER, "close_after_ms": self.sprayduration_ms})
        # schedule valve openings
        for valve_opening in valve_openings:
            # the multiple of self.ms_in_second are to convert between seconds and milliseconds
            self.valve_scheduler.enter(valve_opening["open_at"]/self.ms_in_second, 1, self.open_valve, kwargs={"valve": constants.VALVE_CHEMICAL, "close_after_ms": valve_opening["open_for"]})
        # start everything
        activate_compressor.start()
        activate_watervalve.start()
        self.valve_scheduler.run()  # runs synchronously
        #wait for everything to complete
        activate_compressor.join()
        activate_watervalve.join()
        spray_end_time = time.time()*self.ms_in_second
        self.spraydata["spray_timing"] = {
            "spray_start_time": spray_start_time,
            "spray_end_time": spray_end_time,
            "total_spray_time": spray_end_time-spray_start_time
        }
        logging.info(self.spraydata["spray_timing"])

    # Functions to add sprayoccurrences
    def add_spray_occurrence (self, dayofweek, timeofday):
        occurrence = {"dayofweek": dayofweek, "timeofday": timeofday}
        if occurrence not in self.sprayoccurrences:
            self.sprayoccurrences.append(occurrence)
    
    def add_sprayoccurrences_all_days (self, timeofday):
        for dayofweek in range(7):
            self.add_spray_occurrence(dayofweek, timeofday)

    def add_sprayoccurrences_weekdays (self, timeofday):
        for dayofweek in range(1,6):
            self.add_spray_occurrence(dayofweek, timeofday)
    
    def remove_sprayoccurrence(self, sprayoccurrence_remove):
        for i in range(len(self.sprayoccurrences)):
            if sprayoccurrence_remove == self.sprayoccurrences[i]:
                return self.sprayoccurrences.pop(i)
        return None


    # Functions to generate valid timeofday values
    def generate_fixedtime (self, hourofday):
        return {"type": "fixedtime", "value": datetime.time(hourofday)}

    def generate_relativetime (self, sunevent, sunposition, deltaminutes):
        return {"type": "relativetime", "value": {"sunevent": sunevent, "sunposition": sunposition, "deltaminutes": deltaminutes}}

    # clear sprayoccurrences
    def clear_sprayoccurrences (self):
        self.sprayoccurrences = []
    
    # reset everything to defaults
    def reset_to_defaults (self):
        self.nozzlecount = constants.default_nozzlecount
        self.chemicalclass = constants.CHEMICALCLASS2
        self.sprayduration_ms = constants.default_sprayduration_ms
        self.sprayoccurrences = constants.generate_default_sprayoccurrences()
        self.valve_first_open_offset_ms = constants.default_valve_first_open_offset_ms
        self.valve_activation_interval_ms = constants.default_valve_activation_interval_ms
        self.low_temp_threshold_f = constants.default_low_temp_threshold_f
        self.rain_threshold_in = constants.default_rain_threshold_in

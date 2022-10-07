# Copyright MosquitoMax 2022, all rights reserved

import datetime
import constants
from math import floor
import sched, time
import multiprocessing

class zone:
    name = "Default"
    nozzlecount = 30
    chemicalclass = constants.CHEMICALCLASS2
    sprayduration_ms = 45000
    # [
    #   {
    #       "dayofweek": INT[0-6], 
    #       "timeofday": 
    #           {
    #               "type": "fixedtime|relativetime",
    #               "value": 
    #                   datetime.time
    # OR
    #                   {"sunevent": "sunrise|sunset", "sunposition": "before|after", "deltaminutes": "XX in minutes"}
    #           }
    #   },
    # ...]
    sprayoccurrences = []
    # valve timing
    valve_first_open_offset_ms = 500
    valve_activation_interval_ms = 5000
    valve_scheduler = sched.scheduler()
    ms_in_second = 1000

    def calculate_valve_openings(self):
        # return array of open times and duration [(open_time_ms, open_duration_ms), ...]
        valve_openings = []
        # get milliseconds to open based on chemical class and nozzle quantity
        valve_open_duration_ms = constants.VALVE_OPEN_DURATION[self.chemicalclass][self.nozzlecount]
        # add first open time and duration
        valve_openings.append((self.valve_first_open_offset_ms, valve_open_duration_ms))
        # add remaining times based on 
        number_valve_openings = floor(self.sprayduration_ms/self.valve_activation_interval_ms)
        for opening in range(1, number_valve_openings):
            valve_openings.append((self.valve_activation_interval_ms * opening + self.valve_first_open_offset_ms, valve_open_duration_ms)) 
        return valve_openings

    def open_valve(self, valve, close_after_ms=700):
        # record start time in ms
        open_time = time.time()*self.ms_in_second
        # open valve
        if valve == constants.VALVE_WATER:
            print("water valve open")
        elif valve == constants.VALVE_CHEMICAL:
            print("chemical valve open")
        else:
            print("Invalid valve", valve)
            return
        
        # leave valve open for close_after_ms
        time.sleep(close_after_ms/self.ms_in_second)

        if valve == constants.VALVE_WATER:
            print("water valve close")
        elif valve == constants.VALVE_CHEMICAL:
            print("chemical valve close")
        else:
            print("Invalid valve (shouldn't happen)", valve)

        # record close time in ms
        close_time = time.time()*self.ms_in_second
        print("valve %d opened at %d and closed at %d for a total of %.1f" % (valve, open_time, close_time, close_time-open_time))

    def run_compressor(self, close_after_ms):
        compressor_start_time = time.time()*self.ms_in_second
        print("start compressor")
        time.sleep(close_after_ms/self.ms_in_second)
        print("shutoff_compressor")
        compressor_shutoff_time = time.time()*self.ms_in_second
        print("compressor started at %d and closed at %d for a total of %d" % (compressor_start_time, compressor_shutoff_time, compressor_shutoff_time-compressor_start_time))

    # execute spray
    def execute_spray(self):
        # calculate valve openings
        valve_openings = self.calculate_valve_openings()
        # start compressor
        spray_start_time = time.time()*self.ms_in_second
        activate_compressor = multiprocessing.Process(target=self.run_compressor, kwargs={"close_after_ms": self.sprayduration_ms})
        activate_watervalve = multiprocessing.Process(target=self.open_valve, kwargs={"valve": constants.VALVE_WATER, "close_after_ms": self.sprayduration_ms})
        # schedule valve openings
        for valve_opening in valve_openings:
            # the multiple of self.ms_in_second are to convert between seconds and milliseconds
            self.valve_scheduler.enter(valve_opening[0]/self.ms_in_second, 1, self.open_valve, kwargs={"valve": constants.VALVE_CHEMICAL, "close_after_ms": valve_opening[1]})
        # start everything
        activate_compressor.start()
        activate_watervalve.start()
        self.valve_scheduler.run()  # runs synchronously
        #wait for everything to complete
        activate_compressor.join()
        activate_watervalve.join()
        spray_end_time = time.time()*self.ms_in_second
        print("spray started at %d and closed at %d for a total of %d" % (spray_start_time, spray_end_time, spray_end_time-spray_start_time))

    # Functions to add sprayoccurrences
    def add_spray_occurrence (self, dayofweek, timeofday):
        occurrence = {"dayofweek": dayofweek, "timeofday": timeofday}
        if occurrence not in self.sprayoccurrences:
            self.sprayoccurrences.append(occurrence)
    
    def add_spray_occurrences_all_days (self, timeofday):
        for dayofweek in range(7):
            self.add_spray_occurrence(dayofweek, timeofday)

    def add_spray_occurrences_weekdays (self, timeofday):
        for dayofweek in range(1,6):
            self.add_spray_occurrence(dayofweek, timeofday)

    # Functions to generate valid timeofday values
    def generate_fixedtime (self, hourofday):
        return {"type": "fixedtime", "value": datetime.time(hourofday)}

    def generate_relativetime (self, sunevent, sunposition, deltaminutes):
        return {"type": "relativetime", "value": {"sunevent": sunevent, "sunposition": sunposition, "deltaminutes": deltaminutes}}

    # clear sprayoccurrences
    def clear_spray_occurrences (self):
        self.sprayoccurrences = []
    
    # reset everything to defaults
    def reset_to_defaults (self):
        self.nozzlecount = constants.default_nozzlecount
        self.chemicalclass = constants.CHEMICALCLASS2
        self.sprayduration_ms = constants.default_sprayduration_ms
        self.sprayoccurrences = constants.generate_default_sprayoccurrences()
        self.valve_first_open_offset_ms = constants.default_valve_first_open_offset_ms
        self.valve_activation_interval_ms = constants.default_valve_activation_interval_ms

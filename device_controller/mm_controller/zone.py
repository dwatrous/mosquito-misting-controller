# Copyright MosquitoMax 2022, all rights reserved

import datetime
from math import floor
import sched, time
import multiprocessing
import json

from mm_controller.environment import environment
from mm_controller import constants
from mm_controller import device_sensors
from mm_controller.utils import onpi, app_log
from mm_controller import cloud

class zone:
    ms_in_second = 1000
    valve_scheduler = sched.scheduler()
    zonecloud = cloud.Cloud()

    def __init__(self, zonedefinition=None, low_temp_threshold_f=50, rain_threshold_in=0.5) -> None:
        self.spraying = False
        self.env = environment()
        self.spraydata = {}
        self.sensordata = []

        self.low_temp_threshold_f = low_temp_threshold_f
        self.rain_threshold_in = rain_threshold_in

        if zonedefinition == None:
            self.name = "Default"
            self.reset_to_defaults()
            return

        # if a JSON was passed directly, change it to a dict
        if type(zonedefinition) is not dict:
            zonedefinition = json.loads(zonedefinition)
    
        # hydrate based on zonedefinition
        # TODO: in the case of new values, existing stored values may not be present causing KeyError
        self.name = zonedefinition["name"]
        self.nozzlecount = zonedefinition["nozzlecount"]
        self.chemicalclass = zonedefinition["chemicalclass"]
        self.sprayduration_ms = zonedefinition["sprayduration_ms"]
        self.sprayoccurrences = zonedefinition["sprayoccurrences"]
        self.valve_first_open_offset_ms = zonedefinition["valve_first_open_offset_ms"]
        self.valve_activation_interval_ms = zonedefinition["valve_activation_interval_ms"]
        self.sensor_capture_buffer_s = zonedefinition["sensor_capture_buffer_s"]
        self.sensor_capture_interval_s = zonedefinition["sensor_capture_interval_s"]
        self.beep_duration = zonedefinition["beep_duration"]


    def get_zonedefinition(self):
        zonedefinition = {
            "name": self.name,
            "nozzlecount": self.nozzlecount,
            "chemicalclass": self.chemicalclass,
            "sprayduration_ms": self.sprayduration_ms,
            "sprayoccurrences": self.sprayoccurrences,
            "valve_first_open_offset_ms": self.valve_first_open_offset_ms,
            "valve_activation_interval_ms": self.valve_activation_interval_ms,
            "sensor_capture_buffer_s": self.sensor_capture_buffer_s,
            "sensor_capture_interval_s": self.sensor_capture_interval_s,
            "beep_duration": self.beep_duration
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
        valve_openings.append({"open_at_ms": self.valve_first_open_offset_ms, "open_for_ms": valve_open_duration_ms})
        # add remaining times based on 
        number_valve_openings = floor(self.sprayduration_ms/self.valve_activation_interval_ms)
        for opening in range(1, number_valve_openings):
            valve_opening = {
                "open_at_ms": self.valve_activation_interval_ms * opening + self.valve_first_open_offset_ms,
                "open_for_ms": valve_open_duration_ms
            }
            valve_openings.append(valve_opening) 
        return valve_openings

    def open_valve(self, valve, close_after_ms=700, signal=None):
        # signal, if available
        if signal:
            signal.set()
        # record start time in ms
        open_time = int(time.time()*self.ms_in_second)
        try:
            # open valve
            if valve == constants.VALVE_WATER and onpi:
                device_sensors.gpioctrl_water_valve.on()
            elif valve == constants.VALVE_CHEMICAL and onpi:
                device_sensors.gpioctrl_chemical_valve.on()
            else:
                if onpi:
                    app_log.error("Invalid valve: %d" % valve)
                else:
                    app_log.info("Opened valve %d (not on pi)" % valve)
            
            # leave valve open for close_after_ms
            while int(time.time()*self.ms_in_second) < (open_time+close_after_ms):
                if device_sensors.float_switch_signal.is_set() and valve != constants.GPIO_CHEMICAL_VALVE and onpi:
                    device_sensors.gpioctrl_chemical_valve.off()
                time.sleep(0.001)

        except:
            device_sensors.gpioctrl_water_valve.off()
            device_sensors.gpioctrl_chemical_valve.off()
        finally:
            if valve == constants.VALVE_WATER and onpi:
                device_sensors.gpioctrl_water_valve.off()
            elif valve == constants.VALVE_CHEMICAL and onpi:
                device_sensors.gpioctrl_chemical_valve.off()
            else:
                if onpi:
                    app_log.error("Invalid valve: %d" % valve)
                else:
                    app_log.info("Closed valve %d (not on pi)" % valve)

        # record close time in ms
        close_time = int(time.time()*self.ms_in_second)
        valve_opening = {
            "valve": valve,
            "open_time": open_time,
            "close_time": close_time,
            "total_valve_time_ms": close_time-open_time
        }
        self.spraydata["valve_executions"].append(valve_opening)
        app_log.info(valve_opening)

    def run_motor(self, close_after_ms):
        motor_start_time = int(time.time()*self.ms_in_second)

        try:
            if onpi: device_sensors.gpioctrl_motor.on()
            while int(time.time()*self.ms_in_second) < (motor_start_time+close_after_ms):
                if device_sensors.float_switch_signal.is_set() and onpi:
                    device_sensors.gpioctrl_motor.off()
                else:
                    device_sensors.gpioctrl_motor.on()
                time.sleep(0.001)
        except:
            if onpi: device_sensors.gpioctrl_motor.off()
        finally:
            if onpi: device_sensors.gpioctrl_motor.off()

        motor_shutoff_time = int(time.time()*self.ms_in_second)
        self.spraydata["motor_timing"] = {
            "motor_start_time": motor_start_time,
            "motor_shutoff_time": motor_shutoff_time,
            "total_motor_run_time": motor_shutoff_time-motor_start_time
        }
        app_log.info(self.spraydata["motor_timing"])

    # capture data from all sensors
    def capture_sensor_data(self, signal, sensordata, spray_start_time):
        readings = {
            "start_time": spray_start_time,
            "capture_interval": self.sensor_capture_interval_s,
            "readings": []
        }
        while not signal.is_set():
            try:
                readings["readings"].append(
                    {
                        "pressure_line_in_psi": device_sensors.read_current_line_in_pressure_psi(),
                        "pressure_line_out_psi": device_sensors.read_current_line_out_pressure_psi(),
                        "vacuum_kpa": device_sensors.read_current_vacuum_pressure_kpa(),
                        "weight": device_sensors.read_current_weight()
                    }
                )
            except Exception as ioerr:
                # just pass and miss a reading
                app_log.error(ioerr)
            time.sleep(self.sensor_capture_interval_s)
        sensordata.put(readings)

    # execute spray
    def execute_spray(self, skip_override=False, spray_event="SCHEDULE"):
        if not self.spraying:
            # clear and begin capturing data
            spray_start_time = datetime.datetime.now().astimezone(datetime.timezone.utc)
            self.spraydata = {
                "start_time": spray_start_time,
                "spray_event": spray_event,
                "valve_executions": []
            }
            sensorreadings = multiprocessing.Queue()
            stop_reading_sensors = multiprocessing.Event()
            # decide whether to spray at all
            low_temp_last_24hr = self.env.get_low_temp_last_24hr()
            low_temp_next_24hr = self.env.get_low_temp_next_24hr()
            rain_prediction_next_24hr = self.env.get_rain_prediction_next_24hr()["inches"]
            self.spraydata["low_temp_last_24hr"] = low_temp_last_24hr
            self.spraydata["low_temp_next_24hr"] = low_temp_next_24hr
            self.spraydata["rain_prediction_next_24hr"] = rain_prediction_next_24hr
            if (low_temp_last_24hr < self.low_temp_threshold_f or low_temp_next_24hr < self.low_temp_threshold_f) and not skip_override:
                # handle temperature skip
                self.spraydata["skip"] = True
                self.spraydata["skip_reason"] = "temperature"
                app_log.info("SKIP: Temperature [low_last24: %s, low_next24 %s]" % (self.spraydata["low_temp_last_24hr"], self.spraydata["low_temp_next_24hr"]))
                self.zonecloud.send_message("SKIP_SPRAY")
                self.zonecloud.write_spray_occurence_ds(self.spraydata)
                return
            if rain_prediction_next_24hr > self.rain_threshold_in and not skip_override:
                # handle rain skip
                self.spraydata["skip"] = True
                self.spraydata["skip_reason"] = "rain"
                app_log.info("SKIP: Rain [inches_next24: %s]" % self.spraydata["rain_prediction_next_24hr"])
                self.zonecloud.send_message("SKIP_SPRAY")
                self.zonecloud.write_spray_occurence_ds(self.spraydata)
                return
            if False and not skip_override:   # TODO implement wind skip
                # handle wind skip
                pass
            else:
                self.spraydata["skip"] = False
                self.spraydata["skip_reason"] = "skip override" if skip_override else None

            # notify user and message spray execution
            self.zonecloud.send_message("EXECUTE_SPRAY")
            device_sensors.status_buzzer_beep(self.beep_duration)

            # indicate running
            device_sensors.status_led_running()
            # calculate valve openings
            valve_openings = self.calculate_valve_openings()
            self.spraydata["valve_openings"] = valve_openings
            water_valve_open = multiprocessing.Event()
            # start motor
            spray_start_time = int(time.time()*self.ms_in_second)
            capture_sensors = multiprocessing.Process(target=self.capture_sensor_data, args=(stop_reading_sensors, sensorreadings, spray_start_time))
            activate_motor = multiprocessing.Process(target=self.run_motor, kwargs={"close_after_ms": self.sprayduration_ms})
            activate_watervalve = multiprocessing.Process(target=self.open_valve, kwargs={"valve": constants.VALVE_WATER, "close_after_ms": self.sprayduration_ms + constants.WATER_REFILL_TIME_MS, "signal": water_valve_open})
            # schedule valve openings
            for valve_opening in valve_openings:
                # the multiple of self.ms_in_second are to convert between seconds and milliseconds
                self.valve_scheduler.enter(valve_opening["open_at_ms"]/self.ms_in_second, 1, self.open_valve, kwargs={"valve": constants.VALVE_CHEMICAL, "close_after_ms": valve_opening["open_for_ms"]})
            # start everything
            capture_sensors.start()
            time.sleep(self.sensor_capture_buffer_s)   # let the sensors capture some data before everything starts
            # start scheduled processes and threads
            activate_watervalve.start()
            activate_motor.start()
            water_valve_open.wait()     # wait for water valve process to start before running chem valves
            self.valve_scheduler.run()  # runs synchronously
            #wait for everything to complete
            activate_motor.join()
            activate_watervalve.join()
            spray_end_time = int(time.time()*self.ms_in_second)
            time.sleep(self.sensor_capture_buffer_s)   # let the sensors capture some data after everything finishes
            stop_reading_sensors.set()
            sensordata = sensorreadings.get()
            capture_sensors.join()
            self.spraydata["spray_timing"] = {
                "spray_start_time": spray_start_time,
                "spray_end_time": spray_end_time,
                "total_spray_time_ms": spray_end_time-spray_start_time
            }
            self.spraydata["sensor_data"] = sensordata
            # write spraydata to cloud
            self.zonecloud.write_spray_occurence_ds(self.spraydata)
            app_log.info(self.spraydata["spray_timing"])
            app_log.debug(self.spraydata["sensor_data"])
            # indicate ready
            device_sensors.status_led_ready()
            self.spraying = False
        else:
            app_log.info("Already spraying. Ignore spray request.")

    # Functions to add sprayoccurrences
    def add_spray_occurrence (self, daysofweek, timeofday):
        occurrence = {"daysofweek": daysofweek, "timeofday": timeofday}
        if occurrence not in self.sprayoccurrences:
            self.sprayoccurrences.append(occurrence)
    
    def add_sprayoccurrences_all_days (self, timeofday):
        self.add_spray_occurrence([0,1,2,3,4,5,6], timeofday)

    def add_sprayoccurrences_weekdays (self, timeofday):
        self.add_spray_occurrence([1,2,3,4,5], timeofday)
    
    # removing a sprayoccurrence will normally be done through the app
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
        self.sensor_capture_buffer_s = constants.default_sensor_capture_buffer_seconds
        self.sensor_capture_interval_s = constants.default_sensor_capture_interval_seconds
        self.beep_duration = constants.default_beep_duration


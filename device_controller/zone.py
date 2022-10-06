# Copyright MosquitoMax 2022, all rights reserved

import datetime
import constants
from math import floor
import sched, time

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

    def seconds_to_milliseconds(self, seconds):
        return round(seconds*1000)

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

    def open_valve(self, close_after_ms=700):
        open_time = self.seconds_to_milliseconds(time.time())
        print("open_valve", open_time)
        time.sleep(close_after_ms/1000)
        close_time = self.seconds_to_milliseconds(time.time())
        print("close_valve", close_time)
        print("time_open", close_time-open_time)

    # execute spray
    def execute_spray(self):
        # calculate valve openings
        valve_openings = self.calculate_valve_openings()
        # start compressor
        spray_start_time = time.time()
        print("start compressor", spray_start_time)
        # schedule valve openings
        for valve_opening in valve_openings:
            # the multiple of 1000 are to convert between seconds and milliseconds
            self.valve_scheduler.enter(valve_opening[0]/1000, 1, self.open_valve, kwargs={"close_after_ms": valve_opening[1]})
        self.valve_scheduler.run()
        spray_end_time = time.time()
        print("stop compressor", spray_end_time)
        print("spray_time", spray_end_time-spray_start_time)

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

myzone = zone()

print(myzone.calculate_valve_openings())

myzone.execute_spray()
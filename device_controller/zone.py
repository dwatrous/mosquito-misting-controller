# Copyright MosquitoMax 2022, all rights reserved

import datetime
import constants

class zone:
    name = "Default"
    nozzlecount = 30
    chemicalclass = constants.CHEMICALCLASS2
    sprayduration = 45
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
        self.sprayduration = constants.default_sprayduration
        self.sprayoccurrences = constants.generate_default_sprayoccurrences()

    def get_valve_timing(self):
        pass
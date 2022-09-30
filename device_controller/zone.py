# Copyright MosquitoMax 2022, all rights reserved

import datetime
import constants

class zone:
    name = "Default"
    nozzlecount = 30
    chemicalclass = constants.CHEMICALCLASS2
    sprayduration = 45
    sprayoccurrences = []   # [{"dayofweek": INT[0-6], "timeofday": datetime.time}, ...]

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

    def clear_spray_occurrences (self):
        self.sprayoccurrences = []
    
    def reset_to_defaults (self):
        self.nozzlecount = constants.default_nozzlecount
        self.chemicalclass = constants.CHEMICALCLASS2
        self.sprayduration = constants.default_sprayduration
        self.sprayoccurrences = constants.generate_default_sprayoccurrences()

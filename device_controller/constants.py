#!/usr/bin/env python
# Copyright MosquitoMax 2022, all rights reserved

import datetime

CHEMICALCLASS1 = 1  # unused
CHEMICALCLASS2 = 2  # RipTide, Sector and Eco MC (do not use emulsifier)
CHEMICALCLASS2 = 3  # NoTox and Eco Exempt IC2
CHEMICALCLASS2 = 4  # Pyronyl 303 or Vampyre

def get_chemical_class_description(classnumber):
    if classnumber == CHEMICALCLASS1:
        return "Unused"
    elif classnumber == CHEMICALCLASS2:
        return "RipTide, Sector and Eco MC (do not use emulsifier)"
    elif classnumber == CHEMICALCLASS2:
        return "NoTox and Eco Exempt IC2"
    elif classnumber == CHEMICALCLASS2:
        return "Pyronyl 303 or Vampyre"
    else:
        return "Invalid Class Number!"

dayofweekmap = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}

# defaults

default_nozzlecount = 30
default_sprayduration = 45
def generate_default_sprayoccurrences ():
    default_sprayoccurrences = []
    for dayofweek in range(7):
        for hourofday in [0, 6, 18, 20]:
            default_sprayoccurrences.append({"dayofweek": dayofweek, "timeofday": datetime.time(hourofday)})
    return default_sprayoccurrences

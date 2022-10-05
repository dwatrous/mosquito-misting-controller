#!/usr/bin/env python
# Copyright MosquitoMax 2022, all rights reserved

import datetime

CHEMICALCLASS1 = 1  # unused
CHEMICALCLASS2 = 2  # RipTide, Sector and Eco MC (do not use emulsifier)
CHEMICALCLASS3 = 3  # NoTox and Eco Exempt IC2
CHEMICALCLASS4 = 4  # Pyronyl 303 or Vampyre

configfilename = "device_config.json"

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
            default_sprayoccurrences.append({"dayofweek": dayofweek, "timeofday": {"type": "fixedtime", "value": datetime.time(hourofday)}})
    return default_sprayoccurrences

valve_initial_opening_offset_ms = 500
valve_open_interval = 5000

valve_timing = {}
valve_timing[CHEMICALCLASS4] = {5: 250,
10: 500,
15: 750,
20: 1000,
25: 1250,
30: 1500,
35: 1700,
40: 2000,
45: 2250,
50: 2500,
55: 2750,
60: 3000,
65: 3250,
70: 3500,
75: 3750,
80: 4000,
85: 4250,
90: 4500,
95: 4800,
100: 5000,
105: 5000,
110: 5000,
115: 5000,
120: 5000}

valve_timing[CHEMICALCLASS3] = {5: 150,
10: 350,
15: 550,
20: 750,
25: 950,
30: 1150,
35: 1300,
40: 1500,
45: 1700,
50: 1900,
55: 2100,
60: 2300,
65: 2500,
70: 2650,
75: 2850,
80: 3050,
85: 3250,
90: 3450,
95: 3650,
100: 3850,
105: 4000,
110: 4250,
115: 4400,
120: 4600}

valve_timing[CHEMICALCLASS2] = {5: 100,
10: 200,
15: 300,
20: 450,
25: 550,
30: 700,
35: 800,
40: 900,
45: 1050,
50: 1150,
55: 1300,
60: 1400,
65: 1500,
70: 1650,
75: 1750,
80: 1900,
85: 2000,
90: 2100,
95: 2250,
100: 2350,
105: 2500,
110: 2600,
115: 2750,
120: 2850}

valve_timing[CHEMICALCLASS1] = {5: 100,
10: 150,
15: 300,
20: 350,
25: 450,
30: 550,
35: 650,
40: 800,
45: 900,
50: 1000,
55: 1100,
60: 1200,
65: 1300,
70: 1400,
75: 1500,
80: 1600,
85: 1700,
90: 1800,
95: 1950,
100: 2000,
105: 2150,
110: 2250,
115: 2300,
120: 2400}
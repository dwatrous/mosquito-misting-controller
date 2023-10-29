#!/usr/bin/env python
# Copyright MosquitoMax 2022, all rights reserved

# API Credentials TODO: Move these into a more secure place later
visualcrossing_apiKey = "KGU7KGVS8UBX2UTEWNZ8U3RRM"

# visualcrossing weather integration values
visualcrossing_api = {
    "scheme": "https",
    "host": "weather.visualcrossing.com",
    "path": "/VisualCrossingWebServices/rest/services/timeline/$location/$startdate/$enddate",
    "unitGroup": "us",
    "contentType": "json",
    "data_elements": "datetime,datetimeEpoch,tempmax,tempmin,temp,precip,precipprob,precipcover,preciptype,windgust,windspeed,winddir,sunrise,sunset,conditions,description,icon",
    "data_granularity": "hours"
}
visualcrossing_refresh_threshold = 60 * 60 * 6  # 6 hours in seconds

# device constants
email_representation_domain = "mosquitomax.com"

# use zipcode and state for MosquitoMax office
default_zip = "77449"
default_state = "TX"
default_environment_city = "Houston"    # must be in https://astral.readthedocs.io/en/latest/index.html#cities
default_timezone = "US/Central"     # https://schedule.readthedocs.io/en/latest/timezones.html

controller_wait_time = 120

# winter/summer options

# zone constants
CHEMICALCLASS1 = 1  # unused
CHEMICALCLASS2 = 2  # RipTide, Sector and Eco MC (do not use emulsifier)
CHEMICALCLASS3 = 3  # NoTox and Eco Exempt IC2
CHEMICALCLASS4 = 4  # Pyronyl 303 or Vampyre

VALVE_WATER = 1
VALVE_CHEMICAL = 2
VALVE_ZONE_0 = 10
VALVE_ZONE_1 = 11
VALVE_ZONE_2 = 12
VALVE_ZONE_3 = 13
VALVE_ZONE_4 = 14

WATER_REFILL_TIME_MS = 45000

# GPIO pin assignments see https://app.diagrams.net/#G1WQeF1I6ggE7zajPLvekrFTin8tPEHoUg
GPIO_MOTOR = 17
GPIO_WATER_VALVE = 27
GPIO_CHEMICAL_VALVE = 22
GPIO_RELAY_X = 23   # unused 4th relay
GPIO_RELAY_ACTIVE_HIGH = False
GPIO_WEIGHT_DATA = 5
GPIO_WEIGHT_SCK = 6
GPIO_LED_RED = 16
GPIO_LED_GREEN = 20
GPIO_LED_BLUE = 21
GPIO_FLOAT_SWITCH = 13
GPIO_RESET_BUTTON = 7
GPIO_BUZZER = 24
ADC_CHANNEL_LINE_IN_PRESSURE = 1
ADC_CHANNEL_LINE_OUT_PRESSURE = 2
ADC_CHANNEL_VACUUM = 0
SCALE_RAW_TO_OZ_REFERENCE = 13162

# # Messaging events
#     # "action": [
#     #     "notify_user",
#     #     "notify_device",
#     #     "notify_admin",
#     #     "spray",
#     #     "skip_next",
#     #     "skip_24hr"
#     # ]
#     # "origin": "DEVICE|USER|ADMIN",

# EVENT_SPRAY_NOW = {
#     "origin": "USER",
#     "text_description": "EVENT_SPRAY_NOW",
#     "action": [
#         "notify_device",
#         "spray"
#     ]
# }
# EVENT_SPRAY_SKIP_NEXT = {
#     "origin": "USER",
#     "text_description": "EVENT_SPRAY_SKIP_NEXT",
#     "action": [
#         "notify_device",
#         "skip_next"
#     ]
# }
# EVENT_SPRAY_PENDING = {
#     "origin": "DEVICE",
#     "text_description": "EVENT_SPRAY_PENDING",
#     "action": [
#         "notify_user"
#     ]
# }
# EVENT_SPRAY_COMPLETED = {
#     "origin": "DEVICE",
#     "text_description": "EVENT_SPRAY_COMPLETED",
#     "action": [
#         "notify_user"
#     ]
# }
# EVENT_SKIP_24HR = {
#     "origin": "USER",
#     "text_description": "EVENT_SKIP_24HR",
#     "action": [
#         "notify_device",
#         "skip_24hr"
#     ]
# }
# EVENT_DEVICE_REGISTER = {
#     "origin": "DEVICE",
#     "text_description": "EVENT_DEVICE_REGISTER",
#     "action": [
#         "notify_user",
#         "notify_admin"
#     ]
# }
# EVENT_DEVICE_BOOT = {
#     "origin": "DEVICE",
#     "text_description": "EVENT_DEVICE_BOOT",
#     "action": [
#         "notify_user"
#     ]
# }
# EVENT_DEVICE_LOW_PRESSURE_IN = {
#     "origin": "DEVICE",
#     "text_description": "EVENT_DEVICE_LOW_PRESSURE_IN",
#     "action": [
#         "notify_user",
#         "notify_admin"
#     ]
# }
# EVENT_DEVICE_LOW_PRESSURE_OUT = {
#     "origin": "DEVICE",
#     "text_description": "EVENT_DEVICE_LOW_PRESSURE_OUT",
#     "action": [
#         "notify_user",
#         "notify_admin"
#     ]
# }
# EVENT_DEVICE_LOW_VACUUM = {
#     "origin": "DEVICE",
#     "text_description": "EVENT_DEVICE_LOW_VACUUM",
#     "action": [
#         "notify_user",
#         "notify_admin"
#     ]
# }
# EVENT_DEVICE_WEIGHT_INSUFFICIENT_CHANGE = {
#     "origin": "DEVICE",
#     "text_description": "EVENT_DEVICE_WEIGHT_INSUFFICIENT_CHANGE",
#     "action": [
#         "notify_user",
#         "notify_admin"
#     ]
# }
# EVENT_DEVICE_WEIGHT_EXTREME_CHANGE = {
#     "origin": "DEVICE",
#     "text_description": "EVENT_DEVICE_WEIGHT_EXTREME_CHANGE",
#     "action": [
#         "notify_user",
#         "notify_admin"
#     ]
# }
# EVENT_DEVICE_RESET_INITIATED = {
#     "origin": "DEVICE",
#     "text_description": "EVENT_DEVICE_RESET_INITIATED",
#     "action": [
#         "notify_user",
#         "notify_admin"
#     ]
# }
# EVENT_DEVICE_ERROR_STATE = {
#     "origin": "DEVICE",
#     "text_description": "EVENT_DEVICE_ERROR_STATE",
#     "action": [
#         "notify_user",
#         "notify_admin"
#     ]
# }

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

default_low_temp_threshold_f = 50   # degrees F
default_rain_threshold_in = 0.5     # inches
default_nozzlecount = 30
default_sprayduration_ms = 45000
# sprayoccurrence
# [
#   {
#       "dayofweek": INT[0-6], 
#       "timeofday": 
#           {
#               "type": "fixedtime|relativetime",
#               "value": 
#                   [0-23, 0-59] (military time [hours, minutes])
# OR
#                   {"sunevent": "sunrise|sunset", "sunposition": "before|after", "deltaminutes": XX in minutes}
#           }
#   },
# ...]
def generate_default_sprayoccurrences ():
    default_sprayoccurrences = []
    for dayofweek in range(7):
        default_sprayoccurrences.append({"dayofweek": dayofweek, "timeofday": {"type": "fixedtime", "value": {"hour": 23, "minutes": 0}}})
        default_sprayoccurrences.append({"dayofweek": dayofweek, "timeofday": {"type": "relativetime", "value": {"sunevent": "sunrise", "sunposition": "before", "deltaminutes": 5}}})
        default_sprayoccurrences.append({"dayofweek": dayofweek, "timeofday": {"type": "relativetime", "value": {"sunevent": "dusk", "sunposition": "before", "deltaminutes": 5}}})
    return default_sprayoccurrences

default_valve_first_open_offset_ms = 500
default_valve_activation_interval_ms = 5000
default_sensor_capture_buffer_seconds = 2
default_sensor_capture_interval_seconds = 0.25

VALVE_OPEN_DURATION = {}
VALVE_OPEN_DURATION[CHEMICALCLASS4] = {5: 250,
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

VALVE_OPEN_DURATION[CHEMICALCLASS3] = {5: 150,
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

VALVE_OPEN_DURATION[CHEMICALCLASS2] = {5: 100,
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

VALVE_OPEN_DURATION[CHEMICALCLASS1] = {5: 100,
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
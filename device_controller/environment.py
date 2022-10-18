# https://astral.readthedocs.io/en/latest/index.html

import datetime
from astral import LocationInfo
from astral.sun import sun
from astral.geocoder import database, lookup
from noaa_sdk import NOAA
import json

def get_sundata(city):
    # must be in https://astral.readthedocs.io/en/latest/index.html#cities
    location = lookup(city, database())
    s = sun(location.observer, date=datetime.date.today(), tzinfo=location.timezone)
    sundata = {
        "dawn": s["dawn"],
        "sunrise": s["sunrise"],
        "noon": s["noon"],
        "sunset": s["sunset"],
        "dusk": s["dusk"]
    }
    return sundata
    
def get_hourly_weather_forcast_24hr(zip):
    n = NOAA()
    forecast = n.get_forecasts(zip, 'US', hourly=True)
    return forecast[0:24]

def get_hourly_weather_observations_24hr(zip):
    n = NOAA()
    observations = n.get_observations(zip, 'US')
    return observations

if __name__ == '__main__':
    testcity = "Houston"
    print(get_sundata(testcity))
    print(get_hourly_weather_forcast_24hr('77070'))
    for observation in get_hourly_weather_observations_24hr('77070'):
        print(json.dumps(observation, indent=2))
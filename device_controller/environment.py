# https://astral.readthedocs.io/en/latest/index.html

import datetime
from astral import LocationInfo
from astral.sun import sun
from astral.geocoder import database, lookup
from noaa_sdk import NOAA
import json
import constants

class environment:

    def __init__(self, zip=None, city=None) -> None:
        if zip == None:
            self.zip = constants.default_zip
        if city == None:
            self.city = constants.default_environment_city

        self.noaaapi = NOAA()

        # generate and fetch
        self.weather_forecast_24hr = self.get_hourly_weather_forcast_24hr()
        self.weather_observations_24hr = self.get_hourly_weather_observations_24hr()
        self.sundata = self.get_sundata()

    def get_forecast_24hr(self):
        return self.weather_forecast_24hr

    def get_observations_24hr(self):
        return self.weather_observations_24hr
    
    def get_sundata(self):
        return self.sundata

    # generate and fetch data
    def get_sundata(self):
        # must be in https://astral.readthedocs.io/en/latest/index.html#cities
        location = lookup(self.city, database())
        s = sun(location.observer, date=datetime.date.today(), tzinfo=location.timezone)
        sundata = {
            "dawn": s["dawn"],
            "sunrise": s["sunrise"],
            "noon": s["noon"],
            "sunset": s["sunset"],
            "dusk": s["dusk"]
        }
        return sundata
        
    def get_hourly_weather_forcast_24hr(self):
        forecast = self.noaaapi.get_forecasts(self.zip, 'US', hourly=True)
        return forecast[0:24]

    def get_hourly_weather_observations_24hr(self):
        observations = self.noaaapi.get_observations(self.zip, 'US')
        return observations
    
    # calculations
    def get_rain_next_24hr(self):
        pass

if __name__ == '__main__':
    env = environment()
    print(env.get_sundata())
    print(env.get_forecast_24hr())
    for observation in env.get_observations_24hr():
        print(json.dumps(observation, indent=2))
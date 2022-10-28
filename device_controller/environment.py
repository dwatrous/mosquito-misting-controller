# https://astral.readthedocs.io/en/latest/index.html

import datetime
from astral import LocationInfo
from astral.sun import sun
from astral.geocoder import database, lookup
from noaa_sdk import NOAA
import json
import constants
import itertools

# https://graphical.weather.gov/xml/xml_fields_icon_weather_conditions.php

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

    # utility functions
    def meters_to_inches(self, value_m):
        return value_m * 39.37

    def centigrade_to_fahrenheit(self, temp_c):
        return (temp_c * 9/5) + 32

    # getters
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
        return [observation for observation in itertools.islice(observations, 24)]
    
    # calculations
    def get_rain_next_24hr_percentage(self):
        rain_percentage = 0
        rain_indicator_keywords = ["showers", "thunderstorms", "rain"]
        rain_reducer_keywords = ["chance", "likely", "slight"]
        reducer_skip = False
        rain_references = 0
        for item in self.get_forecast_24hr():
            if any(indicator in item["shortForecast"].lower() for indicator in rain_indicator_keywords):
                rain_percentage = 100
                if not reducer_skip and any(reducer in item["shortForecast"].lower() for reducer in rain_reducer_keywords):
                    rain_references = rain_references + 0.5
                else:
                    reducer_skip = True
        if reducer_skip:
            return rain_percentage
        else:
            return rain_references/len(self.get_forecast_24hr())

    def get_rain_last_24hr_inches(self):
        rain_inches = 0
        for observation in self.get_observations_24hr():
            if observation["precipitationLastHour"]["value"] is not None:
                rain_inches = rain_inches + self.meters_to_inches(observation["precipitationLastHour"]["value"])
        return rain_inches

    def get_low_high_temp_last_24hr_f(self):
        temps = []
        for observation in self.get_observations_24hr():
            if observation["temperature"]["unitCode"] == "wmoUnit:degC":
                temps.append(self.centigrade_to_fahrenheit(observation["temperature"]["value"]))
            else:
                temps.append(observation["temperature"]["value"])
        return (min(temps), max(temps))

    def get_low_high_temp_next_24hr_f(self):
        temps = []
        for item in self.get_forecast_24hr():
            if item["temperatureUnit"] == "F":
                temps.append(item["temperature"])
            else:
                temps.append(self.centigrade_to_fahrenheit(item["temperature"]))
        return (min(temps), max(temps))




if __name__ == '__main__':
    env = environment()
    print(env.get_sundata())
    print(env.get_rain_last_24hr_inches())
    print(env.get_rain_next_24hr_percentage())
    print(env.get_low_high_temp_last_24hr_f())
    print(env.get_low_high_temp_next_24hr_f())
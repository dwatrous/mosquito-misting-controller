# https://astral.readthedocs.io/en/latest/index.html

import datetime
import time
from astral import LocationInfo
from astral.sun import sun
from astral.geocoder import database, lookup
import json
import constants
from visualcrossing import visualcrossing

class environment:

    def __init__(self, zip=None, city=None) -> None:
        if zip == None:
            self.zip = constants.default_zip
        if city == None:
            self.city = constants.default_environment_city
        self.viscross = visualcrossing(location=zip)
        self.weather_data = None
        self.weather_data_refreshed = datetime.datetime.now()
        self.refresh_threshold_seconds = 60 * 60 * 6

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
        
    def refresh_weather_data(self):
        time_delta = datetime.datetime.now() - self.weather_data_refreshed
        if self.weather_data is None or time_delta.total_seconds() > self.refresh_threshold_seconds:
            self.weather_data = self.viscross.fetch_weather_data()

    def get_low_temp_next_24hr(self):
        # refresh
        self.refresh_weather_data()
        # get current time
        today = time.strftime("%Y-%m-%d")
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        currenthour = time.strftime("%H:00:00")
        hours = 0
        low_temp = None
        firsttemp = False
        # loop through forecast and find low temp
        for day in self.weather_data["days"]:
            if day["datetime"] in [today, tomorrow]:
                for hour in day["hours"]:
                    if not firsttemp:
                        if hour["datetime"] == currenthour:
                            firsttemp = True
                            low_temp = hour["temp"]
                            hours = hours + 1
                    if firsttemp and hours < 24:
                        if hour["temp"] < low_temp: low_temp = hour["temp"]
                        hours = hours + 1
        return low_temp

    def get_low_temp_last_24hr(self):
        pass

    def get_max_wind_next_24hr(self):
        pass

    def get_rain_prob_next_24hr(self):
        pass


if __name__ == '__main__':
    env = environment()
    print(env.get_sundata())
    print(env.get_low_temp_next_24hr())

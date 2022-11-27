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

    # generate and fetch data
    def get_sundata(self):
        
        # city must be in https://astral.readthedocs.io/en/latest/index.html#cities
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

    def get_low_temp_last_24hr(self):
        return self.viscross.get_high_low_temp_next_24hr()["low_temp"]    

    def get_low_temp_next_24hr(self):
        return self.viscross.get_high_low_temp_last_24hr()["low_temp"]    

    def get_rain_prediction_next_24hr(self):
        prediction = {"probability": self.viscross.get_rain_probability_next_24hr(), "inches": self.viscross.get_rain_inches_next_24hr()}
        return prediction
    
    def get_rain_actual_last_24hr(self):
        return self.viscross.get_rain_actual_last_24hr()

if __name__ == '__main__':
    env = environment()
    print(env.get_sundata())
    print(env.get_low_temp_next_24hr())
    print(env.get_low_temp_last_24hr())
    print(env.get_rain_actual_last_24hr())
    print(env.get_rain_prediction_next_24hr())
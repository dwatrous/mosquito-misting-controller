# https://astral.readthedocs.io/en/latest/index.html

import datetime
from astral import LocationInfo
from astral.sun import sun
from astral.geocoder import database, lookup

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
    
if __name__ == '__main__':
    testcity = "Houston"
    print(get_sundata(testcity))
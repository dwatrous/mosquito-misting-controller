#Downloading weather data using Python as a CSV using the Visual Crossing Weather API
#See https://www.visualcrossing.com/resources/blog/how-to-load-historical-weather-data-using-python-without-scraping/ for more information.

import time
import codecs
import requests
from urllib.parse import urlunsplit, urlencode
import sys

# Collect
scheme = "https"
host = "weather.visualcrossing.com"

apikey="KGU7KGVS8UBX2UTEWNZ8U3RRM"
#UnitGroup sets the units of the output - us or metric
unitgroup="us"
contentType="json"

data_elements="datetime,datetimeEpoch,tempmax,tempmin,temp,precip,precipprob,precipcover,preciptype,windgust,windspeed,winddir,sunrise,sunset,conditions,description,icon"
data_granularity="hours,days,current"

#Location for the weather data
location="77070"

def build_api_url(location, startdate, enddate):
    path = f"/VisualCrossingWebServices/rest/services/timeline/{location}/{startdate}/{enddate}"
    query = urlencode({"unitGroup": unitgroup, "include": data_granularity, "elements": data_elements, "key": apikey, "contentType": contentType})
    return urlunsplit((scheme, host, path, query, ""))

starttime = int(time.time()-86400)
endtime = int(time.time()+86400)

request_url = build_api_url("77070",starttime ,endtime)

response = requests.get(request_url)

print(response.json())

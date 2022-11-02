#Downloading weather data using Python as a CSV using the Visual Crossing Weather API
#See https://www.visualcrossing.com/resources/blog/how-to-load-historical-weather-data-using-python-without-scraping/ for more information.

import time
import constants
import requests
from urllib.parse import urlunsplit, urlencode
from string import Template

class virtualcrossing:

    def __init__(self, location=None) -> None:
        if location == None:
            self.location = constants.default_zip

    def generate_request_url(self, location, startdate, enddate):
        path_template = Template(constants.virtualcrossing_api["path"])
        path = path_template.substitute(location=location, startdate=startdate, enddate=enddate)
        query = urlencode({
            "unitGroup": constants.virtualcrossing_api["unitGroup"], 
            "include": constants.virtualcrossing_api["data_granularity"], 
            "elements": constants.virtualcrossing_api["data_elements"], 
            "key": constants.virtualcrossing_apiKey, 
            "contentType": constants.virtualcrossing_api["contentType"]})
        return urlunsplit((constants.virtualcrossing_api["scheme"], constants.virtualcrossing_api["host"], path, query, ""))

    def fetch_weather_data(self):
        starttime = int(time.time()-86400)
        endtime = int(time.time()+86400)

        request_url = self.generate_request_url(self.location, starttime, endtime)
        weather_response = requests.get(request_url)
        return weather_response.json()

if __name__ == '__main__':
    vc = virtualcrossing()
    weather_data = vc.fetch_weather_data()
    print(weather_data)

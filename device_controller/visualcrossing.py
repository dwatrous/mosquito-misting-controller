import time
import constants
import requests
from urllib.parse import urlunsplit, urlencode
from string import Template

class visualcrossing:

    def __init__(self, location=None, api_specs=None) -> None:
        if location == None:
            self.location = constants.default_zip
        if api_specs == None:
            self.api_specs = constants.visualcrossing_api

    def generate_request_url(self, location, startdate, enddate):
        path_template = Template(self.api_specs["path"])
        path = path_template.substitute(location=location, startdate=startdate, enddate=enddate)
        query = urlencode({
            "unitGroup": self.api_specs["unitGroup"], 
            "include": self.api_specs["data_granularity"], 
            "elements": self.api_specs["data_elements"], 
            "key": constants.visualcrossing_apiKey, 
            "contentType": self.api_specs["contentType"]})
        return urlunsplit((self.api_specs["scheme"], self.api_specs["host"], path, query, ""))

    def fetch_weather_data(self):
        # 86400 seconds in a day, so this is 24 hours back and forward from now in Unix epoch
        starttime = int(time.time()-86400)
        endtime = int(time.time()+86400)

        request_url = self.generate_request_url(self.location, starttime, endtime)
        weather_response = requests.get(request_url)
        return weather_response.json()

if __name__ == '__main__':
    vc = visualcrossing()
    weather_data = vc.fetch_weather_data()
    print(weather_data)

import time
import datetime
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
        self.weather_data = None
        self.weather_data_hourly = []
        self.weather_data_refreshed = datetime.datetime.min
        self.refresh_threshold_seconds = constants.visualcrossing_refresh_threshold
        self.high_low_temps_next_24hr = None
        self.high_low_temps_last_24hr = None
        self.rain_probability_next_24hr = None
        self.rain_actual_last_24hr = None

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
        self.weather_data = weather_response.json()
        self.weather_data_refreshed = datetime.datetime.now()

        # flatten to hourly
        self.weather_data_hourly.clear()
        for day in self.weather_data["days"]:
            for hour in day["hours"]:
                hour["date"] = day["datetime"]
                self.weather_data_hourly.append(hour)

        # find high/low temps
        self.find_data_next_24hr()
        self.find_data_last_24hr()

    def find_data_next_24hr(self):
        # get current time
        today = time.strftime("%Y-%m-%d")
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        currenthour = time.strftime("%H:00:00")
        hours = 0
        temps = []
        rain_prob = []
        firsttemp = False
        # loop through forecast and find low temp
        for hour in self.weather_data_hourly:
            if hour["date"] in [today, tomorrow]:
                if not firsttemp:
                    if hour["datetime"] == currenthour:
                        firsttemp = True
                        temps.append(hour["temp"])
                        rain_prob.append(hour["precipprob"])
                        hours = hours + 1
                if firsttemp and hours < 24:
                    temps.append(hour["temp"])
                    rain_prob.append(hour["precipprob"])
                    hours = hours + 1
        self.high_low_temps_next_24hr = {"high_temp": max(temps), "low_temp": min(temps)}
        self.rain_probability_next_24hr = max(rain_prob)

    def find_data_last_24hr(self):
        # get current time
        today = time.strftime("%Y-%m-%d")
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        currenthour = time.strftime("%H:00:00")
        hours = 0
        temps = []
        rain_actual = []
        firsttemp = False
        # loop through forecast and find low temp
        for hour in self.weather_data_hourly:
            if hour["date"] in [today, yesterday]:
                if not firsttemp:
                    if hour["datetime"] == currenthour:
                        firsttemp = True
                        temps.append(hour["temp"])
                        rain_actual.append(hour["precip"])
                        hours = hours + 1
                if firsttemp and hours < 24:
                    temps.append(hour["temp"])
                    rain_actual.append(hour["precip"])
                    hours = hours + 1
        self.high_low_temps_last_24hr = {"high_temp": max(temps), "low_temp": min(temps)}
        self.rain_actual_last_24hr = sum(rain_actual)

    def refresh_weather_data(self):
        time_delta = datetime.datetime.now() - self.weather_data_refreshed
        if self.weather_data is None or time_delta.total_seconds() > self.refresh_threshold_seconds:
            self.fetch_weather_data()

    def get_weather_data_hourly(self):
        self.refresh_weather_data()
        return self.weather_data_hourly
    
    def get_weather_data(self):
        self.refresh_weather_data()
        return self.weather_data

    def get_high_low_temp_next_24hr(self):
        self.refresh_weather_data()
        return self.high_low_temps_next_24hr

    def get_high_low_temp_last_24hr(self):
        self.refresh_weather_data()
        return self.high_low_temps_last_24hr
    
    def get_rain_probability_next_24hr(self):
        self.refresh_weather_data()
        return self.rain_probability_next_24hr

    def get_rain_actual_last_24hr(self):
        self.refresh_weather_data()
        return self.rain_actual_last_24hr


if __name__ == '__main__':
    vc = visualcrossing()
    weather_data = vc.get_weather_data()
    weather_data_hourly = vc.get_weather_data_hourly()
    print(weather_data)
    print(weather_data_hourly)
    print(vc.get_high_low_temp_next_24hr())
    print(vc.get_high_low_temp_last_24hr())
    print(vc.get_rain_probability_next_24hr())
    print(vc.get_rain_actual_last_24hr())

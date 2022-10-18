# Copyright MosquitoMax 2022, all rights reserved

import sched
import zone
import constants
import json
import time
import datetime

class device:
    zone_scheduler = sched.scheduler()

    def __init__(self, devicedefinition=None) -> None:
        self.zones = []
        if devicedefinition == None:
            self.street1 = None
            self.street2 = None
            self.city = None
            self.state = constants.default_state
            self.zip = constants.default_zip
            self.environment_city = constants.default_environment_city
            self.zones.append(zone.zone())
            return

        # if a JSON was passed directly, change it to a dict
        if type(devicedefinition) is not dict:
            devicedefinition = json.loads(devicedefinition)
    
        # hydrate based on devicedefinition
        self.street1 = devicedefinition["street1"]
        self.street2 = devicedefinition["street2"]
        self.city = devicedefinition["city"]
        self.state = devicedefinition["state"]
        self.zip = devicedefinition["zip"]
        self.zones = devicedefinition["zones"]

    def get_devicedefinition(self):
        devicedefinition = {
            "street1": self.street1,
            "street2": self.street2,
            "city": self.city,
            "state": self.state,
            "zip": self.zip,
            "zones": self.zones
        }
    
    def get_devicedefinition_json(self):
        return json.dumps(self.get_devicedefinition())

    # zones
    def get_all_sprayoccurrences():
        pass

    def open_zone_valve(self, valve, close_after_ms=700):
        # record start time in ms
        open_time = time.time()*self.ms_in_second
        # open valve
        print("zone valve open [%d]" % valve)
        
        # leave valve open for close_after_ms
        time.sleep(close_after_ms/self.ms_in_second)

        print("zone valve close [%d]" % valve)

        # record close time in ms
        close_time = time.time()*self.ms_in_second
        print("valve %d opened at %d and closed at %d for a total of %.1f" % (valve, open_time, close_time, close_time-open_time))

    # schedule sprays
    def schedule_spray_all_zones_24hrs(self):
        now = datetime.datetime.now()
        currenthour = now.hour
        currentday = now.weekday()
        (sunrise, sunset) = self.
        for spray_zone in self.zones:
            for sprayoccurence in spray_zone.sprayoccurrences:
                if sprayoccurence["dayofweek"] = currentday and sprayoccurence[""]



    # app/online connection

    # integrations
    def get_rain_actual(self):
        pass

    def get_temp_forecast(self):
        pass

    def schedule_24_hours(self):
        pass

    # on board sensors
    def read_current_line_pressure(self):
        pass

    def read_current_temp(self):
        pass

    def read_current_vacuum_pressure(self):
        pass


# Copyright MosquitoMax 2022, all rights reserved

import zone
import constants
import json

class device:
    zones = []

    def __init__(self, devicedefinition=None) -> None:
        self.zones = []
        if devicedefinition == None:
            self.street1 = None
            self.street2 = None
            self.city = None
            self.state = constants.default_state
            self.zip = constants.default_zip
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

    # spray

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


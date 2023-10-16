# Copyright MosquitoMax 2022, all rights reserved

import logging
import threading
import schedule
import zone
import device_sensors
import constants
import json
import time
import datetime
from utils import app_log
from environment import environment
from pytz import timezone
import cloud

class device:

    def __init__(self, devicedefinition=None) -> None:
        self.zones = []
        self.env = environment()
        self.schedule_thread_kill_signal = threading.Event()
        self.device_cloud = cloud.Cloud()

        if devicedefinition == None:
            self.name = "My Device"
            self.street1 = None
            self.street2 = None
            self.city = None
            self.state = constants.default_state
            self.zip = constants.default_zip
            self.environment_city = constants.default_environment_city
            self.low_temp_threshold_f = constants.default_low_temp_threshold_f
            self.rain_threshold_in = constants.default_rain_threshold_in
            self.timezone = constants.default_timezone
            self.zones.append(zone.zone())
        else:
            # if a JSON was passed directly, change it to a dict
            if type(devicedefinition) is not dict:
                devicedefinition = json.loads(devicedefinition)
        
            # hydrate based on devicedefinition
            self.name = devicedefinition["name"]
            self.street1 = devicedefinition["street1"]
            self.street2 = devicedefinition["street2"]
            self.city = devicedefinition["city"]
            self.state = devicedefinition["state"]
            self.zip = devicedefinition["zip"]
            self.environment_city = devicedefinition["environment_city"]
            self.low_temp_threshold_f = devicedefinition["low_temp_threshold_f"]
            self.rain_threshold_in = devicedefinition["rain_threshold_in"]
            self.timezone = devicedefinition["timezone"]
            self.zones = [zone.zone(devicezone) for devicezone in devicedefinition["zones"]]

        # schedule sprays and start schedule thread
        self.check_system()
        # TODO if system isn't ready, signal error and don't schedule sprays
        self.schedule_sprays()
        self.start_schedule_thread()

    def get_devicedefinition(self):
        devicedefinition = {
            "name": self.name,
            "street1": self.street1,
            "street2": self.street2,
            "city": self.city,
            "state": self.state,
            "zip": self.zip,
            "environment_city": self.environment_city,
            "low_temp_threshold_f": self.low_temp_threshold_f,
            "rain_threshold_in": self.rain_threshold_in,
            "timezone": self.timezone,
            "zones": [devicezone.get_zonedefinition() for devicezone in self.zones]
        }
        return devicedefinition
    
    def message_handler(self, message):
        if message["data"] == None:
            app_log.info("Empty message: %s", message)
        else:
            for key in message["data"]: 
                app_log.info("Received message: %s", message)
                # do something with the message
                self.device_cloud.mark_message_read({key: message["data"][key]})

    def check_system(self):
        # TODO add expected thresholds for ready and update conditional
        if (device_sensors.read_current_line_in_pressure_psi() and device_sensors.read_current_weight()):
            device_sensors.status_led_ready()

    def get_devicedefinition_json(self):
        return json.dumps(self.get_devicedefinition())

    # currently unused
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
    # https://schedule.readthedocs.io/en/stable/background-execution.html
    def start_schedule_thread(self, interval=60):

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not self.schedule_thread_kill_signal.is_set():
                    schedule.run_pending()
                    time.sleep(interval)

        continuous_thread = ScheduleThread()
        continuous_thread.start()

    def schedule_dayofweek(self, daynumber, spraytime, dofunc, tag):
        logging.info({"schedule_dayofweek": {"daynumber": daynumber, "spraytime": spraytime, "dofunc": dofunc, "tag": tag}})
        if daynumber == 0:
            schedule.every().sunday.at(spraytime, self.timezone).do(dofunc).tag(tag)
        if daynumber == 1:
            schedule.every().monday.at(spraytime, self.timezone).do(dofunc).tag(tag)
        if daynumber == 2:
            schedule.every().tuesday.at(spraytime, self.timezone).do(dofunc).tag(tag)
        if daynumber == 3:
            schedule.every().wednesday.at(spraytime, self.timezone).do(dofunc).tag(tag)
        if daynumber == 4:
            schedule.every().thursday.at(spraytime, self.timezone).do(dofunc).tag(tag)
        if daynumber == 5:
            schedule.every().friday.at(spraytime, self.timezone).do(dofunc).tag(tag)
        if daynumber == 6:
            schedule.every().saturday.at(spraytime, self.timezone).do(dofunc).tag(tag)


    def schedule_sprays(self):
        # clear existing schedule and thread as a reset
        schedule.clear()
        for spray_zone in self.zones:
            # TODO: may need offset for zones that spray at the same time
            for sprayoccurence in spray_zone.sprayoccurrences:
                # handle each day (see constants.py dayofweekmap)
                if sprayoccurence["timeofday"]["type"] == "fixedtime":
                    spraytime = "%02d:%02d" % (sprayoccurence["timeofday"]["value"][0], sprayoccurence["timeofday"]["value"][1])
                    self.schedule_dayofweek(sprayoccurence["dayofweek"], spraytime, spray_zone.execute_spray, "fixedtime")
                # handle only relative time
                if sprayoccurence["timeofday"]["type"] == "relativetime":
                    # see environment for structure of sundata and constants.py for structure of sprayoccurrence
                    sundata = self.env.get_sundata()
                    suntime = sundata[sprayoccurence["timeofday"]["value"]["sunevent"]]
                    deltaminutes = datetime.timedelta(minutes=sprayoccurence["timeofday"]["value"]["deltaminutes"])
                    # adjust suntime for timedelta
                    if sprayoccurence["timeofday"]["value"]["sunposition"] == "before":
                        spraytime_dt = suntime - deltaminutes
                    elif sprayoccurence["timeofday"]["value"]["sunposition"] == "after":
                        spraytime_dt = suntime + deltaminutes
                    else:
                        pass # TODO handle error
                    # create scheduled based on adjusted spraytime
                    spraytime = "%02d:%02d" % (spraytime_dt.hour, spraytime_dt.minute)
                    self.schedule_dayofweek(sprayoccurence["dayofweek"], spraytime, spray_zone.execute_spray, "relativetime")


if __name__ == '__main__':
    mydevice = device()
    mydevice.schedule_sprays()
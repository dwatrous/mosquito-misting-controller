# Copyright MosquitoMax 2022, all rights reserved

import sched
import threading
import schedule
import zone
import constants
import json
import time
import datetime
from environment import environment
from threading import Thread
from pytz import timezone

class device:
    zone_scheduler = sched.scheduler(timefunc=time.time)

    def __init__(self, devicedefinition=None) -> None:
        self.zones = []
        self.env = environment()

        if devicedefinition == None:
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
        self.environment_city = devicedefinition["environment_city"]
        self.low_temp_threshold_f = devicedefinition["low_temp_threshold_f"]
        self.rain_threshold_in = devicedefinition["rain_threshold_in"]
        self.timezone = devicedefinition["timezone"]
        self.zones = devicedefinition["zones"]

    def get_devicedefinition(self):
        devicedefinition = {
            "street1": self.street1,
            "street2": self.street2,
            "city": self.city,
            "state": self.state,
            "zip": self.zip,
            "environment_city": self.environment_city,
            "low_temp_threshold_f": self.low_temp_threshold_f,
            "rain_threshold_in": self.rain_threshold_in,
            "timezone": self.timezone,
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
    def schedule_sprays(self, interval=60):
        self.schedule_fixed_spray_times()
        self.schedule_relative_scheduler()
        # https://schedule.readthedocs.io/en/stable/background-execution.html
        cease_continuous_run = threading.Event()

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not cease_continuous_run.is_set():
                    schedule.run_pending()
                    time.sleep(interval)

        continuous_thread = ScheduleThread()
        continuous_thread.start()
        return cease_continuous_run


    def schedule_fixed_spray_times(self):
        for spray_zone in self.zones:
            # TODO: may need offset for zones that spray at the same time
            for sprayoccurence in spray_zone.sprayoccurrences:
                # handle each day (see constants.py dayofweekmap)
                if sprayoccurence["timeofday"]["type"] == "fixedtime" and sprayoccurence["dayofweek"] == 0:
                    spraytime = "%02d:%02d" % (sprayoccurence["timeofday"]["value"][0], sprayoccurence["timeofday"]["value"][1])
                    schedule.every().sunday.at(spraytime, self.timezone).do(spray_zone.execute_spray)
                if sprayoccurence["timeofday"]["type"] == "fixedtime" and sprayoccurence["dayofweek"] == 1:
                    spraytime = "%02d:%02d" % (sprayoccurence["timeofday"]["value"][0], sprayoccurence["timeofday"]["value"][1])
                    schedule.every().monday.at(spraytime, self.timezone).do(spray_zone.execute_spray)
                if sprayoccurence["timeofday"]["type"] == "fixedtime" and sprayoccurence["dayofweek"] == 2:
                    spraytime = "%02d:%02d" % (sprayoccurence["timeofday"]["value"][0], sprayoccurence["timeofday"]["value"][1])
                    schedule.every().tuesday.at(spraytime, self.timezone).do(spray_zone.execute_spray)
                if sprayoccurence["timeofday"]["type"] == "fixedtime" and sprayoccurence["dayofweek"] == 3:
                    spraytime = "%02d:%02d" % (sprayoccurence["timeofday"]["value"][0], sprayoccurence["timeofday"]["value"][1])
                    schedule.every().wednesday.at(spraytime, self.timezone).do(spray_zone.execute_spray)
                if sprayoccurence["timeofday"]["type"] == "fixedtime" and sprayoccurence["dayofweek"] == 4:
                    spraytime = "%02d:%02d" % (sprayoccurence["timeofday"]["value"][0], sprayoccurence["timeofday"]["value"][1])
                    schedule.every().thursday.at(spraytime, self.timezone).do(spray_zone.execute_spray)
                if sprayoccurence["timeofday"]["type"] == "fixedtime" and sprayoccurence["dayofweek"] == 5:
                    spraytime = "%02d:%02d" % (sprayoccurence["timeofday"]["value"][0], sprayoccurence["timeofday"]["value"][1])
                    schedule.every().friday.at(spraytime, self.timezone).do(spray_zone.execute_spray)
                if sprayoccurence["timeofday"]["type"] == "fixedtime" and sprayoccurence["dayofweek"] == 6:
                    spraytime = "%02d:%02d" % (sprayoccurence["timeofday"]["value"][0], sprayoccurence["timeofday"]["value"][1])
                    schedule.every().saturday.at(spraytime, self.timezone).do(spray_zone.execute_spray)

    # start relative time scheduler
    def schedule_relative_scheduler(self):
        sundata = self.env.get_sundata()
        for spray_zone in self.zones:
            for sprayoccurence in spray_zone.sprayoccurrences:
                if sprayoccurence["timeofday"]["type"] == "relativetime":
                    # need a scheduler to run an hour or so before each possible event
                    # note that it doesn't really mattere when this sprayoccurence is 
                    # since we're not scheduling the actual spray right now
                    suntime = sundata["dawn"] - datetime.timedelta(hours=1, minutes=5)
                    schedule_time = "%02d:%02d" % (suntime.hour, suntime.minute)
                    schedule.every().day.at(schedule_time, self.timezone).do(self.schedule_relative_spray)
                    suntime = sundata["sunset"] - datetime.timedelta(hours=1, minutes=5)
                    schedule_time = "%02d:%02d" % (suntime.hour, suntime.minute)
                    schedule.every().day.at(schedule_time, self.timezone).do(self.schedule_relative_spray)
                    # since we found a relative time, we only need the schedulers, so we can break
                    break
        
    def schedule_relative_spray(self):
        now = datetime.datetime.now(tz=timezone(self.timezone))
        # use priority to offset zones that spray at the same time
        priority = 0
        currentday = now.weekday()
        sundata = self.env.get_sundata()
        for spray_zone in self.zones:
            priority = priority + 1
            for sprayoccurence in spray_zone.sprayoccurrences:
                if sprayoccurence["dayofweek"] == currentday:
                    # handle only relative time
                    if sprayoccurence["timeofday"]["type"] == "relativetime":
                        # see environment for structure of sundata and constants.py for structure of sprayoccurrence
                        suntime = sundata[sprayoccurence["timeofday"]["value"]["sunevent"]]
                        deltaminutes = datetime.timedelta(minutes=sprayoccurence["timeofday"]["value"]["deltaminutes"])
                        # adjust suntime for timedelta
                        if sprayoccurence["timeofday"]["value"]["sunposition"] == "before":
                            spraytime = suntime - deltaminutes
                        elif sprayoccurence["timeofday"]["value"]["sunposition"] == "after":
                            spraytime = suntime + deltaminutes
                        else:
                            pass # TODO handle error
                        # create scheduled based on adjusted spraytime
                        time_until_spraytime = spraytime - now
                        if time_until_spraytime.total_seconds() < constants.DEVICE_SCHEDULE_AHEAD_THRESHOLD_SECONDS:
                            scheduled = datetime.datetime(
                                spraytime.year, 
                                spraytime.month, 
                                spraytime.day, 
                                spraytime.hour, 
                                spraytime.minute,
                                tzinfo=timezone(self.timezone)
                            )
                            self.zone_scheduler.enterabs(time.mktime(scheduled.timetuple()), priority, spray_zone.execute_spray)

        t = Thread(target=self.zone_scheduler.run)
        t.start()

    # app/online connection

    # on board sensors
    def read_current_line_pressure(self):
        pass

    def read_current_vacuum_pressure(self):
        pass

if __name__ == '__main__':
    mydevice = device()
    mydevice.schedule_sprays()
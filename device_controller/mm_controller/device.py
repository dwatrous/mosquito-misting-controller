# Copyright MosquitoMax 2022, all rights reserved

import logging
import subprocess
import threading
import schedule
import json
import time
import datetime
from importlib.metadata import version

from mm_controller import zone
from mm_controller import device_sensors
from mm_controller import constants
from mm_controller import cloud
from mm_controller import calibrate_device
from mm_controller.environment import environment
from mm_controller.utils import app_log, Config

class device:

    def __init__(self, initialize=False) -> None:
        self.zones = []
        self.env = environment()
        self.schedule_thread_kill_signal = threading.Event()
        self.device_cloud = cloud.Cloud()
        self.global_config = Config()

        devicerecord = self.device_cloud.device_get()

        if devicerecord == None or initialize == True:
            self.state = constants.default_state
            self.zip = constants.default_zip
            self.environment_city = constants.default_environment_city
            self.low_temp_threshold_f = constants.default_low_temp_threshold_f
            self.rain_threshold_in = constants.default_rain_threshold_in
            self.timezone = constants.default_timezone
            self.solution_capacity = constants.default_solution_capacity
            self.zones.append(zone.zone())
        else:
            self.load_devicedefinition_from_cloud()

        # schedule sprays and start schedule thread (skip on register)
        if initialize == False:
            self.check_system()
            # TODO if system isn't ready, signal error and don't schedule sprays
            self.schedule_sprays()
            self.start_schedule_thread()
            self.send_status_update()

    def load_devicedefinition_from_cloud(self, reload=False):
        if reload:
            self.device_cloud.device_details_reload = True
        devicerecord = self.device_cloud.device_get()

        # if a JSON was passed directly, change it to a dict
        if type(devicerecord) is not dict:
            devicerecord = json.loads(devicerecord)

        self.devicedefinition = devicerecord["config"]
    
        # hydrate based on devicedefinition
        self.state = self.devicedefinition["state"]
        self.zip = self.devicedefinition["zip"]
        self.environment_city = self.devicedefinition["environment_city"]
        self.low_temp_threshold_f = self.devicedefinition["low_temp_threshold_f"]
        self.rain_threshold_in = self.devicedefinition["rain_threshold_in"]
        self.timezone = self.devicedefinition["timezone"]
        self.solution_capacity = self.devicedefinition["solution_capacity"]
        self.zones = [zone.zone(devicezone, low_temp_threshold_f=self.low_temp_threshold_f, rain_threshold_in=self.rain_threshold_in) for devicezone in self.devicedefinition["zones"]]

    def get_devicedefinition(self):
        devicedefinition = {
            "state": self.state,
            "zip": self.zip,
            "environment_city": self.environment_city,
            "low_temp_threshold_f": self.low_temp_threshold_f,
            "rain_threshold_in": self.rain_threshold_in,
            "timezone": self.timezone,
            "solution_capacity": self.solution_capacity,
            "zones": [devicezone.get_zonedefinition() for devicezone in self.zones]
        }
        return devicedefinition
    
    def get_devicedefinition_json(self):
        return json.dumps(self.get_devicedefinition())

    def message_handler(self, message):
        # see cloud.py _build_message function for message structure
        app_log.info("Received message: %s", message)
        # handle SPRAYNOW
        if message["message"]["event"] == "SPRAYNOW":
            # TODO need to change this when implementing multiple zones
            self.zones[0].execute_spray(skip_override=True, spray_event="USER")
            self.send_status_update()
        if message["message"]["event"] == "SPRAYWATER":
            # TODO need to change this when implementing multiple zones
            self.zones[0].execute_spray(skip_override=True, spray_event="USER", water_only=True)
            self.send_status_update()
        if message["message"]["event"] == "REFRESHCONFIG":
            self.load_devicedefinition_from_cloud(reload=True)
            self.schedule_sprays()
            self.send_status_update()
        if message["message"]["event"] == "STATUS":
            self.send_status_update()
        if message["message"]["event"] == "SKIPNEXT":
            self.cancel_next_spray()
            self.send_status_update()
        if message["message"]["event"] == "CALIBRATE":
            if "SCALE" in message["message"]["info"]:
                app_log.info("Calibrating Scale")
                calibrate_device.calibrate(scale=True)
            if "LINE_IN" in message["message"]["info"]:
                app_log.info("Calibrating Line IN")
                calibrate_device.calibrate(line_in=True)
            if "LINE_OUT" in message["message"]["info"]:
                app_log.info("Calibrating Line OUT")
                calibrate_device.calibrate(line_out=True)
            if "VACUUM" in message["message"]["info"]:
                app_log.info("Calibrating Vacuum")
                calibrate_device.calibrate(vacuum=True)
            self.send_status_update()
        if message["message"]["event"] == "UPGRADE":
            # use subprocess to pip install and then restart
            subprocess.Popen(["/home/mm/.ctrlenv/bin/mmctrl", "-u"])
        if message["message"]["event"] == "RESTART":
            # restart
            subprocess.Popen(["/home/mm/.ctrlenv/bin/mmctrl", "--restart"])
        return True

    def check_system(self):
        # TODO add expected thresholds for ready and update conditional
        if (device_sensors.read_current_line_in_pressure_psi() and device_sensors.read_current_weight()):
            device_sensors.status_led_ready()
    
    def send_status_update(self):
        try:
            software_version = version('mm_controller')
            latest_version = self.device_cloud.get_latest_release()
        except:
            software_version = "0.0.0"
            latest_version = "0.0.0"
        status_update = {"status": 
                            {
                                "line_in_pressure": device_sensors.read_current_line_in_pressure_psi(),
                                "solution_weight": device_sensors.read_current_weight(),
                                "next_spray": self.get_next_spraytime(),
                                "timestamp": datetime.datetime.utcnow(),
                                "version": software_version,
                                "latest_version": latest_version,
                                "upgrade_available": latest_version > software_version,
                                "wifi_signal_strength": self.global_config.wifi_signal_strength
                            }
                        }
        self.device_cloud.device_update(status_update)

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

        self.schedule_thread = ScheduleThread()
        self.schedule_thread.start()

    def schedule_daysofweek(self, daystospray, spraytime, dofunc, tag):
        logging.info({"schedule_daysofweek": {"daystospray": daystospray, "spraytime": spraytime, "dofunc": dofunc, "tag": tag}})
        if 0 in daystospray:
            schedule.every().sunday.at(spraytime, self.timezone).do(dofunc).tag(tag)
        if 1 in daystospray:
            schedule.every().monday.at(spraytime, self.timezone).do(dofunc).tag(tag)
        if 2 in daystospray:
            schedule.every().tuesday.at(spraytime, self.timezone).do(dofunc).tag(tag)
        if 3 in daystospray:
            schedule.every().wednesday.at(spraytime, self.timezone).do(dofunc).tag(tag)
        if 4 in daystospray:
            schedule.every().thursday.at(spraytime, self.timezone).do(dofunc).tag(tag)
        if 5 in daystospray:
            schedule.every().friday.at(spraytime, self.timezone).do(dofunc).tag(tag)
        if 6 in daystospray:
            schedule.every().saturday.at(spraytime, self.timezone).do(dofunc).tag(tag)

    def schedule_status_updates(self):
        schedule.every(10).minutes.do(self.send_status_update).tag("status_update")

    def schedule_sprays(self):
        # clear existing schedule and thread as a reset
        schedule.clear()
        for spray_zone in self.zones:
            # TODO: may need offset for zones that spray at the same time
            for sprayoccurence in spray_zone.sprayoccurrences:
                # handle each day (see constants.py daysofweekmap)
                if sprayoccurence["timeofday"]["type"] == "fixedtime":
                    spraytime = "%02d:%02d" % (sprayoccurence["timeofday"]["value"]["hour"], sprayoccurence["timeofday"]["value"]["minutes"])
                    self.schedule_daysofweek(sprayoccurence["daysofweek"], spraytime, spray_zone.execute_spray, "fixedtime")
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
                    self.schedule_daysofweek(sprayoccurence["daysofweek"], spraytime, spray_zone.execute_spray, "relativetime")
        self.schedule_status_updates()

    def get_next_spraytime(self):
        return self.get_next_spray().astimezone(datetime.timezone.utc)

    def get_next_spray(self):
        if not isinstance(schedule.next_run('fixedtime'), datetime.datetime) and isinstance(schedule.next_run('relativetime'), datetime.datetime):
            nextspray = schedule.next_run('fixedtime')
        elif not isinstance(schedule.next_run('relativetime'), datetime.datetime) and isinstance(schedule.next_run('fixedtime'), datetime.datetime):
            nextspray = schedule.next_run('fixedtime')
        elif schedule.next_run('fixedtime') > schedule.next_run('relativetime'):
            nextspray = schedule.next_run('relativetime')
        else:
            nextspray = schedule.next_run('fixedtime')
        return nextspray
    
    def cancel_next_spray(self):
        nextspray = self.get_next_spray()
        for pendingjob in schedule.get_jobs():
            if pendingjob.next_run == nextspray:
                schedule.cancel_job(pendingjob)

if __name__ == '__main__':
    mydevice = device()
    mydevice.schedule_sprays()
    print(mydevice.get_next_spraytime())
    mydevice.cancel_next_spray()
    print(mydevice.get_next_spraytime())
    mydevice.send_status_update()
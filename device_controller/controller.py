#!/usr/bin/env python
# Copyright MosquitoMax 2023, all rights reserved

# This is the main controller file

import datetime
from pytz import timezone
import constants
# import json
# from os.path import exists
from time import sleep
from device import device
import schedule
import cloud
from utils import Config, app_log

if __name__ == '__main__':
    # get Config
    config = Config()
    # get cloud object
    controller_cloud = cloud.Cloud()

    # handle first time setup
    # start wifi hotspot
    # start server to accept connection from the app
    # write initial device configuration file

    # Connect to cloud to check for existing device configuration
    clouddevice = controller_cloud.device_get()
    if clouddevice == None:
        print(u"No such device!") # TODO handle error
    # deviceconfigfile = Path(__file__).with_name("deviceconfig.json")
    # with deviceconfigfile.open("w") as configwriter:
    #     configwriter.write(json.dumps(device_config))
    # if WiFi unavailable, do ??? (need try/except to trigger a local run only)

    # create the device instance
    this_device = device(clouddevice["config"])
    # listen for messages from the cloud
    controller_cloud.listen_for_messages(this_device.message_handler)

    while True:
        # MESSAGES: reload configuration, spray now, skip next spray, get device status
        # check and send device status (hourly?) (may include error state that will be handled from the cloud)

        # periodically refresh schedule (daily should be fine)
        app_log.info("Next spray {0}".format(schedule.next_run()))
        app_log.info("waiting {0} seconds at {1}".format(constants.controller_wait_time, datetime.datetime.now(tz=timezone(constants.default_timezone))))
        controller_cloud.listen_for_messages_refresh()
        sleep(constants.controller_wait_time)


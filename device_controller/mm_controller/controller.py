#!/usr/bin/env python
# Copyright MosquitoMax 2023, all rights reserved

# This is the main controller file

import datetime
from pytz import timezone
from time import sleep

from mm_controller.device import device
from mm_controller import constants
from mm_controller import cloud
from mm_controller.utils import Config, app_log

def run():
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
    # if WiFi unavailable, do ??? (need try/except to trigger a local run only)

    # create the device instance
    this_device = device()
    # listen for messages from the cloud
    controller_cloud.listen_for_messages(this_device.message_handler)

    # open water valve for 30 seconds
    # TODO need to adjust for multiple zones in the future
    this_device.zones[0].open_valve(constants.VALVE_WATER, 30000)

    while True:
        # MESSAGES: reload configuration, spray now, skip next spray, get device status
        # check and send device status (hourly?) (may include error state that will be handled from the cloud)

        # periodically refresh schedule (daily should be fine)
        app_log.info("Next spray {0}".format(this_device.get_next_spraytime()))
        app_log.info("waiting {0} seconds at {1}".format(constants.controller_wait_time, datetime.datetime.now(tz=timezone(constants.default_timezone))))
        sleep(constants.controller_wait_time)

if __name__ == '__main__':
    run()
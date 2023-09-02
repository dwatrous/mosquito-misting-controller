#!/usr/bin/env python
# Copyright MosquitoMax 2023, all rights reserved

# This is the main controller file

import datetime
from pytz import timezone
import constants
import json
from os.path import exists
from time import sleep
from device import device
import schedule
import cloud
import utils

wait_time = 60

# get Config
config = utils.Config()
# get cloud object
controller_cloud = cloud.Cloud()

# handle first time setup
# start wifi hotspot
# start server to accept connection from the app
# write initial account configuration file

# Connect to cloud to check for existing device configuration
account = controller_cloud.account_get(config.get_config()["account_id"])
if account == None:
    print(u"No such account!") # TODO handle error
# check for empty devices and create default config
if account["devices"] == {}:
    new_default_device = device()
    account["devices"][config.get_config()["device"]["name"]] = new_default_device.get_devicedefinition()
    controller_cloud.account_update(config.get_config()["account_id"], account)
    new_default_device.schedule_thread_kill_signal.set()
    del new_default_device
# load device configuration if available (cloud first, then local)
try:
    device_config = account["devices"][config.get_config()["device"]["name"]]
except:
    print(u"No such device!") # TODO handle error
# deviceconfigfile = Path(__file__).with_name("deviceconfig.json")
# with deviceconfigfile.open("w") as configwriter:
#     configwriter.write(json.dumps(device_config))
# if WiFi unavailable, do ??? (need try/except to trigger a local run only)

if __name__ == '__main__':

    # create the device instance
    this_device = device(account["devices"][config.get_config()["device"]["name"]])
    # listen for messages from the cloud
    controller_cloud.listen_for_messages(this_device.message_handler)

    while True:
        # MESSAGES: reload configuration, spray now, skip next spray, get device status
        # check and send device status (hourly?) (may include error state that will be handled from the cloud)

        # periodically refresh schedule (daily should be fine)
        utils.app_log.info("Next spray {0}".format(schedule.next_run()))
        utils.app_log.info("waiting {0} seconds at {1}".format(wait_time, datetime.datetime.now(tz=timezone(constants.default_timezone))))
        sleep(wait_time)


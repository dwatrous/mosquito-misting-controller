#!/usr/bin/env python
# Copyright MosquitoMax 2022, all rights reserved

# This is the main controller file

import logging
from logging.handlers import TimedRotatingFileHandler

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
logFile = 'controller.log'

my_handler = TimedRotatingFileHandler(logFile, when="D", interval=1, backupCount=10, encoding='utf-8')
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.DEBUG)

app_log = logging.getLogger('root')
app_log.setLevel(logging.DEBUG)

app_log.addHandler(my_handler)

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

# handle first time setup
# start wifi hotspot
# start server to accept connection from the app
# write initial account configuration file

# Connect to cloud to check for existing device configuration
account_ref = cloud.db.collection(u"accounts").document(config.getConfig()["account_id"])
account_doc = account_ref.get()
if account_doc.exists:
    account = account_doc.to_dict()
else:
    print(u"No such account!") # TODO handle error
# check for empty devices and create default config
if account["devices"] == {}:
    new_default_device = device()
    account["devices"][config.getConfig()["device_name"]] = new_default_device.get_devicedefinition()
    account_ref.set(account)
    new_default_device.schedule_thread_kill_signal.set()
    del new_default_device
# load device configuration if available (cloud first, then local)
try:
    device_config = account["devices"][config.getConfig()["device_name"]]
except:
    print(u"No such device!") # TODO handle error
deviceconfigfile = Path(__file__).with_name("deviceconfig.json")
with deviceconfigfile.open("w") as configwriter:
    configwriter.write(json.dumps(device_config))
# if WiFi unavailable, do ??? (need try/except to trigger a local run only)

if __name__ == '__main__':

    # create the device instance
    this_device = device(account["devices"][config.getConfig()["device_name"]])

    while True:
        # listen for messages from the cloud
        # handle message
        # MESSAGES: reload configuration, spray now, skip next spray, get device status
        # check and send device status (hourly?) (may include error state that will be handled from the cloud)

        # periodically refresh schedule (daily should be fine)
        app_log.info("Next spray {0}".format(schedule.next_run()))
        app_log.info("waiting {0} seconds at {1}".format(wait_time, datetime.datetime.now(tz=timezone(constants.default_timezone))))
        sleep(wait_time)


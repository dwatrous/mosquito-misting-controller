#!/usr/bin/env python
# Copyright MosquitoMax 2022, all rights reserved

# This is the main controller file

import datetime
from pytz import timezone
import constants
import json
from os.path import exists
from time import sleep
from device import device

import firebase_admin
from firebase_admin import firestore
from pathlib import Path

wait_time = 60

# Application Default credentials are automatically created.
app = firebase_admin.initialize_app()
db = firestore.client()

# load in configuration
configfile = Path(__file__).with_name("config.json")
with configfile.open("r") as configreader:
    config = json.loads(configreader.read())

# handle first time setup
# start wifi hotspot
# start server to accept connection from the app
# write initial account configuration file

# Connect to cloud to check for existing device configuration
account_ref = db.collection(u"accounts").document(config["account_id"])
account_doc = account_ref.get()
if account_doc.exists:
    account = account_doc.to_dict()
else:
    print(u"No such account!") # TODO handle error
# check for empty devices and create default config
if account["devices"] == {}:
    new_default_device = device()
    account["devices"][config["device_name"]] = new_default_device.get_devicedefinition()
    account_ref.set(account)
    new_default_device.schedule_thread_kill_signal.set()
    del new_default_device
# load device configuration if available (cloud first, then local)
try:
    device_config = account["devices"][config["device_name"]]
except:
    print(u"No such device!") # TODO handle error
deviceconfigfile = Path(__file__).with_name("deviceconfig.json")
with deviceconfigfile.open("w") as configwriter:
    configwriter.write(json.dumps(device_config))
# if WiFi unavailable, do ??? (need try/except to trigger a local run only)

# create the device instance
this_device = device(account["devices"][config["device_name"]])

while True:
    # listen for messages from the cloud
    # handle message
    # MESSAGES: reload configuration, spray now, skip next spray, get device status
    # check and send device status (hourly?) (may include error state that will be handled from the cloud)

    # periodically refresh schedule (daily should be fine)
    print("waiting ", wait_time, " seconds at ", datetime.datetime.now(tz=timezone(constants.default_timezone)))
    sleep(wait_time)


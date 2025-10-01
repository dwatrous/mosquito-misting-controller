import requests
import json

from mm_controller.utils import Config, app_log
from mm_controller import cloud
from mm_controller.device import device
from mm_controller.constants import mm_api_host, mm_api_register, mm_api_password_reset

config = Config()
reg_cloud = cloud.Cloud()

device_info = {"device_email": config.device_email,"serial_number": config.device_serial_number, "mac_address": config.device_mac_address, "name": "My Mister"}
url = mm_api_host + mm_api_register
reset_url = mm_api_host + mm_api_password_reset

def is_registered():
    # check for existing password in config.json
    with config.configfile.open("r") as configreader:
        configfile_contents = json.loads(configreader.read())

    return configfile_contents["device"]["password"] != ""

def register():
    # call API to register device
    try:
        credentials = requests.post(url, json=device_info)
        creds = credentials.json()
    except:
        app_log.error("Call to %s failed" % url)
        app_log.error(credentials.content)
        exit(1)

    # write password to config.json
    with config.configfile.open("r") as configreader:
        configfile_contents = json.loads(configreader.read())

    configfile_contents["device"]["password"] = creds["device_password"]

    with config.configfile.open("w") as configwriter:
        json.dump(configfile_contents, configwriter, indent=4)

    # authenticate and confirm device registration
    config.reload = True

    # create default device config and save
    mydevice = reg_cloud.device_get()
    if "config" not in mydevice:
        new_default_device = device(initialize=True)
        mydevice["config"] = new_default_device.get_devicedefinition()
        reg_cloud.device_update(mydevice)
        del new_default_device

    app_log.info("Device Registerd")
    app_log.info(device_info)
    print("Device Registerd")

def reset_password():
    # call API to reset device password
    try:
        credentials = requests.post(reset_url, json=device_info)
        creds = credentials.json()
    except:
        app_log.error("Call to %s failed" % reset_url)
        app_log.error(credentials.content)
        exit(1)

    # write password to config.json
    with config.configfile.open("r") as configreader:
        configfile_contents = json.loads(configreader.read())

    configfile_contents["device"]["password"] = creds["device_password"]

    with config.configfile.open("w") as configwriter:
        json.dump(configfile_contents, configwriter, indent=4)

    # authenticate and confirm device registration
    config.reload = True

    app_log.info("Device Password Reset")
    app_log.info(device_info)
    print("Device Password Reset")

if __name__ == '__main__':
    register()
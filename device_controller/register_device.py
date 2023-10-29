import requests
from utils import Config, app_log
import json
import cloud
from device import device

config = Config()
reg_cloud = cloud.Cloud()

apihost = "https://mm-api-shbeom7lea-uc.a.run.app"
apipath = "/api/v1/device/register"

device_info = {"device_email": config.device_email,"serial_number": config.device_serial_number, "mac_address": config.device_mac_address, "name": "My Mister"}
url = apihost + apipath

# call API to register device
try:
    credentials = requests.post(url, json=device_info)
    creds = credentials.json()
except:
    app_log.error("Call to %s failed" % apipath)
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
device_account = reg_cloud.get_authenticated_device_account()

# create default device config and save
mydevice = reg_cloud.device_get()
if "config" not in mydevice:
    new_default_device = device()
    mydevice["config"] = new_default_device.get_devicedefinition()
    reg_cloud.device_update(mydevice)
    new_default_device.schedule_thread_kill_signal.set()
    del new_default_device

app_log.info("Device Registerd")
app_log.info(device_info)
print("Device Registerd")
import requests
from utils import Config, app_log
import json

config = Config()

apihost = "https://mm-api-shbeom7lea-uc.a.run.app"
apipath = "/api/v1/device/register"

device_info = {"serial_number": config.device_serial_number, "mac_address": config.device_mac_address}
url = apihost + apipath

# call API to register device
credentials = requests.post(url, json=device_info)
creds = credentials.json()

# write password to config.json
with config.configfile.open("r") as configreader:
    configfile_contents = json.loads(configreader.read())

configfile_contents["device"]["password"] = creds["device_password"]

with config.configfile.open("w") as configwriter:
    json.dump(configfile_contents, configwriter, indent=4)

app_log.info("Device Registerd")
app_log.info(device_info)
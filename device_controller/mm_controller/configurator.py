from time import sleep, time
from bottle import app, request, Bottle
from multiprocessing import Process, Queue
import subprocess

from mm_controller import cloud
from mm_controller.utils import Config

config = Config()
config_cloud = cloud.Cloud()
app = Bottle()

success_signal = "SUCCESS_EXIT"

# expects a JSON document 
# {"ssid": "[ssid]", "passkey": "[passkey]", "owner": "[uid]"}
@app.post('/configure')
def configure():
    configuration = request.json

    # update WiFi
    # https://www.raspberrypi.com/documentation/computers/configuration.html#wireless-lan-2
    # TODO think about errors, like bad ssid/passkey
    subprocess.run(["sudo", "raspi-config", "nonint", "do_wifi_ssid_passphrase", configuration["ssid"], configuration["passkey"]]) 
    subprocess.run(["sudo", "nmcli", "connection", "delete", "mm_hotspot"])

    # notify device to update device with "owner": [uid]
    config_cloud.device_update({"owner": configuration["owner"]})

    app.config["exitsignal"].put(success_signal)

    # FYI, this can never return because the connection is broken after configuring the new WiFi
    return "Configuration updated"

def runapp(exitsignal):
    app.config["exitsignal"] = exitsignal
    app.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == '__main__':
    now = time()
    exitsignal = Queue()
    server = Process(target=runapp, args=(exitsignal,))

    # turn on hotspot
    subprocess.run(["sudo", "nmcli", "connection", "add", "type", "wifi", "con-name", "mm_hotspot", "autoconnect", "no", "wifi.mode", "ap", "wifi.ssid", "mm_device", "ipv4.method", "shared"])
    subprocess.run(["sudo", "nmcli", "connection", "up", "mm_hotspot"])

    # start server
    server.start()

    # wait for complete, or timeout
    if exitsignal.get() == success_signal:
        print("Success, Exit")
        server.terminate()
        server.join()

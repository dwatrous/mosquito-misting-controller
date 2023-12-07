from time import sleep, time
from bottle import app, HTTPResponse, request, Bottle
from multiprocessing import Process, Queue
import subprocess

from mm_controller import cloud
from mm_controller.utils import Config, app_log

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

    # confirm that SSID is valid for this environment
    app_log.debug("Confirm SSID is valid")
    wifilist = subprocess.run(["/usr/bin/nmcli", "dev", "wifi", "list"], capture_output=True)
    wifilist_stdout = wifilist.stdout.decode("utf-8")
    if wifilist_stdout.find(configuration["ssid"]) < 0:
        return HTTPResponse(status=404, body="WiFi SSID not available")

    # attempt to connect to the provided ssid/passkey
    app_log.debug("Connect to new WiFi")
    connected = subprocess.run(["/usr/bin/sudo", "/usr/bin/nmcli", "device", "wifi", "connect", configuration["ssid"], "password", configuration["passkey"], "ifname", "wlan0"], capture_output=True)
    connected_stderr = connected.stderr.decode("utf-8")
    if connected_stderr.find("Timeout") > 0:
        subprocess.run(["/usr/bin/sudo", "/usr/bin/nmcli", "connection", "up", "mm_hotspot"])
        return HTTPResponse(status=400, body="WiFi connection failed") # never returned
    subprocess.run(["/usr/bin/sudo", "/usr/bin/nmcli", "connection", "delete", "mm_hotspot"])

    # notify device to update device with "owner": [uid]
    app_log.debug("Update device owner")
    config_cloud.device_update({"owner": configuration["owner"]})

    app.config["exitsignal"].put(success_signal)

    # FYI, this can never return because the connection is broken after configuring the new WiFi
    return "Configuration updated"

def runapp(exitsignal):
    app_log.debug("Starting Bottle app (REST endpoint)")
    app.config["exitsignal"] = exitsignal
    app.run(host='0.0.0.0', port=8080, debug=True)

def configurate():
    now = time()
    exitsignal = Queue()
    server = Process(target=runapp, args=(exitsignal,))

    # turn on hotspot
    subprocess.run(["/usr/bin/sudo", "/usr/bin/nmcli", "connection", "add", "type", "wifi", "con-name", "mm_hotspot", "autoconnect", "no", "wifi.mode", "ap", "wifi.ssid", "mm_device", "ipv4.method", "shared"])
    subprocess.run(["/usr/bin/sudo", "/usr/bin/nmcli", "connection", "up", "mm_hotspot"])

    # start server
    server.start()

    # wait for complete, or timeout
    if exitsignal.get() == success_signal:
        app_log.debug("Success: Exit")
        server.terminate()
        server.join()

if __name__ == '__main__':
    configurate()
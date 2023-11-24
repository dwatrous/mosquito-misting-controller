from time import sleep
import json
import logging
import multiprocessing
from pathlib import Path
import io
import logging
from logging.handlers import TimedRotatingFileHandler
import subprocess, time
import re

from mm_controller import constants

# filter idToken out of logs
jwt_regex = r"ey[\w-]*\.[\w-]*\.[\w-]*"
key_regex = r"key=([A-Za-z0-9]+)"
class secure_formatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        message = re.sub(jwt_regex, 'JWT', message)
        message = re.sub(key_regex, 'key=KEY', message)
        return message

formatter = secure_formatter('%(asctime)s %(levelname)s %(pathname)s :: %(funcName)s(%(lineno)d) %(message)s')    
logFile = 'device.log'

my_handler = TimedRotatingFileHandler(logFile, when="D", interval=1, backupCount=10, encoding='utf-8')
my_handler.setFormatter(formatter)
my_handler.setLevel(logging.DEBUG)

app_log = logging.getLogger('root')
app_log.setLevel(logging.DEBUG)

app_log.addHandler(my_handler)

def is_raspberrypi():
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower(): return True
    except Exception: pass
    return False

def start_hotspot():
    pass

# create a signal for the float switch, set when FALLING, clear with RISING
float_switch_signal = multiprocessing.Event()

onpi = False
if is_raspberrypi():
    onpi = True
    from gpiozero import RGBLED, Buzzer, DigitalOutputDevice, Button
    status_led = RGBLED(constants.GPIO_LED_RED, constants.GPIO_LED_GREEN, constants.GPIO_LED_BLUE, active_high=False)
    buzzer = Buzzer(constants.GPIO_BUZZER, active_high=True)
    gpioctrl_motor = DigitalOutputDevice(constants.GPIO_MOTOR, active_high=constants.GPIO_RELAY_ACTIVE_HIGH)
    gpioctrl_chemical_valve = DigitalOutputDevice(constants.GPIO_CHEMICAL_VALVE, active_high=constants.GPIO_RELAY_ACTIVE_HIGH)
    gpioctrl_water_valve = DigitalOutputDevice(constants.GPIO_WATER_VALVE, active_high=constants.GPIO_RELAY_ACTIVE_HIGH)
    gpioctrl_float_switch = Button(constants.GPIO_FLOAT_SWITCH)
    gpioctrl_float_switch.when_pressed = float_switch_signal.set
    gpioctrl_float_switch.when_released = float_switch_signal.clear
    gpioctrl_reset_button = Button(constants.GPIO_RESET_BUTTON, hold_time=10)
    gpioctrl_reset_button.when_held = start_hotspot
else:
    # ensure Python doesn't complain about these not being defined when not on a pi
    status_led = object
    buzzer = object
    gpioctrl_motor = object
    gpioctrl_chemical_valve = object
    gpioctrl_water_valve = object
    gpioctrl_float_switch = object
    gpioctrl_reset_button = object

app_log.info("On Raspberry Pi: %s", onpi)

class Config(object):
    config = None
    reload = False
    serial_number = None
    mac_address = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Config, cls).__new__(cls)
        return cls.instance
    
    @property
    def device_email(self):
        return self.device_serial_number + "@" + constants.email_representation_domain
        
    @property
    def device_serial_number(self):
        if self.serial_number == None:
            try:
                with open("/sys/firmware/devicetree/base/serial-number", "r") as sno:
                    self.serial_number = sno.read().rstrip('\x00')
            except:
                self.serial_number = "0000000000000000"
        return self.serial_number

    @property
    def device_mac_address(self):
        if self.mac_address == None:
            try:
                with open("/sys/class/net/wlan0/address", "r") as mac:
                    self.mac_address = mac.read().rstrip('\n')
            except:
                self.mac_address = "00:00:00:00:00:00"
        return self.mac_address

    @property
    def device_password(self):
        return self.get_config()["device"]["password"]

    @property
    def configfile(self):
        return Path("/home").joinpath("mm").joinpath("config.json")
    
    def get_config(self):
        # TODO accommodate remote update of config values to force reload
        if self.config == None or self.reload:
            with self.configfile.open("r") as configreader:
                self.config = json.loads(configreader.read())
            self.reload = False
        return self.config

if __name__ == '__main__':
    config = Config()
    other_config = Config()
    print(config is other_config)
    print(config.get_config() == other_config.get_config())
    print(other_config.get_config())
    print(config.device_email)
    print(config.device_password)
    print(config.device_serial_number)
    print(config.device_mac_address)
import constants
from time import sleep
import json
import atexit
import logging
import multiprocessing
from pathlib import Path
import io
import logging
from logging.handlers import TimedRotatingFileHandler

# TODO need to filter idToken out of logs
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
logFile = 'device.log'

my_handler = TimedRotatingFileHandler(logFile, when="D", interval=1, backupCount=10, encoding='utf-8')
my_handler.setFormatter(log_formatter)
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
    buzzer = Buzzer(constants.GPIO_BUZZER, active_high=False)
    gpioctrl_motor = DigitalOutputDevice(constants.GPIO_MOTOR, active_high=False)
    gpioctrl_chemical_valve = DigitalOutputDevice(constants.GPIO_CHEMICAL_VALVE, active_high=False)
    gpioctrl_water_valve = DigitalOutputDevice(constants.GPIO_WATER_VALVE, active_high=False)
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

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Config, cls).__new__(cls)
        return cls.instance

    def get_config(self):
        # TODO accommodate remote update of config values to force reload
        if self.config == None or self.reload:
            configfile = Path(__file__).with_name("config.json")
            with configfile.open("r") as configreader:
                self.config = json.loads(configreader.read())
        return self.config

if __name__ == '__main__':
    config = Config()
    other_config = Config()
    print(config is other_config)
    print(config.get_config() == other_config.get_config())
    print(other_config.get_config())
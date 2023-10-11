import constants
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

onpi = False
GPIO = object
if is_raspberrypi():
    onpi = True
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)  # choose BCM for Raspberry pi GPIO numbers
    GPIO.setup(constants.GPIO_CHEMICAL_VALVE, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(constants.GPIO_WATER_VALVE, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(constants.GPIO_MOTOR, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(constants.GPIO_FLOAT_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(constants.GPIO_RESET_BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(constants.GPIO_BUZZER, GPIO.OUT, initial=GPIO.LOW)
    atexit.register(GPIO.cleanup)

app_log.info("On Raspberry Pi: %s", onpi)

# create a signal for the float switch, set when FALLING, clear with RISING
float_switch_signal = multiprocessing.Event()
if onpi:
    GPIO.add_event_detect(constants.GPIO_FLOAT_SWITCH, GPIO.FALLING, callback=float_switch_signal.set)
    # GPIO.add_event_detect(constants.GPIO_FLOAT_SWITCH, GPIO.RISING, callback=float_switch_signal.clear)

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
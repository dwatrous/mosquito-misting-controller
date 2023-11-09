# Copyright MosquitoMax 2022, all rights reserved

import constants
import atexit
import time
import utils
from time import sleep
import logging

if utils.is_raspberrypi():
    # setup ADS1115
    import Adafruit_ADS1x15
    adc = Adafruit_ADS1x15.ADS1115()
    # reduce logging from I2C
    adc._device._logger.setLevel(logging.INFO)
    # setup HX711 scale
    config = utils.Config()
    from hx711 import HX711
    hx = HX711(constants.GPIO_WEIGHT_DATA, constants.GPIO_WEIGHT_SCK)
    # hx.reset()    # This doesn't seem to be needed/helpful
    # the referen_unit converts the measurement to OZ
    hx.set_reference_unit(constants.SCALE_RAW_TO_OZ_REFERENCE)
    # setting the offset is how to tare the scale
    # hx.tare() captures several readings and uses those to find and set the offset
    hx.set_offset(config.get_config()["device"]["scale_offset"])
else:
    # ensure Python doesn't complain about these not being defined
    adc = object
    hx = object

# Pressure sensor details
# Range: 0-300 PSI
# Input: 5V DC
# Output: 0.5-4.5 V
# Given ADS1115 reads based on input from 0-4.096 V, a gain of 2/3 moves that to +/-6.144V
ADC_GAIN = 2/3
ADC_MAX_V = 6.144
# Given ADS1115 outputs -32768 to 32767, it should be expected that the 
# lowest input value of 0.5 V will produce a floor of about (0.5/4.5) * 32767 = 3641
SENSOR_MAX_ADC = 32767
SENSOR_ZERO = 0.5/ADC_MAX_V * SENSOR_MAX_ADC
SENSOR_MAX = 4.5/ADC_MAX_V * SENSOR_MAX_ADC
# PSI calculation should be (OUT - 3641)/(32767-3641)
SENSOR_PRESSURE_LINE_OUT_MAX_PSI = 300
SENSOR_PRESSURE_LINE_IN_MAX_PSI = 100
SENSOR_VACUUM_MAX_NEG_KPA = 40
ATMOSPHERE_PSI = 14.696 # https://en.wikipedia.org/wiki/Atmospheric_pressure
ADC_SLOPE_LINE_OUT = (SENSOR_PRESSURE_LINE_OUT_MAX_PSI-0)/(SENSOR_MAX-SENSOR_ZERO)
ADC_B_LINE_OUT = SENSOR_ZERO * ADC_SLOPE_LINE_OUT
ADC_SLOPE_LINE_IN = (SENSOR_PRESSURE_LINE_IN_MAX_PSI-0)/(SENSOR_MAX-SENSOR_ZERO)
ADC_B_LINE_IN = SENSOR_ZERO * ADC_SLOPE_LINE_IN
ADC_SLOPE_VACUUM = (SENSOR_VACUUM_MAX_NEG_KPA-0)/(SENSOR_MAX-SENSOR_ZERO)
ADC_B_VACUUM = SENSOR_ZERO * ADC_SLOPE_VACUUM

# calibration functions
def calibrate_scale():
    if utils.onpi:
        return hx.tare()
    else:
        return -1

def calibrate_line_in():
    if utils.onpi:
        current_pressure = adc.read_adc(constants.ADC_CHANNEL_LINE_IN_PRESSURE, gain=ADC_GAIN)
        return (ADC_SLOPE_LINE_IN * current_pressure) - ATMOSPHERE_PSI
    else:
        return -1

def calibrate_line_out():
    if utils.onpi:
        current_pressure = adc.read_adc(constants.ADC_CHANNEL_LINE_OUT_PRESSURE, gain=ADC_GAIN)
        return (ADC_SLOPE_LINE_OUT * current_pressure) - ATMOSPHERE_PSI
    else:
        return -1

def calibrate_vacuum():
    if utils.onpi:
        current_pressure = adc.read_adc(constants.ADC_CHANNEL_VACUUM, gain=ADC_GAIN)
        return (ADC_SLOPE_VACUUM * current_pressure)
    else:
        return -1

# on board sensors
def read_current_line_in_pressure_psi():
    if utils.onpi:
        current_pressure = adc.read_adc(constants.ADC_CHANNEL_LINE_IN_PRESSURE, gain=ADC_GAIN)
        return (ADC_SLOPE_LINE_IN * current_pressure) - config.get_config()["device"]["line_in_offset_psi"]
    else:
        return -1

def read_current_line_out_pressure_psi():
    if utils.onpi:
        current_pressure = adc.read_adc(constants.ADC_CHANNEL_LINE_OUT_PRESSURE, gain=ADC_GAIN)
        return (ADC_SLOPE_LINE_OUT * current_pressure) - config.get_config()["device"]["line_out_offset_psi"]
    else:
        return -1

def read_current_vacuum_pressure_kpa():
    if utils.onpi:
        current_vacuum = adc.read_adc(constants.ADC_CHANNEL_VACUUM, gain=ADC_GAIN)
        return (ADC_SLOPE_VACUUM * current_vacuum) - config.get_config()["device"]["vacuum_offset_kpa"]
        return (current_vacuum - SENSOR_ZERO)/(SENSOR_MAX-SENSOR_ZERO)*SENSOR_VACUUM_MAX_NEG_KPA
    else:
        return -1

def read_current_weight():
    if utils.onpi:
        weight = hx.get_weight(3)   # TODO not sure if this needs to be configurable at some point
        time.sleep(0.1)
        return weight
    else:
        return -1

# Manage LED
def status_led_ready():
    if utils.onpi:
        utils.status_led.on()
    else:
        "LED: ready"

def status_led_disable():
    if utils.onpi:
        utils.status_led.off()
    else:
        "LED: disabled"

def status_led_running():
    if utils.onpi:
        utils.status_led.blink(on_color=(0,1,0.5))
    else:
        "LED: running"

def status_led_error():
    if utils.onpi:
        utils.status_led.blink(on_color=(1,0,0))
    else:
        "LED: error"

# Manage Buzzer
def status_buzzer_beep(beepfor_s = 20):
    if utils.onpi:
        utils.buzzer.beep()
    else:
        "BUZZER: beep start"
    sleep(beepfor_s)
    if utils.onpi:
        utils.buzzer.off()
    else:
        "BUZZER: beep end"
    

def status_buzzer_off():
    if utils.onpi:
        utils.buzzer.off()
    else:
        "BUZZER: off"

if __name__ == '__main__':
    from time import sleep
    print("Buzzer beep")
    status_buzzer_beep()
    print("LED Ready")
    status_led_ready()
    sleep(6)
    print("LED Error")
    status_led_error()
    sleep(6)
    print("LED Running")
    status_led_running()
    sleep(6)
    print("LED Disable")
    status_led_disable()
    while True:
        print("Current Line In Pressure: ", read_current_line_in_pressure_psi())
        print("Current Line Out Pressure: ", read_current_line_out_pressure_psi())
        print("Current Vacuum: ", read_current_vacuum_pressure_kpa())
        print("Current Weight in OZ: ", read_current_weight())
        print("Reset Button: ", utils.gpioctrl_reset_button.value)
        print("Float Switch: ", utils.gpioctrl_float_switch.value)
        print("Float Signal: ", utils.float_switch_signal.is_set())
        sleep(4)


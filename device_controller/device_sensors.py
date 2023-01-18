# Copyright MosquitoMax 2022, all rights reserved

import constants
import atexit
import time

import sys, os
adc_gain = 2/3
if sys.platform == 'linux':
    if os.uname().nodename == 'raspberrypi':
        onpi = True
        import Adafruit_ADS1x15
        adc = Adafruit_ADS1x15.ADS1115()
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)  # choose BCM for Raspberry pi GPIO numbers
        from hx711 import HX711
        hx = HX711(constants.GPIO_WEIGHT_DATA, constants.GPIO_WEIGHT_SCK)
        hx.set_reading_format("MSB", "MSB")
        reference_unit = 1
        hx.set_reference_unit(reference_unit)
        hx.reset()
        hx.tare()
        atexit.register(GPIO.cleanup)
else:
    onpi = False
    # ensure Python doesn't complain about these not being defined
    adc = object
    hx = object

# on board sensors
def read_current_line_in_pressure():
    if onpi:
        return adc.read_adc(constants.ADC_CHANNEL_LINE_IN_PRESSURE, gain=adc_gain)
    else:
        return -1

def read_current_line_out_pressure():
    if onpi:
        return adc.read_adc(constants.ADC_CHANNEL_LINE_OUT_PRESSURE, gain=adc_gain)
    else:
        return -1

def read_current_vacuum_pressure():
    if onpi:
        return adc.read_adc(constants.ADC_CHANNEL_VACUUM, gain=adc_gain)
    else:
        return -1

def read_current_weight():
    if onpi:
        weight = hx.get_weight(5)
        hx.reset()
        time.sleep(0.1)
        return weight
    else:
        return -1
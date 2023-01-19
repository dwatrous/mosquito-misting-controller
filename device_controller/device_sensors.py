# Copyright MosquitoMax 2022, all rights reserved

import constants
import atexit
import time

import sys, os
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

# Pressure sensor details
# Range: 0-300 PSI
# Input: 5V DC
# Output: 0.5-4.5 V
# Given ADS1115 reads based on input from 0-4.096 V, a gain of 2/3 moves that to +/-6.144V
ADC_GAIN = 2/3
ADC_MAX_V = 6.144
# Given ADS1115 outputs -32768 to 32767, it should be expected that the 
# lowest input value of 0.5 V will product a floor of about (0.5/4.5) * 32767 = 3641
SENSOR_MAX_ADC = 32767
SENSOR_ZERO = 0.5/ADC_MAX_V * SENSOR_MAX_ADC
SENSOR_MAX = 4.5/ADC_MAX_V * SENSOR_MAX_ADC
# PSI calculation should be (OUT - 3641)/(32767-3641)
SENSOR_PRESSURE_MAX_PSI = 300
SENSOR_VACUUM_MAX_NEG_KPA = 40

# on board sensors
def read_current_line_in_pressure_psi():
    if onpi:
        current_pressure = adc.read_adc(constants.ADC_CHANNEL_LINE_IN_PRESSURE, gain=ADC_GAIN)
        return (current_pressure - SENSOR_ZERO)/(SENSOR_MAX-SENSOR_ZERO)*SENSOR_PRESSURE_MAX_PSI
    else:
        return -1

def read_current_line_out_pressure_psi():
    if onpi:
        current_pressure = adc.read_adc(constants.ADC_CHANNEL_LINE_OUT_PRESSURE, gain=ADC_GAIN)
        return (current_pressure - SENSOR_ZERO)/(SENSOR_MAX-SENSOR_ZERO)*SENSOR_PRESSURE_MAX_PSI
    else:
        return -1

def read_current_vacuum_pressure_kpa():
    if onpi:
        current_vacuum = adc.read_adc(constants.ADC_CHANNEL_VACUUM, gain=ADC_GAIN)
        return (current_vacuum - SENSOR_ZERO)/(SENSOR_MAX-SENSOR_ZERO)*SENSOR_VACUUM_MAX_NEG_KPA
    else:
        return -1

def read_current_weight():
    if onpi:
        weight = hx.get_weight(5)   # TODO not sure if this needs to be configurable at some point
        hx.reset()
        time.sleep(0.1)
        return weight
    else:
        return -1
import constants
from device import device
import zone_test
import os

# create zone instance
mydevice = device()

# assert default values
assert mydevice.state == constants.default_state
assert mydevice.zip == constants.default_zip
assert len(mydevice.zones) == 1
# assert timing in zone
mydevice_zone0 = mydevice.zones[0]
assert mydevice_zone0.calculate_valve_openings() == zone_test.expected_default_timing

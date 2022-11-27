import datetime
import os
from time import sleep

import constants
import zone_test
from device import device
from freezegun import freeze_time

# create zone instance
mydevice = device()

# assert default values
assert mydevice.state == constants.default_state
assert mydevice.zip == constants.default_zip
assert len(mydevice.zones) == 1
# assert timing in zone
mydevice_zone0 = mydevice.zones[0]
assert mydevice_zone0.calculate_valve_openings() == zone_test.expected_default_timing

trigger_now = datetime.datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)

if __name__ == '__main__':
    with freeze_time(trigger_now):
        mydevice.schedule_sprays()
        while True:
            print("waiting 1 minute at ", datetime.datetime.now())
            sleep(60)

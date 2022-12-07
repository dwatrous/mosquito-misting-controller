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

trigger_now = datetime.datetime.now().replace(hour=22, minute=59, second=37, microsecond=0)
test_duration = trigger_now

if __name__ == '__main__':
    with freeze_time(trigger_now, tick=True):
        scheduler = mydevice.schedule_sprays()
        while True:
            print("waiting 15 seconds at ", datetime.datetime.now())
            sleep(15)
            if datetime.datetime.now() - test_duration > datetime.timedelta(minutes=3): break
        scheduler.set()

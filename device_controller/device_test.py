import datetime
import os
from time import sleep
import schedule

import constants
import zone_test
from environment import environment
from device import device
import time_machine
from pytz import timezone

# create zone instance
mydevice = device()

# assert default values
assert mydevice.state == constants.default_state
assert mydevice.zip == constants.default_zip
assert len(mydevice.zones) == 1
# assert timing in zone
mydevice_zone0 = mydevice.zones[0]
assert mydevice_zone0.calculate_valve_openings() == zone_test.expected_default_timing

env = environment()

if __name__ == '__main__':
    #run a fixed time spray
    # trigger_now = datetime.datetime.now().replace(hour=22, minute=59, second=37, microsecond=0)
    # test_duration = trigger_now
    # with freeze_time(trigger_now, tick=True):
    #     scheduler = mydevice.schedule_sprays()
    #     while True:
    #         print("waiting 15 seconds at ", datetime.datetime.now())
    #         sleep(15)
    #         if datetime.datetime.now() - test_duration > datetime.timedelta(minutes=3): break
    #     scheduler.set()

    # run a relative time spray
    sundata = env.get_sundata()
    # , timezone=timezone(constants.default_timezone)
    trigger_schedule = sundata["dawn"] - datetime.timedelta(hours=1, minutes=7, seconds=0)
    trigger_run = sundata["dawn"] + datetime.timedelta(minutes=4, seconds=49)
    test_duration = trigger_run
    with time_machine.travel(trigger_schedule, tick=True):
        scheduler = mydevice.schedule_sprays()
        schedule.get_jobs()
        next_run = schedule.next_run()
        while True:
            print("waiting 15 seconds at ", datetime.datetime.now(tz=timezone(constants.default_timezone)))
            sleep(15)
            if next_run != schedule.next_run(): break
        print("ready to change time")
        scheduler.set()

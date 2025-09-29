import datetime
import os
from time import sleep, time
import schedule
import time_machine
from pytz import timezone

import zone_test
from mm_controller import constants
from mm_controller.environment import environment
from mm_controller.device import device

devicedefinition_filename = "devicedefinition.json"
env = environment()

if __name__ == '__main__':
    # create device instance
    mydevice = device()

    # assert default values
    assert mydevice.state == constants.default_state
    assert mydevice.zip == constants.default_zip
    assert len(mydevice.zones) == 1
    # assert timing in zone
    mydevice_zone0 = mydevice.zones[0]
    assert mydevice_zone0.calculate_valve_openings() == zone_test.expected_default_timing

    # test save devicedefinition
    with open(devicedefinition_filename, "w") as savedfile:
        savedfile.write(mydevice.get_devicedefinition_json())

    # load from devicedefinition
    with open(devicedefinition_filename, "r") as savedfile:
        new_devicedefinition_json = savedfile.read()
    newdevice = device(initialize=True)
    # assert default values
    assert mydevice.state == constants.default_state
    assert mydevice.zip == constants.default_zip
    assert len(mydevice.zones) == 1

    if os.path.exists(devicedefinition_filename):
        os.remove(devicedefinition_filename)
    else:
        print("The file does not exist")

    # run a fixed time spray
    trigger_now = datetime.datetime.now(tz=timezone(constants.default_timezone)).replace(hour=22, minute=59, second=37, microsecond=0)
    test_duration = trigger_now
    with time_machine.travel(trigger_now, tick=True):
        while True:
            print("waiting 15 seconds at ", datetime.datetime.now(tz=timezone(constants.default_timezone)))
            sleep(15)
            if datetime.datetime.now(tz=timezone(constants.default_timezone)) - test_duration > datetime.timedelta(minutes=3): break

    # run a relative time spray
    sundata = env.get_sundata()
    # , timezone=timezone(constants.default_timezone)
    trigger_schedule = sundata["sunrise"] - datetime.timedelta(minutes=5, seconds=37)
    with time_machine.travel(trigger_schedule, tick=True):
        scheduler = mydevice.schedule_sprays()
        next_run = schedule.next_run()
        while True:
            print("waiting 15 seconds at ", datetime.datetime.now(tz=timezone(constants.default_timezone)))
            sleep(15)
            if next_run != schedule.next_run():
                mydevice.schedule_thread_kill_signal.set()
                break


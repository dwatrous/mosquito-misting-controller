import json

from mm_controller.device_sensors import calibrate_scale, calibrate_line_in, calibrate_line_out, calibrate_vacuum
from mm_controller.utils import Config, app_log

def calibrate(scale=False, line_in=False, line_out=False, vacuum=False):
    config = Config()

    # write calibration values to config.json
    with config.configfile.open("r") as configreader:
        configfile_contents = json.loads(configreader.read())

    if scale:
        configfile_contents["device"]["scale_offset"] = calibrate_scale()
        app_log.info("Scale Calibrated")
    if line_in:
        configfile_contents["device"]["line_in_offset_psi"] = calibrate_line_in()
        app_log.info("Line In Calibrated")
    if line_out:
        configfile_contents["device"]["line_out_offset_psi"] = calibrate_line_out()
        app_log.info("Line Out Calibrated")
    if vacuum:
        configfile_contents["device"]["vacuum_offset_kpa"] = calibrate_vacuum()
        app_log.info("Vacuum Calibrated")

    with config.configfile.open("w") as configwriter:
        json.dump(configfile_contents, configwriter, indent=4)

    app_log.info("Device Calibration Complete")
    app_log.info(configfile_contents["device"])
    print("Device Calibration Complete")

if __name__ == "__main__":
   calibrate(True,True,True,True)
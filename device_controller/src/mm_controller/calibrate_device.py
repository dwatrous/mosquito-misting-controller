from device_sensors import calibrate_scale, calibrate_line_in, calibrate_line_out, calibrate_vacuum
from utils import Config, app_log
import json

def calibrate_all():
    config = Config()

    # write calibration values to config.json
    with config.configfile.open("r") as configreader:
        configfile_contents = json.loads(configreader.read())

    configfile_contents["device"]["scale_offset"] = calibrate_scale()
    configfile_contents["device"]["line_in_offset_psi"] = calibrate_line_in()
    configfile_contents["device"]["line_out_offset_psi"] = calibrate_line_out()
    configfile_contents["device"]["vacuum_offset_kpa"] = calibrate_vacuum()

    with config.configfile.open("w") as configwriter:
        json.dump(configfile_contents, configwriter, indent=4)

    app_log.info("Device Calibrated")
    app_log.info(configfile_contents["device"])
    print("Device Calibrated")


if __name__ == "__main__":
   calibrate_all()
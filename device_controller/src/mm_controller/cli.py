import argparse
import sys
from mm_controller import device_sensors, calibrate_device, controller


def cli():
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--diagnostics", action="store_true", help="Run diagnostics.")
    parser.add_argument("-c", "--calibrate", action="store_true", help="Calibrate connected devices.")
    parser.add_argument("--validate", choices=["cloud", "weather"], help="Run various exercises to validate connectivity.")
    parser.add_argument("-l", "--loglevel", choices=["DEBUG", "INFO", "WARN", "ERROR"], default="INFO", help="Set logging level.")

    args = parser.parse_args()

    print("Log level: %s" % args.loglevel)
    if args.diagnostics:
        print("Running diagnostics...")
        device_sensors.rundiagnostics()
    elif args.calibrate:
        print("Running calibration...")
        calibrate_device.calibrate_all()
    elif args.validate == "cloud":
       pass
    elif args.validate == "weather":
       pass
    else:
        print("Run controller")
        controller.run()
    sys.exit(1)

if __name__ == "__main__":
   cli()
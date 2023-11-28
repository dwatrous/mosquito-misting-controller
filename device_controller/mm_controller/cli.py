import argparse
import sys
from importlib.metadata import version

from mm_controller import device_sensors, calibrate_device, controller, register_device


def cli():
    parser = argparse.ArgumentParser(prog='MosquitoMax Controller',
                    description='The is the MosquitoMax Controller. Use it to calibrate the device, run diagnostics and start the controller',
                    epilog='Contact MosquitoMax with questions')

    parser.add_argument("-s", "--start", action="store_true", help="Start the controller.")
    parser.add_argument("-v", "--version", action="store_true", help="Print version and exit.")
    parser.add_argument("-d", "--diagnostics", action="store_true", help="Run diagnostics.")
    parser.add_argument("-c", "--calibrate", action="store_true", help="Calibrate connected devices.")
    parser.add_argument("-r", "--register", action="store_true", help=argparse.SUPPRESS) # TODO secure this so consumers can't register devices
    parser.add_argument("--validate", choices=["cloud", "weather"], help="Run various exercises to validate connectivity.")
    parser.add_argument("-l", "--loglevel", choices=["DEBUG", "INFO", "WARN", "ERROR"], default="INFO", help="Set logging level.")

    args = parser.parse_args()

    print("Log level: %s" % args.loglevel)
    if args.version:
        print(version('mm_controller'))
        sys.exit(0)
    if args.calibrate:
        print("Running calibration...")
        calibrate_device.calibrate_all()
    if args.register:
        print("Running registration...")
        register_device.register()
    if args.diagnostics:
        print("Running diagnostics...")
        device_sensors.rundiagnostics()
    if args.validate == "cloud":
       pass
    elif args.validate == "weather":
       pass
    if args.start:
        print("Run controller")
        controller.run()
    sys.exit(0)

if __name__ == "__main__":
   cli()
import argparse
import sys
from importlib.metadata import version
import subprocess
from datetime import datetime, timedelta
import re

# Define the log file path
# TODO this may get out of sync with config
log_file = "/home/mm/device.log"

# Regular expression to extract timestamp
timestamp_regex = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})"

def service_is_running(minutes_back=2):
    with open(log_file, "r") as f:
        # Read the last line
        last_line = f.readlines()[-1].strip()

        # Extract the timestamp
        match = re.search(timestamp_regex, last_line)
        if match:
            timestamp_str = match.group(1)

            # Parse the timestamp into datetime object
            try:
                log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
            except ValueError:
                print(f"Error parsing timestamp: {timestamp_str}")

    # Get the current time
    current_time = datetime.now()

    # Check if the log time is within the past 2 minutes
    time_diff = current_time - log_time

    return time_diff < timedelta(minutes=minutes_back)

def restart_service_if_running():
    """Restarts the service if it is running."""
    if service_is_running():
        subprocess.run(["/usr/bin/sudo", "/usr/bin/systemctl", "restart", "mmctrl.service"])

def enable_service():
    """Enable and start the service (usually after registration)."""
    subprocess.run(["/usr/bin/sudo", "/usr/bin/systemctl", "enable", "--now", "mmctrl.service"])

def cli():
    parser = argparse.ArgumentParser(prog='mmctrl',
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
    print("Service running: %s" % service_is_running())
    if args.version:
        print(version('mm_controller'))
        sys.exit(0)
    if args.calibrate:
        print("Running calibration...")
        from mm_controller import calibrate_device
        calibrate_device.calibrate_all()
        restart_service_if_running()
    if args.register:
        print("Running registration...")
        from mm_controller import register_device
        if not register_device.is_registered():
            register_device.register()
            enable_service()
        else:
            print("Device password exists. Skipping...")
            restart_service_if_running()
    if args.diagnostics:
        print("Running diagnostics...")
        from mm_controller import device_sensors
        device_sensors.rundiagnostics()
        restart_service_if_running()
    if args.validate == "cloud":
       pass
    elif args.validate == "weather":
       pass
    if args.start:
        if not service_is_running():
            print("Run controller")
            from mm_controller import controller
            controller.run()
        else:
            print("Controller is running. Use /usr/bin/systemctl.")
    sys.exit(0)

if __name__ == "__main__":
   cli()
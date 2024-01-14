import argparse
import os
import re
import sys
from importlib.metadata import version
import subprocess
from datetime import datetime, timedelta
import psutil

# Define the log file path
# TODO this may get out of sync with config
log_file = "/home/mm/device.log"

def is_instance_running():
    """Checks if another instance of the script is already running."""
    my_pid = os.getpid()
    print("my_pid: %s" % my_pid)
    for proc in psutil.process_iter():
        if proc.cmdline() == ['/home/mm/.ctrlenv/bin/python', '/home/mm/.ctrlenv/bin/mmctrl', '--start'] and proc.pid != my_pid:
            return True
    return False

def start_service():
    """Restarts the service if it is running."""
    if is_instance_running():
        subprocess.run(["/usr/bin/sudo", "/usr/bin/systemctl", "restart", "mmctrl.service"])

def enable_service():
    """Enable and start the service (usually after registration)."""
    subprocess.run(["/usr/bin/sudo", "/usr/bin/systemctl", "enable", "--now", "mmctrl.service"])

def stop_service():
    """Stop the service"""
    subprocess.run(["/usr/bin/sudo", "/usr/bin/systemctl", "stop", "mmctrl.service"])

def get_loglevel(loglevel_arg):
    import logging
    if loglevel_arg == "DEBUG":
        return logging.DEBUG
    elif loglevel_arg == "INFO":
        return logging.INFO
    elif loglevel_arg == "WARN":
        return logging.WARN
    elif loglevel_arg == "ERROR":
        return logging.ERROR

def cli():
    parser = argparse.ArgumentParser(prog='mmctrl',
                    description='The is the MosquitoMax Controller. Use it to calibrate the device, run diagnostics and start the controller',
                    epilog='Contact MosquitoMax with questions')

    parser.add_argument("-s", "--start", action="store_true", help="Start the controller.")
    parser.add_argument("-v", "--version", action="store_true", help="Print version and exit.")
    parser.add_argument("-d", "--diagnostics", action="store_true", help="Run diagnostics.")
    parser.add_argument("-c", "--calibrate", choices=["SCALE", "LINE_IN", "LINE_OUT", "VACUUM", "ALL"], default="ALL", help="Calibrate connected devices.")
    parser.add_argument("-r", "--register", action="store_true", help=argparse.SUPPRESS) # TODO secure this so consumers can't register devices
    parser.add_argument("-n", "--clean", action="store_true", help="Remove WiFi and logs from device.")
    parser.add_argument("--validate", choices=["cloud", "weather"], help="Run various exercises to validate connectivity.")
    parser.add_argument("-u", "--upgrade", action="store_true", help="Upgrade the controller package (considers all whl files in /home/mm)")
    parser.add_argument("-l", "--loglevel", choices=["DEBUG", "INFO", "WARN", "ERROR"], default="DEBUG", help="Set logging level.")

    args = parser.parse_args()

    # Print version and exit
    if args.version:
        print(version('mm_controller'))
        sys.exit(0)
    
    # Calibrate the device
    if args.calibrate:
        try:
            stop_service()
            print("Running calibration...")
            from mm_controller import calibrate_device
            if args.calibrate == "SCALE" or args.calibrate == "ALL":
                calibrate_device.calibrate(scale=True)
            if args.calibrate == "LINE_IN" or args.calibrate == "ALL":
                calibrate_device.calibrate(line_in=True)
            if args.calibrate == "LINE_OUT" or args.calibrate == "ALL":
                calibrate_device.calibrate(line_out=True)
            if args.calibrate == "VACUUM" or args.calibrate == "ALL":
                calibrate_device.calibrate(vacuum=True)
        except KeyboardInterrupt:
            print("Calibration aborted.")
        finally:
            start_service()

    # Clean the device
    if args.clean:
        print("Cleaning device...")
        # from mm_controller import clean_device
        # remove WiFi creds
        # remove or change user password
        # clean_device.clean()
        # start_service()

    # Register the device
    if args.register:
        print("Running registration...")
        stop_service()
        from mm_controller import register_device
        if not register_device.is_registered():
            register_device.register()
            enable_service()
        else:
            print("Device password exists. Skipping...")
            start_service()

    # Run diagnostics
    if args.diagnostics:
        try:
            stop_service()
            print("Running diagnostics...")
            from mm_controller import device_sensors
            device_sensors.rundiagnostics()
            start_service()
        except KeyboardInterrupt:
            start_service()
        
    if args.validate == "cloud":
       pass
    elif args.validate == "weather":
       pass

    # Upgrade the controller package
    if args.upgrade:
        print("Upgrading...")
        print("Current version: %s" % version('mm_controller'))
        print("Looking for upgrades...")
        path = "/home/mm"
        dir_list = os.listdir(path)
        for filename in dir_list:
            match = re.match(r"mm_controller-(.*)-py3-none-any.whl", filename)
            if match:
                version_match = match.group(1)
                if version_match > version('mm_controller'):
                    try:
                        print("Upgrading to %s" % version_match)
                        stop_service()
                        subprocess.run([".ctrlenv/bin/pip", "install", os.path.join(path, filename)])
                        print("Upgrade complete.")
                    except:
                        print("Upgrade failed.")
                    finally:
                        start_service()
                    sys.exit(0)
        print("No upgrades found.")
        sys.exit(0)

    # Start the controller
    if args.start:        
        if not is_instance_running():
            print("Log level: %s" % args.loglevel)
            from mm_controller.utils import my_handler
            my_handler.setLevel(get_loglevel(args.loglevel))
            
            print("Run controller")
            from mm_controller import controller
            controller.run()
        else:
            print("Controller is running. Use /usr/bin/systemctl.")

    # Print help if nothing else happened yet
    parser.print_help()
    parser.exit()

if __name__ == "__main__":
   cli()
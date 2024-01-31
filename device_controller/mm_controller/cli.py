import argparse
import os
import re
import sys
from importlib.metadata import version
import subprocess
from datetime import datetime, timedelta
import psutil

def is_instance_running():
    """Checks if another instance of the script is already running."""
    my_pid = os.getpid()
    print("my_pid: %s" % my_pid)
    for proc in psutil.process_iter():
        if proc.cmdline() == ['/home/mm/.ctrlenv/bin/python', '/home/mm/.ctrlenv/bin/mmctrl', '--start'] and proc.pid != my_pid:
            print("proc.pid: %d == my_pid: %d" % (proc.pid, my_pid))
            return True
    return False

def start_service():
    """Ensure the service is (re)started if it is running."""
    # if is_instance_running():
    status = subprocess.run(["/usr/bin/sudo", "/usr/bin/systemctl", "restart", "mmctrl.service"], capture_output=True)
    print("return code: %d " % status.returncode)
    sys.exit(0)

def enable_service():
    """Enable and start the service (usually after registration)."""
    status = subprocess.run(["/usr/bin/sudo", "/usr/bin/systemctl", "enable", "--now", "mmctrl.service"], capture_output=True)
    print("return code: %d " % status.returncode)

def stop_service():
    """Stop the service"""
    status = subprocess.run(["/usr/bin/sudo", "/usr/bin/systemctl", "stop", "mmctrl.service"], capture_output=True)
    print("return code: %d " % status.returncode)

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
    nohelp = False
    parser = argparse.ArgumentParser(prog='mmctrl',
                    description='The is the MosquitoMax Controller. Use it to calibrate the device, run diagnostics and start the controller',
                    epilog='Contact MosquitoMax with questions')

    parser.add_argument("-s", "--start", action="store_true", help="Start the controller.")
    parser.add_argument("-v", "--version", action="store_true", help="Print version and exit.")
    parser.add_argument("-d", "--diagnostics", action="store_true", help="Run diagnostics.")
    parser.add_argument("-c", "--calibrate", choices=["SCALE", "LINE_IN", "LINE_OUT", "VACUUM", "ALL"], nargs="*", help="Calibrate connected devices.")
    parser.add_argument("-r", "--register", action="store_true", help=argparse.SUPPRESS) # TODO secure this so consumers can't register devices
    parser.add_argument("-n", "--clean", action="store_true", help="Remove WiFi and logs from device.")
    parser.add_argument("--validate", choices=["cloud", "weather"], help="Run various exercises to validate connectivity.")
    parser.add_argument("-u", "--upgrade", action="store_true", help="Upgrade the controller package (considers all whl files in /home/mm)")
    parser.add_argument("-l", "--loglevel", choices=["DEBUG", "INFO", "WARN", "ERROR"], default="DEBUG", help="Set logging level.")

    args = parser.parse_args()

    # Print version and exit
    if args.version:
        nohelp = True
        print(version('mm_controller'))
        parser.exit()
    
    # Calibrate the device
    if args.calibrate:
        nohelp = True
        try:
            stop_service()
            print("Running calibration...")
            from mm_controller import calibrate_device
            if "SCALE" in args.calibrate or "ALL" in args.calibrate:
                print("Calibrating Scale")
                calibrate_device.calibrate(scale=True)
            if "LINE_IN" in args.calibrate or "ALL" in args.calibrate:
                print("Calibrating Line IN")
                calibrate_device.calibrate(line_in=True)
            if "LINE_OUT" in args.calibrate or "ALL" in args.calibrate:
                print("Calibrating Line OUT")
                calibrate_device.calibrate(line_out=True)
            if "VACUUM" in args.calibrate or "ALL" in args.calibrate:
                print("Calibrating Vacuum")
                calibrate_device.calibrate(vacuum=True)
        except KeyboardInterrupt:
            print("Calibration aborted.")
        finally:
            start_service()

    # Clean the device
    if args.clean:
        nohelp = True
        print("Cleaning device...")
        # from mm_controller import clean_device
        # remove WiFi creds
        # remove or change user password
        # clean_device.clean()
        # start_service()

    # Register the device
    if args.register:
        nohelp = True
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
        nohelp = True
        try:
            stop_service()
            print("Running diagnostics...")
            from mm_controller import device_sensors
            device_sensors.rundiagnostics()
            start_service()
        except KeyboardInterrupt:
            start_service()
        
    if args.validate == "cloud":
        nohelp = True
        pass
    elif args.validate == "weather":
        nohelp = True
        pass

    # Upgrade the controller package
    if args.upgrade:
        nohelp = True
        # use Cloud to retrieve newer version, if available
        from mm_controller import cloud
        from mm_controller.utils import app_log
        upgrade_cloud = cloud.Cloud()
        current_version = version('mm_controller')
        print("Current version: %s" % current_version)
        app_log.info("Current version: %s" % current_version)
        latest_version = upgrade_cloud.get_latest_release()
        print("Latest version: %s" % latest_version)
        app_log.info("Latest version: %s" % latest_version)
        if latest_version > current_version:
            upgrade_cloud.download_latest_release()
        # handle upgrade, if present
        print("Looking for upgrades...")
        app_log.info("Looking for upgrades...")
        path = "/home/mm"
        dir_list = os.listdir(path)
        for filename in dir_list:
            match = re.match(r"mm_controller-(.*)-py3-none-any.whl", filename)
            if match:
                version_match = match.group(1)
                if version_match > version('mm_controller'):
                    try:
                        print("Upgrading to %s" % version_match)
                        app_log.info("Upgrading to %s" % version_match)
                        status = subprocess.run(["/home/mm/.ctrlenv/bin/pip", "install", os.path.join(path, filename)], capture_output=True)
                        print(status.stdout)
                        app_log.debug(status.stdout)
                        print("Upgrade complete.")
                        app_log.info("Upgrade complete.")
                    except:
                        print("Upgrade failed.")
                        app_log.error("Upgrade failed.")
                    finally:
                        app_log.info("Restarting service.")
                        start_service()
        print("No upgrades found.")
        app_log.debug("No upgrades found.")
        start_service()
        parser.exit()

    # Start the controller
    if args.start:        
        nohelp = True
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
    if not nohelp:
        parser.print_help()
        parser.exit()

if __name__ == "__main__":
   cli()
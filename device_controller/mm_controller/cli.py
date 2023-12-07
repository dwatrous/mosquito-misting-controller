import argparse
import sys
from importlib.metadata import version
import subprocess

try:
    service_status = subprocess.run(["sudo", "systemctl", "status", "mmctrl.service"], capture_output=True)
except FileNotFoundError:
    service_status = subprocess.run(["sudo", "systemctl", "status", "mmctrl.service"], capture_output=True, shell=True)
service_running = "Active: active (running)" in service_status.stdout.decode("utf-8")

def restart_service_if_running():
    """Restarts the service if it is running."""
    if service_running:
        try:
            subprocess.run(["sudo", "systemctl", "restart", "mmctrl.service"])
        except FileNotFoundError:
            subprocess.run(["sudo", "systemctl", "restart", "mmctrl.service"], shell=True)

def enable_service():
    """Restarts the service if it is running."""
    if service_running:
        try:
            subprocess.run(["sudo", "enable", "--now", "mmctrl.service"])
        except FileNotFoundError:
            subprocess.run(["sudo", "enable", "--now", "mmctrl.service"], shell=True)

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
    print("Service running: %s" % service_running)
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
        if not service_running:
            print("Run controller")
            from mm_controller import controller
            controller.run()
        else:
            print("Controller is running. Use systemctl.")
    sys.exit(0)

if __name__ == "__main__":
   cli()
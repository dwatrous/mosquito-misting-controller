This file explains how to deliver the mm-controller service

## Tools required to deliver mm-controller
The following tools are used to build and deliver the mm_controller service

### Required tools

* git
  * Linux: `sudo apt install git fdisk`
  * Windows: https://git-scm.com/download/win (use gitbash)
* gcloud https://cloud.google.com/sdk/docs/install-sdk
* PDM: https://pdm-project.org/
  * This is used to build the Python release. It packages the files into a wheel.
  * Installation instructions: https://pdm-project.org/latest/#installation
* SDM: https://github.com/gitbls/sdm
  * This is used to create a bootable image for the Raspberry Pi.
  * Install (always Linux): `curl -L https://raw.githubusercontent.com/gitbls/sdm/master/EZsdmInstaller V10.0 | bash`

### Incidental tools

* Raspberry Pi imager (when not using SDM to burn the image)
  * https://www.raspberrypi.com/software/
* Decompress images.
  * Linux: unxz
    * `sudo apt install xz-utils`
  * Windows: https://7-zip.org/
* On Windows: WSL: https://learn.microsoft.com/en-us/windows/wsl/install
  * `wsl -d Debian` to start a new session from Windows Shell
* Windows Terminal: https://github.com/microsoft/terminal
* Google Compute Engine: *If a local laptop/computer isn't available or isn't working properly*, it's possible to create a Virtual Machine in Google Cloud that can be used to build mm-controller.
  * Create Debian host in GCE for the following steps: https://cloud.google.com/compute/docs/instances/create-start-instance.
  * Run `sudo apt update`

## Setup the environment

Start by getting the source code for mm-controller which is kept in https://source.cloud.google.com/FIREBASE_PROJECT/MosquitoMax. This requires git and gcloud (see above requirements). Start by authenticating using gcloud and then clone the repository.
```
gcloud auth login
gcloud source repos clone MosquitoMax
cd ~/MosquitoMax/device_controller
```

Next, get the raspios image. You can download it here: https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2024-03-15/

1. Linux:
    ```
    curl -o 2024-03-15-raspios-bookworm-armhf-lite.img.xz https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2024-03-15/2024-03-15-raspios-bookworm-armhf-lite.img.xz
    unxz -k 2024-03-15-raspios-bookworm-armhf-lite.img.xz
    ```
1. Windows: Use the link above to download and extract with 7-zip (see requirements above).

### Local Configuration File

For local development, you can create a `config.local.yaml` file in the `device_controller` directory. This file allows you to keep your secrets and local configuration in one place. This file is ignored by git.

Here is the format of the `config.local.yaml` file:

```yaml
# Local configuration for mosquito-misting-controller
# This file is intended for local development and should not be checked into version control.

# Values from replacement-map files
firebase:
  project: "PROJECT_ID"
  api_key: "API_KEY"
  service_account: "firebase-adminsdk-blxt8@PROJECT_ID.iam.gserviceaccount.com"

# MM_ environment variables
mm_env:
  wifi_ssid: "YOUR_WIFI_SSID"
  wifi_password: "YOUR_WIFI_PASSWORD"
  hostname: "mmdevice"
  version: "0.1.67" # This should match the version in pyproject.toml
  user_password: "YOUR_USER_PASSWORD"
```

### Setting Environment Variables

To set the required `MM_` environment variables for your shell session, you can use the `set_env.sh` script located in the project root. This script reads the values from `device_controller/config.local.yaml`.

From the project root, run the following command:

```bash
source set_env.sh
```

After running the script, you can verify that the variables are set correctly by running `env | grep MM_`.

## Build the Python wheel

A python wheel provides a way to package an installable python application: https://realpython.com/python-wheels/. The PDM tool is makes it possible to bundle all the mm-controller files into wheel package. These can then be installed using pip: https://realpython.com/what-is-pip/. The files `~/MosquitoMax/pyproject.toml` contains the instructions used by PDM to build the wheel. Build the wheel package as follows:

NOTE: Before running this, make sure the MM_VERSION is correct and all files are updated (see [Version numbers](#version-numbers]))

```
cd ~/MosquitoMax/device_controller
pdm build -v
```

This produces the following two files, where `0.1.0` represents the version number.
```
dist/mm_controller-0.1.0.tgz
dist/mm_controller-0.1.0-py3-none-any.whl
```

### Push to cloud for broader distribution
Using gsutil, this new build can be pushed to the cloud and installed on individual devices. Use this command:

Windows
```
gsutil cp .\dist\mm_controller-$MM_VERSION-py3-none-any.whl gs://mm_controller_releases/
```

Linux
```
gsutil cp dist/mm_controller-$MM_VERSION-py3-none-any.whl gs://mm_controller_releases/
```

## Build the SD card image
### Setup
The file `~/MosquitoMax/device_controller/mmsetup` is a custom plugin for SDM that performs parts of the mm-controller setup (see https://github.com/gitbls/sdm/blob/master/Docs/Plugins.md for more information about plugins). This file must be copied into the SDM plugins directory.

```
cd ~/MosquitoMax/device_controller
sudo cp mmsetup /usr/local/sdm/local-plugins/
sudo chmod +x /usr/local/sdm/local-plugins/mmsetup
```

Verify that you have the first file using `cat` as follows
```
cat /usr/local/sdm/local-plugins/mmsetup
```

### SDM components
SDM copies a few files into the image that are required by mm-controller. These files are listed in `~/MosquitoMax/sdmfilelist`. NOTE: `sdmfilelist` requires an empty line at the end of the file.

### Clean up
The following commands modify the img file directly, which means that each time you run them, you should delete any existing .img files and uncompress the .xz file for a clean image (see [Setup the environment](#setup-the-environment)).

```
cd ~/MosquitoMax/device_controller
rm 2024-03-15-raspios-bookworm-armhf-lite.img
rm mm.img
unxz -k 2024-03-15-raspios-bookworm-armhf-lite.img.xz
```
NOTE: On Windows, 7-zip is much faster than unxz and can to extract the .xz file.

#### Faster clean up on Linux
To make cleanup faster on Linux, you can create a copy of the .img file and use that to avoid decompressing the .xz file. Store the original with this command:

```
cp 2024-03-15-raspios-bookworm-armhf-lite.img 2024-03-15-raspios-bookworm-armhf-lite.img.copy
```

Clean up like this
```
rm 2024-03-15-raspios-bookworm-armhf-lite.img
rm mm.img
cp 2024-03-15-raspios-bookworm-armhf-lite.img.copy 2024-03-15-raspios-bookworm-armhf-lite.img
```

### Build the image
Before you run this, double check that the environment variables are set (see [Setup the environment](#setup-the-environment)))

SDM can now be used to build the SD card image. This will take a few minutes.
```
cd ~/MosquitoMax
sudo sdm --customize \
  --plugin raspiconfig:"i2c=0" \
  --plugin copyfile:"filelist=sdmfilelist" \
  --plugin disables:piwiz \
  --plugin L10n:host \
  --plugin user:"adduser=mm|password=$MM_USERPASSWORD" \
  --plugin user:"deluser=pi" \
  --plugin network:"netman=nm|wifissid='$MM_WIFISSID'|wifipassword='$MM_WIFIPASSWORD'|wificountry=US|noipv6" \
  --plugin apps:"apps=python3-pip,python3-venv,python3-dev" \
  --plugin mmsetup:"version=$MM_VERSION" \
  --extend --xmb 1000 \
  --restart \
  --host $MM_HOSTNAME \
  2024-03-15-raspios-bookworm-armhf-lite.img
```

### Burn the image
The image can be 'burned' to a file and written to an SD card using the Raspberry Pi imager. This method is perferred for Windows, because WSL doesn't have direct access to SD card readers.
```
sudo sdm --burnfile mm.img --expand-root 2024-03-15-raspios-bookworm-armhf-lite.img
```

When using SDM on a Linux host, SDM can burn the image directly to the SD card.
```
sudo sdm --burn /dev/sde --expand-root 2024-03-15-raspios-bookworm-armhf-lite.img
```

OPTIONAL: If you run this on a Google Cloud VM, you will want to compress and copy the image to Google Cloud Storage. This makes it easier to download the image.
```
xz -k mm.img
gsutil cp mm.img.xz gs://sdm-builds
```

## Version numbers
The version number is indicated in three places:
1. pyproject.toml
1. sdmfilelist
1. in the MM_VERSION environment variable (see [Setup the environment](#setup-the-environment))

If you have updated the MM_VERSION environment variable, you can use the following sed command to update both files.
```
sed -i -E "s/[0-9]+\.[0-9]+\.[0-9]+/$MM_VERSION/g" pyproject.toml sdmfilelist
```

## Creating a new release of mm_controller
1. Update the version in required files (see [Version numbers](#version-numbers))
1. Clean up previous builds (see [Clean up](#clean-up))
1. Build a new wheel (see [Build the Python wheel](#build-the-python-wheel))
1. Build a new SD card image (see [Build the SD card image](#build-the-sd-card-image))
1. Use Raspberry Pi imager to write the SD card

## Device details
If needed, various details can be captured directly from the device. 

To find the serial number of the device, this can be run while logged in to the device.

```
cat /sys/firmware/devicetree/base/serial-number
```

The device MAC address can be found with this:

```
cat /sys/class/net/wlan0/address
```
### Check on the service
mm_controller runs as a Linux system service. You can see the current status using this command (which includes some sample output):

```
mm@mmdwatrous:~ $ sudo systemctl status mmctrl.service
● mmctrl.service - MosquitoMax Controller Service
     Loaded: loaded (/etc/systemd/system/mmctrl.service; enabled; preset: enabled)
     Active: active (running) since Sun 2023-12-24 07:16:11 CST; 3 days ago
   Main PID: 5246 (mmctrl)
      Tasks: 11 (limit: 389)
        CPU: 1h 53min 7.489s
     CGroup: /system.slice/mmctrl.service
             └─5246 /home/mm/.ctrlenv/bin/python /home/mm/.ctrlenv/bin/mmctrl --start
```

You can see the logs using this command:

```
sudo journalctl -f -u mmctrl.service
```

The service can be restarted with this command:

```
sudo systemctl restart mmctrl.service
```

### Device log
Device logs are located in `/home/mm` and can be views like this.

```
tail -f device.log
```

Logs rollover each day, with old logs having the date in the filename, like `device.log.2023-12-22`.
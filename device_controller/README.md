This file explains how to deliver the mm-controller service

## Tools required to deliver mm-controller

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

Next, get the raspios image. You can download it here: https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2023-10-10/

1. Linux:
    ```
    curl -o 2023-10-10-raspios-bookworm-armhf-lite.img.xz https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2023-10-10/2023-10-10-raspios-bookworm-armhf-lite.img.xz
    unxz -k 2023-10-10-raspios-bookworm-armhf-lite.img.xz
    ```
1. Windows: Use the link above to download and extract with 7-zip (see requirements above).

Set the 'factory' WiFi credentials as environment variables. The SSID needs to reference a 2.4GHz network.

```
export WIFISSID='SSID'
export WIFIPASSWORD='PASSWORD'
export HOSTNAME='mmdevice'
export VERSION='0.1.0'
```

## Build the Python wheel

A python wheel provides a way to package an installable python application: https://realpython.com/python-wheels/. The PDM tool is makes it possible to bundle all the mm-controller files into wheel package. These can then be installed using pip: https://realpython.com/what-is-pip/. The files `~/MosquitoMax/pyproject.toml` contains the instructions used by PDM to build the wheel. Build the wheel package as follows:

```
cd ~/MosquitoMax/device_controller
pdm build -v
```

This produces the following two files, where `0.1.0` is the version number (see below for more about the version number).
```
dist/mm_controller-0.1.0.tgz
dist/mm_controller-0.1.0-py3-none-any.whl
```

## Build the SD card image
### Setup
The file `~/MosquitoMax/mmsetup` is a custom plugin for SDM that performs parts of the mm-controller setup (see https://github.com/gitbls/sdm/blob/master/Docs/Plugins.md for more information about plugins). This file must be copied into the SDM plugins directory.

```
sudo cp ~/MosquitoMax/mmsetup /usr/local/sdm/local-plugins/
sudo chmod +x /usr/local/sdm/local-plugins/mmsetup
```

### SDM components
SDM copies a few files into the image that are required by mm-controller. These files are listed in `~/MosquitoMax/sdmfilelist`. NOTE: `sdmfilelist` requires an empty line at the end of the file.

### Clean up
The following commands modify the img file directly, which means that each time you run them, you should delete any existing .img files and uncompress the .xz file for a clean image (see [Setup the environment](#setup-the-environment)).

```
cd ~/MosquitoMax/device_controller
rm 2023-10-10-raspios-bookworm-armhf-lite.img
rm mm.img
unxz -k 2023-10-10-raspios-bookworm-armhf-lite.img.xz
```
NOTE: On Windows, 7-zip is much faster than unxz and can to extract the .xz file.

### Build the image
SDM can now be used to build the SD card image. This will take a few minutes.
```
sudo sdm --customize --plugin raspiconfig:"i2c=0" --plugin copyfile:"filelist=sdmfilelist" --plugin disables:piwiz --plugin L10n:host --plugin user:"adduser=mm|password=secret" --plugin user:"deluser=pi" --plugin network:"netman=nm|wifissid='$WIFISSID'|wifipassword='$WIFIPASSWORD'|wificountry=US|noipv6" --plugin apps:"apps=python3-pip,python3-venv,python3-dev" --plugin mmsetup:"version=$VERSION" --extend --xmb 500 --restart --host $HOSTNAME 2023-10-10-raspios-bookworm-armhf-lite.img
```


### Burn the image
The image can be 'burned' to a file and written to an SD card using the Raspberry Pi imager. This method is perferred for Windows, because WSL doesn't have direct access to SD card readers.
```
sudo sdm --burnfile mm.img --expand-root 2023-10-10-raspios-bookworm-armhf-lite.img
```

When using SDM on a Linux host, SDM can burn the image directly to the SD card.
```
sudo sdm --burn /dev/sde --expand-root 2023-10-10-raspios-bookworm-armhf-lite.img
```

OPTIONAL: If you run this on a Google Cloud VM, you will want to compress and copy the image to Google Cloud Storage. This makes it easier to download the image.
```
xz -k mm.img
gsutil cp mm.img.xz gs://sdm-builds
```

OPTIONAL: If you want to copy a new version of the whl file to an existing image, you can use the copyfile plugin.
```
sudo sdm --plugin copyfile:"from=dist/mm_controller-0.1.0-py3-none-any.whldist/mm_controller-0.1.0-py3-none-any.whl|to=/home/mm/controller" 2023-10-10-raspios-bookworm-armhf-lite.img
```

## Version numbers
The version number is indicated in three places:
1. pyproject.toml
1. sdmfilelist
1. in the VERSION environment variable (see [Setup the environment](#setup-the-environment))

If you have updated the VERSION environment variable, you can use the following sed command to update both files.
```
sed -i -E "s/[0-9]+\.[0-9]+\.[0-9]+/$VERSION/g" pyproject.toml sdmfilelist
```

## Creating a new release of mm_controller
1. Update the version in required files (see [Version numbers](#version-numbers))
1. Clean up previous builds (see [Clean up](#clean-up))
1. Build a new wheel (see [Build the Python wheel](#build-the-python-wheel))
1. Build a new SD card image (see [Build the SD card image](#build-the-sd-card-image))
1. Use Raspberry Pi imager to write the SD card
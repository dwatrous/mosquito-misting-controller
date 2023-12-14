# mm-controller

`wsl -d Debian`

```
# Create Debian host in GCE for the following steps
# sudo apt update
# sudo apt install -y git fdisk
# gcloud auth login
# gcloud source repos clone MosquitoMax
# cd MosquitoMax/device_controller

# curl -L https://raw.githubusercontent.com/gitbls/sdm/master/EZsdmInstaller V10.0 | bash

# https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2023-10-10/
# e.g. curl -o 2023-10-10-raspios-bookworm-armhf-lite.img.xz https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2023-10-10/2023-10-10-raspios-bookworm-armhf-lite.img.xz
# unxz -k 2023-10-10-raspios-bookworm-armhf-lite.img.xz
# OR Use 7zip to extract on Windows

sudo cp mmsetup /usr/local/sdm/local-plugins/
sudo chmod +x /usr/local/sdm/local-plugins/mmsetup

# mfg wifi connected
sudo sdm --customize --plugin raspiconfig:"i2c=0" --plugin copyfile:"filelist=sdmfilelist" --plugin disables:piwiz --plugin L10n:host --plugin user:"adduser=mm|password=secret" --plugin user:"deluser=pi" --plugin network:"netman=nm|wifissid='Wishy Washy'|wifipassword='not to late to fate'|wificountry=US|noipv6" --plugin apps:"apps=python3-pip,python3-venv,python3-dev" --plugin mmsetup --extend --xmb 500 --restart --host mmdwatrous 2023-10-10-raspios-bookworm-armhf-lite.img
sudo sdm --burnfile mm.img --expand-root 2023-10-10-raspios-bookworm-armhf-lite.img
# on GCE
# xz -k mm.img
# gsutil cp mm.img.xz gs://sdm-builds

# sudo sdm --plugin copyfile:"from=dist/mm_controller-0.1.0-py3-none-any.whldist/mm_controller-0.1.0-py3-none-any.whl|to=/home/mm/controller" 2023-10-10-raspios-bookworm-armhf-lite.img
```

## Creating a new release of mm_controller
1. Update the version in all of the following places
  1. pyproject.toml
  1. sdmfilelist
  1. mmsetup
1. `pdm build -v`
1. See sdm-commands.txt
1. Use Raspberry Pi imager to write the SD card
# mm-controller
## Creating a new release of mm_controller
1. Update the version in all of the following places
  1. pyproject.toml
  1. sdmfilelist
  1. mmsetup
1. `pdm build -v`
1. See sdm-commands.txt
1. Use Raspberry Pi imager to write the SD card
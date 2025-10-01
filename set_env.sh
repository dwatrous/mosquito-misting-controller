#!/bin/bash

# This script reads from device_controller/config.local.yaml to set environment variables for the factory setup.
# Usage: source set_env.sh

# Function to parse yaml and export variable
export_var() {
    local key=$1
    local env_var=$2
    local value=$(grep "^  $key:" device_controller/config.local.yaml | sed -e "s/.*: *//;s/ *#.*//;s/\"//g")
    if [ -n "$value" ]; then
        export $env_var="$value"
        echo "Exported $env_var"
    fi
}

export_var "wifi_ssid" "MM_WIFISSID"
export_var "wifi_password" "MM_WIFIPASSWORD"
export_var "hostname" "MM_HOSTNAME"
export_var "version" "MM_VERSION"
export_var "user_password" "MM_USERPASSWORD"
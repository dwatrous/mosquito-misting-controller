# Mosquito Misting Controller

This project is a comprehensive system for controlling a mosquito misting device. It consists of three main components: a cloud-based API, a device controller that runs on a Raspberry Pi, and a messaging service for real-time notifications.

## Architecture

The system is designed with a cloud-backend and a hardware controller.

### Cloud Backend

The cloud backend consists of a Flask-based API and a Firebase Cloud Function.

*   **API (`api/`)**: A Python Flask application that exposes a RESTful API for device registration and management. It uses Firebase for authentication and Firestore for data storage. Software updates for the device controller are stored in a Google Cloud Storage bucket and served by the API.

*   **Messaging (`messaging/`)**: A Firebase Cloud Function that listens for messages from the device controller in a Realtime Database. When a message is received, it sends a push notification to the device owner's mobile device using Firebase Cloud Messaging (FCM).

### Device Controller

The device controller (`device_controller/`) is a Python application designed to run on a Raspberry Pi connected to the mosquito misting hardware. [View the wiring diagram here](https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&highlight=0000ff&edit=_blank&layers=1&nav=1&title=mm-controller-wiring.drawio&dark=auto#Uhttps%3A%2F%2Fraw.githubusercontent.com%2Fdwatrous%2Fmosquito-misting-controller%2Fmain%2Fdiagrams%2Fmm-controller-wiring.drawio).

*   **Hardware Interaction**: The controller uses libraries like `gpiozero` and `Adafruit-ADS1x15` to interact with the hardware, including valves, pumps, and sensors.

*   **Command-Line Interface**: The `mmctrl` command-line interface provides a way to manage the device, including:
    *   Starting and stopping the controller service.
    *   Calibrating the device.
    *   Registering the device with the cloud API.
    *   Running diagnostics.
    *   Upgrading the controller software.

*   **Cloud Communication**: The device controller communicates with the cloud API to register itself and to check for and download software updates. It also sends messages to the cloud messaging service to trigger push notifications.

## Getting Started

[See manufacturing flow here](https://viewer.diagrams.net/?tags=%7B%7D&lightbox=1&highlight=0000ff&edit=_blank&layers=1&nav=1&title=manufacturing-timeline.drawio&dark=auto#Uhttps%3A%2F%2Fraw.githubusercontent.com%2Fdwatrous%2Fmosquito-misting-controller%2Fmain%2Fdiagrams%2Fmanufacturing-timeline.drawio)

### Prerequisites

*   A Google Cloud Platform project with Firebase enabled.
*   A Raspberry Pi with the necessary hardware for the mosquito misting controller.

### Installation

#### Cloud Backend

1.  **API**:
    *   Deploy the Flask application in the `api/` directory to a container-based environment like Google Cloud Run.
    *   Set up a Firestore database and configure the authentication in your Firebase project.
    *   Create a Google Cloud Storage bucket for storing device controller releases.

2.  **Messaging**:
    *   Deploy the Firebase Cloud Function in the `messaging/functions/` directory to your Firebase project.

#### Device Controller

1.  **Hardware Setup**:
    *   Connect the necessary hardware (valves, pumps, sensors) to the Raspberry Pi's GPIO pins.

2.  **Software Installation**:
    *   Clone this repository to the Raspberry Pi.
    *   Install the dependencies listed in `device_controller/pyproject.toml` using a package manager like `pdm`.
    *   Install the `mmctrl.service` file to `/etc/systemd/system/` to manage the controller as a systemd service.

## Usage

### `mmctrl` Command-Line Interface

The `mmctrl` command-line interface is the primary way to interact with the device controller.

*   **Start the controller:**
    ```bash
    mmctrl --start
    ```

*   **Stop the controller:**
    ```bash
    sudo systemctl stop mmctrl.service
    ```

*   **Restart the controller:**
    ```bash
    mmctrl --restart
    ```

*   **Calibrate the device:**
    ```bash
    mmctrl --calibrate [SCALE|LINE_IN|LINE_OUT|VACUUM|ALL]
    ```

*   **Register the device:**
    ```bash
    mmctrl --register
    ```

*   **Run diagnostics:**
    ```bash
    mmctrl --diagnostics
    ```

*   **Upgrade the controller:**
    ```bash
    mmctrl --upgrade
    ```

### API Endpoints

The following are the main endpoints exposed by the cloud API:

*   `POST /api/v1/device/register`: Register a new device.
*   `GET /api/v1/latest_release`: Get the latest software release version for the device controller.
*   `GET /api/v1/latest_release/download`: Download the latest software release for the device controller.

## Diagrams

The `diagrams/` directory contains diagrams that illustrate the system's design and wiring.

*   `manufacturing-timeline.drawio`: A timeline of the manufacturing process.
*   `mm-controller-wiring.drawio`: A wiring diagram for the device controller.
*   `MosquitoMax-smart-design.drawio`: A high-level design of the smart mosquito misting system.

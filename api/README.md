# MosquitoMax API

This is the backend API for the MosquitoMax mosquito misting system. It is a Flask application that provides endpoints for device registration, password reset, and software updates.

## Prerequisites

Before you begin, you will need:

*   A Google Cloud Platform project with Firebase enabled.
*   The `gcloud` command-line tool installed and configured.
*   Docker installed on your local machine.

## Building and Testing

To build and test the API locally, you can use the provided Dockerfile. The comments at the top of `mm_api.py` provide instructions for building and running the Docker container.

1.  **Build the Docker image:**

    ```bash
    docker build -t mmapi .
    ```

2.  **Run the Docker container:**

    ```bash
    docker run -p 8080:8080 -v <path_to_creds>:/creds mmapi
    ```

    Replace `<path_to_creds>` with the path to your Firebase service account credentials file.

3.  **Test the API:**

    You can use `curl` to test the API endpoints. The comments in `mm_api.py` provide example `curl` commands for each endpoint.

## Deployment

The API is designed to be deployed to Google Cloud Run using Google Cloud Build. The `cloudbuild.yaml` file defines the build and deployment steps.

1.  **Submit the build:**

    To deploy the API, submit a build to Google Cloud Build with the following command. Make sure to replace `<your-service-account-email>` with the email address of the service account you want to use for the Cloud Run service.

    ```bash
    gcloud builds submit --config cloudbuild.yaml --substitutions=_SERVICE_ACCOUNT=<your-service-account-email>
    ```

    This command will build the Docker image, push it to the Google Container Registry, and deploy it to Google Cloud Run. The `cloudbuild.yaml` is configured to use the `$PROJECT_ID` environment variable for the Firebase project ID, so you do not need to set it manually.

## API Endpoints

The following are the main endpoints exposed by the API:

*   `POST /api/v1/device/register`: Register a new device.
*   `POST /api/v1/device/reset_password`: Reset the password for a device.
*   `GET /api/v1/latest_release`: Get the latest software release version for the device controller.
*   `GET /api/v1/latest_release/download`: Download the latest software release for the device controller.

## Testing the Deployed API

The API has been deployed to the following URL:

`https://mm-api-747800457578.us-central1.run.app`

You can test the endpoints using `curl`. Note that some endpoints require an authentication token.

*   **Register a new device:**
    ```bash
    curl -X POST -H 'Content-Type: application/json' -d '{"device_email": "your_device_email@mosquitomax.com", "serial_number": "your_serial_number", "mac_address": "your_mac_address"}' https://mm-api-747800457578.us-central1.run.app/api/v1/device/register
    ```
    (Replace with actual values)

*   **Reset a device password:**
    ```bash
    curl -X POST -H 'Content-Type: application/json' -d '{"device_email": "your_device_email@mosquitomax.com"}' https://mm-api-747800457578.us-central1.run.app/api/v1/device/reset_password
    ```
    (Replace with an actual device email)

*   **Get the latest release version:**
    ```bash
    curl -H 'X-ID-Token: <your-auth-token>' https://mm-api-747800457578.us-central1.run.app/api/v1/latest_release
    ```
    (Replace `<your-auth-token>` with a valid Firebase ID token)

*   **Download the latest release:**
    ```bash
    curl -o latest_release.whl -H 'X-ID-Token: <your-auth-token>' https://mm-api-747800457578.us-central1.run.app/api/v1/latest_release/download
    ```
    (Replace `<your-auth-token>` with a valid Firebase ID token)
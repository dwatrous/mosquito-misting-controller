# docker build -t mmapi .
# docker run -p 8080:8080 -v C:\Users\Daniel\Documents\mosquito-controller\MosquitoMax\api\creds:/creds mmapi
# gcloud builds submit --config cloudbuild.yaml
from functools import wraps
from flask import Flask, request
import firebase_admin
from firebase_admin import auth, firestore, credentials
import secrets
import re
import requests
import json
import random
from google.cloud import storage
from google.auth import default

#Initialize Firestore
firebase_admin.initialize_app()

# api key
apikey = "FIREBASE_API_KEY_PLACEHOLDER"

release_bucket_name = "mm_controller_releases"

# Get a reference to the collection
db = firestore.client()
device_collection = db.collection("devices")
accounts_collection = db.collection("accounts")

app = Flask(__name__)

def get_latest_release():
    storage_client = storage.Client()
    bucket = storage_client.bucket(release_bucket_name)

    latest_release_url = None
    latest_version = None

    for blob in bucket.list_blobs():
        match = re.match(r"mm_controller-(.*)-py3-none-any.whl", blob.name)
        if match:
            version = match.group(1)
            if latest_version is None or version > latest_version:
                latest_version = version
                latest_release_url = f"gs://{release_bucket_name}/{blob.name}"

    return {"version": latest_version, "bucket": release_bucket_name, "object": blob.name, "url": latest_release_url}

# function to validate serial number for RPi
def validate_rpi_serial_number(number):
    regex = "^[a-z0-9]{16}$"
    if re.match(regex, number):
        return True
    else:
        return False

# register a new device in the factory
# TEST: curl -X POST -H 'Content-Type: application/json' -d '{"device_email": "000000003d1d1c36@mosquitomax.com", "serial_number": "000000003d1d1c36", "mac_address": "00:00:5e:00:53:af"}' http://127.0.0.1:8080/api/v1/device/register
@app.post("/api/v1/device/register")
def device_register():
    # TODO consider adding a key validation step to prevent unauthorized device registrations
    # TODO add error handling around this rather optimistic getting of JSON (expecting {"serial_no": "", "mac_address": ""})
    device_info = request.get_json()
    # validate that the what was received looks like a RPi serial number
    if not validate_rpi_serial_number(device_info["serial_number"]):
        return "Invalid serial number", 400
    # check for existing device registration
    device_ref = device_collection.document(device_info["device_email"])
    device = device_ref.get()
    # Check if the document exists
    if device.exists:
        # Get the data from the document
        return "Device record already exists", 409
    # generate a new password for this device
    password = secrets.token_hex(random.randint(32,43))
    # create a new user
    try:
        device_user = auth.create_user(email=device_info["device_email"], password=password)
    except auth.EmailAlreadyExistsError:
        return "Auth account already exists", 409
    except ValueError:
        return "Provided values are invalid", 400
    # create device record in Firestore
    device_info["uid"] = device_user.uid
    device_collection.document(device_info["device_email"]).set(device_info)
    # resopnd with device configuration file (including JSON auth response)
    device_config = {"device_password": password}
    return device_config

def authenticate(function):

    @wraps(function)
    def wrapper(*args, **kwargs):
        token_header_name = "X-ID-Token"
        token_header_value = request.headers.get(token_header_name)
        try:
            device_token_values = auth.verify_id_token(token_header_value)
        except auth.ExpiredIdTokenError:
            # TODO consider refreshing the token and returning with the response if successful
            return "Expired ID Token", 403
        except:
            return "Unauthorized", 403
        kwargs["device_email"] = device_token_values["email"]
        return function(*args, **kwargs)

    return wrapper

# get the latest release available for controller devices
# TEST: curl -H 'X-ID-Token: eyJhbGciOiJSUzI1NiIsImtpZCI6IjYzODBlZjEyZjk1ZjkxNmNhZDdhNGNlMzg4ZDJjMmMzYzIzMDJmZGUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vbW9zcXVpdG9tYXgtMzY0MDEyIiwiYXVkIjoibW9zcXVpdG9tYXgtMzY0MDEyIiwiYXV0aF90aW1lIjoxNjkyNTAzOTI1LCJ1c2VyX2lkIjoidld6M0hJTUtXUU5iaEdxQk1hTUNVbDRaZGV2MSIsInN1YiI6InZXejNISU1LV1FOYmhHcUJNYU1DVWw0WmRldjEiLCJpYXQiOjE2OTI2MTk3MjMsImV4cCI6MTY5MjYyMzMyMywiZW1haWwiOiJkZXZpY2VfaWRkQG1vc3F1aXRvbWF4LmNvbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJlbWFpbCI6WyJkZXZpY2VfaWRkQG1vc3F1aXRvbWF4LmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6InBhc3N3b3JkIn19.Rrbz41ECUgJWjLIi2Snmwysm9l0N-LXTspi4xtmpYrq_TyoK6Ag2UskfutY6NT6sYo6zrWL2xb9ayMII1mUIRBf1n1u144n3XTjYEibFbAGlcmG8xWpl2EkThJHUbZA09XAOLaD9zmkkpMLm_NG2qK-r7Yn3FCzuyE4FWSimX0JM-k47UAUESSWo13GV0vtbqEffJHwCZcv0hLnPErXnLzzlTItONj5KmcggnSaEVvU3Q6hto9HL9ExTapIh6tR9v1X1dKQShSfeVcxZuIobObcFT2fXp3RvVkxSqtCGRbN_yuFKSauZ_W8UMXeNrWnWxvMg1bHNlZh378t4rhnoKg' http://127.0.0.1:8080/api/v1/latest_release
@app.get("/api/v1/latest_release")
@authenticate
def latest_release(device_email):
    # get latest release
    latest_release = get_latest_release()
    return {"version": latest_release["version"]}

# credentials, project_id = default()
# storage_client = storage.Client(credentials=credentials, project=project_id)

# download the latest release available for controller devices
# TEST: curl -H 'X-ID-Token: eyJhbGciOiJSUzI1NiIsImtpZCI6IjYzODBlZjEyZjk1ZjkxNmNhZDdhNGNlMzg4ZDJjMmMzYzIzMDJmZGUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vbW9zcXVpdG9tYXgtMzY0MDEyIiwiYXVkIjoibW9zcXVpdG9tYXgtMzY0MDEyIiwiYXV0aF90aW1lIjoxNjkyNTAzOTI1LCJ1c2VyX2lkIjoidld6M0hJTUtXUU5iaEdxQk1hTUNVbDRaZGV2MSIsInN1YiI6InZXejNISU1LV1FOYmhHcUJNYU1DVWw0WmRldjEiLCJpYXQiOjE2OTI2MTk3MjMsImV4cCI6MTY5MjYyMzMyMywiZW1haWwiOiJkZXZpY2VfaWRkQG1vc3F1aXRvbWF4LmNvbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJlbWFpbCI6WyJkZXZpY2VfaWRkQG1vc3F1aXRvbWF4LmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6InBhc3N3b3JkIn19.Rrbz41ECUgJWjLIi2Snmwysm9l0N-LXTspi4xtmpYrq_TyoK6Ag2UskfutY6NT6sYo6zrWL2xb9ayMII1mUIRBf1n1u144n3XTjYEibFbAGlcmG8xWpl2EkThJHUbZA09XAOLaD9zmkkpMLm_NG2qK-r7Yn3FCzuyE4FWSimX0JM-k47UAUESSWo13GV0vtbqEffJHwCZcv0hLnPErXnLzzlTItONj5KmcggnSaEVvU3Q6hto9HL9ExTapIh6tR9v1X1dKQShSfeVcxZuIobObcFT2fXp3RvVkxSqtCGRbN_yuFKSauZ_W8UMXeNrWnWxvMg1bHNlZh378t4rhnoKg' http://127.0.0.1:8080/api/v1/latest_release/download
@app.get("/api/v1/latest_release/download")
@authenticate
def latest_release_download(device_email):
    # download latest release
    latest_release = get_latest_release()
    storage_client = storage.Client()
    bucket = storage_client.bucket(latest_release["bucket"])
    blob = bucket.blob(latest_release["object"])
    content = blob.download_as_bytes()
    return content

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
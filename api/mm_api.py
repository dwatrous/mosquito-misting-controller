# ┌────────────────┐               ┌─────────────┐               ┌───────────────────┐
# │                │               │             │               │                   │
# │  Smart Device  │               │   Backend   │               │   Firebase Auth   │
# │                │               │             │               │                   │
# └────────────────┘               └─────────────┘               └───────────────────┘


#             username/password              /v1/accounts:signInWithPassword
#          ─────────────────────────►          ─────────────────────────────►

#                                                                 ┌──────────────────┐
#          ◄──────────────────────────        ◄────────────────── │ ID/Refresh token │
#                                                                 └──────────────────┘
#            request action/resource
#              (ID Token)                       auth.verify_id_token
#          ──────────────────────────►        ──────────────────────────────►

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

#Initialize Firestore
try:
    cred = credentials.Certificate("/creds/credfile.json")
except:
    # this case is for local development
    import os
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'creds/credfile.json')
    cred = credentials.Certificate(filename)
firebase_admin.initialize_app(cred)

# api key
apikey = "FIREBASE_API_KEY_PLACEHOLDER"

# Get a reference to the collection
db = firestore.client()
device_collection = db.collection("devices")
accounts_collection = db.collection("accounts")

app = Flask(__name__)

# get email equivalent of device ID
def device_id_as_email(device_id):
    return device_id+"@mosquitomax.com"

# function to validate serial number for RPi
def validate_rpi_serial_number(number):
    regex = "^[a-z0-9]{16}$"
    if re.match(regex, number):
        return True
    else:
        return False

# register a new device
# TEST: curl -X POST -H 'Content-Type: application/json' -d '{"serial_number": "000000003d1d1c36", "mac_address": "00:00:5e:00:53:af"}' http://127.0.0.1:8080/api/v1/device/register
@app.post("/api/v1/device/register")
def device_register():
    # TODO consider adding a key validation step to prevent unauthorized device registrations
    # TODO add error handling around this rather optimistic getting of JSON (expecting {"serial_no": "", "mac_address": ""})
    device_info = request.get_json()
    # validate that the what was received looks like a RPi serial number
    if not validate_rpi_serial_number(device_info["serial_number"]):
        return "Invalid serial number", 400
    # assume email device_id@mosquitomax.com
    username = device_id_as_email(device_info["serial_number"])
    # check for existing device registration
    device_ref = device_collection.document(username)
    device = device_ref.get()
    # Check if the document exists
    if device.exists:
        # Get the data from the document
        return "Device record already exists", 409
    # generate a new password for this device
    password = secrets.token_hex(30)
    # create a new user
    try:
        device_user = auth.create_user(email=username, password=password)
    except auth.EmailAlreadyExistsError:
        return "Auth account already exists", 409
    except ValueError:
        return "Provided values are invalid", 400
    # create device record in Firestore
    device_collection.document(username).set(device_info)
    # resopnd with device configuration file (including JSON auth response)
    device_config = {"username": username, "password": password}
    return device_config

# Authenticate a new device
# TEST: curl -X POST -H 'Content-Type: application/json' -d '{"password": "bc3a236a8d5d73aca0ff36aab8f1a3b8f623e1035689653505dd9f33c970", "username": "device_idd@mosquitomax.com"}' http://127.0.0.1:8080/api/v1/device/auth
@app.post("/api/v1/device/auth")
def device_auth():
    # get credentials in request
    device_creds = request.get_json()
    # sign in with provided username and password
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key="+apikey

    headers = {"Content-Type": "application/json"}

    data = {
        "email": device_creds["username"],
        "password": device_creds["password"],
        "returnSecureToken": True
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    # verify that username matches
    if response.status_code == 200:
        return response.content
    else:
        return "Something went wrong. Auth failed", 400

# Refresh an ID token
# TEST: curl -X POST -H 'Content-Type: application/json' -d '{"refresh_token": "AMf-vBwyo_hTtL2Gy5VfVGp-bsefl9X-lRUr5ThndhtINsu8NSqVjYLW__BwJbtlARADcrmhS5KCwuao_iEObPYeO2mOjMel_eKxxbK3CrLlYUKrRL0T1KjQn13XrJRxXvs5JzIxW7-SOQk5fXkLpj7ZYeKk3Y6ZORgbJb-_z4SHRgVfXFKD1JnL8vxM5vruZAjcUMeeho1jd8Ald_meu2JyTS5ItMz2RNyn436y0tjZ7PYKR1V6mz4"}' http://127.0.0.1:8080/api/v1/device/auth/refresh
@app.post("/api/v1/device/auth/refresh")
def device_auth_refresh():
    # get credentials in request
    refresh_token = request.get_json()
    # sign in with provided username and password
    url = "https://securetoken.googleapis.com/v1/token?key="+apikey

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = "grant_type=refresh_token&refresh_token="+refresh_token["refresh_token"]

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        return response.content
    else:
        return "Something went wrong. Auth refresh failed", 400

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

# get details about a device
# TEST: curl -H 'X-ID-Token: eyJhbGciOiJSUzI1NiIsImtpZCI6IjYzODBlZjEyZjk1ZjkxNmNhZDdhNGNlMzg4ZDJjMmMzYzIzMDJmZGUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vbW9zcXVpdG9tYXgtMzY0MDEyIiwiYXVkIjoibW9zcXVpdG9tYXgtMzY0MDEyIiwiYXV0aF90aW1lIjoxNjkyNTAzOTI1LCJ1c2VyX2lkIjoidld6M0hJTUtXUU5iaEdxQk1hTUNVbDRaZGV2MSIsInN1YiI6InZXejNISU1LV1FOYmhHcUJNYU1DVWw0WmRldjEiLCJpYXQiOjE2OTI2MTk3MjMsImV4cCI6MTY5MjYyMzMyMywiZW1haWwiOiJkZXZpY2VfaWRkQG1vc3F1aXRvbWF4LmNvbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJlbWFpbCI6WyJkZXZpY2VfaWRkQG1vc3F1aXRvbWF4LmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6InBhc3N3b3JkIn19.Rrbz41ECUgJWjLIi2Snmwysm9l0N-LXTspi4xtmpYrq_TyoK6Ag2UskfutY6NT6sYo6zrWL2xb9ayMII1mUIRBf1n1u144n3XTjYEibFbAGlcmG8xWpl2EkThJHUbZA09XAOLaD9zmkkpMLm_NG2qK-r7Yn3FCzuyE4FWSimX0JM-k47UAUESSWo13GV0vtbqEffJHwCZcv0hLnPErXnLzzlTItONj5KmcggnSaEVvU3Q6hto9HL9ExTapIh6tR9v1X1dKQShSfeVcxZuIobObcFT2fXp3RvVkxSqtCGRbN_yuFKSauZ_W8UMXeNrWnWxvMg1bHNlZh378t4rhnoKg' http://127.0.0.1:8080/api/v1/device
@app.get("/api/v1/device")
@authenticate
def device_details(device_email):
    # check for device
    device_ref = device_collection.document(device_email)
    device = device_ref.get()
    # Check if the document exists
    if device.exists:
        # Get the data from the document
        device = device.to_dict()
    else:
        # TODO return 404 Device not found
        return "No such device", 404
    return device

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
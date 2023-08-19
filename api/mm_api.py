# docker build -t mmapi .
# docker run -p 8080:8080 -v C:\Users\Daniel\Documents\mosquito-controller\MosquitoMax\api\creds:/creds mmapi
# gcloud builds submit --config cloudbuild.yaml
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
    import os
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'creds/credfile.json')
    cred = credentials.Certificate(filename)
firebase_admin.initialize_app(cred)

# Get a reference to the collection
db = firestore.client()
device_collection = db.collection("devices")
accounts_collection = db.collection("accounts")

app = Flask(__name__)

# function to validate serial number for RPi
def validate_rpi_serial_number(number):
    regex = "^[a-z0-9]{16}$"
    if re.match(regex, number):
        return True
    else:
        return False

# register a new device
# TEST: curl -X POST -H 'Content-Type: application/json' -d '{"serial_number": "000000003d1d1c36", "mac_address": "00:00:5e:00:53:af"}' http://127.0.0.1:5000/api/v1/device/device_idd/register
@app.post("/api/v1/device/<device_id>/register")
def device_register(device_id):
    # TODO consider adding a key validation step to prevent unauthorized device registrations
    # TODO add error handling around this rather optimistic getting of JSON (expecting {"serial_no": "", "mac_address": ""})
    device_info = request.get_json()
    # validate that the what was received looks like a RPi serial number
    if not validate_rpi_serial_number(device_info["serial_number"]):
        return "Invalid serial number", 400
    # assume email device_id@mosquitomax.com
    username = device_id+"@mosquitomax.com"
    # check for existing device registration
    device_ref = device_collection.document(device_id)
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
    device_collection.document(device_id).set(device_info)
    # resopnd with device configuration file (including JSON auth response)
    device_config = {"username": username, "password": password, }
    return device_config

# get details about a device
@app.get("/api/v1/device/<device_id>")
def device_details(device_id):
    # check for device
    device_ref = device_collection.document(device_id)
    device = device_ref.get()
    # Check if the document exists
    if device.exists:
        # Get the data from the document
        device = device.to_dict()
    else:
        # TODO return 404 Device not found
        return "No such device", 404
    return device

# Auth a new device
# TEST: curl -X POST -H 'Content-Type: application/json' -d '{"password": "bc3a236a8d5d73aca0ff36aab8f1a3b8f623e1035689653505dd9f33c970", "username": "device_idd@mosquitomax.com"}' http://127.0.0.1:5000/api/v1/device/device_idd/auth
@app.post("/api/v1/device/<device_id>/auth")
def device_auth(device_id):
    # get credentials in request
    device_creds = request.get_json()
    # sign in with provided username and password
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=FIREBASE_API_KEY_PLACEHOLDER"

    headers = {"Content-Type": "application/json"}

    data = {
        "email": device_creds["username"],
        "password": device_creds["password"],
        "returnSecureToken": True
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.content
    else:
        return "Something went wrong. Auth failed", 400

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
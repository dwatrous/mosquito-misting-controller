# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

import datetime
from typing import Any
from firebase_functions import db_fn
from firebase_admin import initialize_app, messaging, db, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Initialize Firebase app (replace with your project credentials)
msgapp = initialize_app()

# Function to send FCM message
def send_fcm_message(sender, recipient, message):
    ds = firestore.client()
    print("Processing sender: %s, recipient: %s" % (sender, recipient))
    print("Message: ", message)
    # should only be one for sender UID
    devices = ds.collection("devices").where(filter=FieldFilter("uid", "==", sender)).get()
    token = None
    if len(devices) != 1:
        print("No device found for sender: " + sender)
        print("Devices length: %d" % len(devices))
        return False
    for device in devices:
        device_details = device.to_dict()
        print("Device: ", device_details)
        if recipient != device_details["owner"]:
            print("recipient: %s != owner: %s" % (recipient, device_details["owner"]))
        tokens = ds.collection('Users').document(device_details["owner"]).collection("fcm_tokens").order_by("created_at", direction=firestore.Query.DESCENDING).limit(1).get()
        if len(tokens) <= 0:
            print("No FCM tokens found for owner %s" % device_details["owner"])
            return False
        for token in tokens:
            token_details = token.to_dict()
            print("Token: ", token_details)

            notification = messaging.Notification(title=message["event"], body=message["info"], image="https://storage.googleapis.com/flutterflow-io-6f20.appspot.com/projects/mosquito-max-vuftce/assets/sfm7sqxp5hor/mm-app-icon.png")
            msg = messaging.Message(
                notification=notification,
                token=token_details["fcm_token"]
            )
            messaging.send(msg)
            print("Sent message")
            return True

@db_fn.on_value_created(reference="/messages/{messageid}")
def message_to_notification(event: db_fn.Event[Any]) -> None:
    message_sent = send_fcm_message(event.data["sender"], event.data["recipient"], event.data["message"])
    # clean up messages
    if message_sent:
        db.reference("/processed").child(datetime.date.today().strftime('%Y-%m-%d')).push(event.data)
        msg = db.reference(event.reference).delete()

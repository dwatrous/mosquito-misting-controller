# Import Firebase REST API 
import atexit
import json
import threading
from time import sleep
import firebase
from utils import Config, app_log
import datetime
from aiosseclient import aiosseclient
import asyncio

class Cloud(object):
    # get Config
    config = Config()
    authenticated_device_account = None
    device_details = None
    device_details_reload = False
    message_processor = None

    # Firebase app https://github.com/AsifArmanRahman/firebase-rest-api/tree/main
    app = None
    # Firebase Auth https://github.com/AsifArmanRahman/firebase-rest-api/blob/main/docs/guide/authentication.rst
    auth = None
    # Firestore https://github.com/AsifArmanRahman/firebase-rest-api/blob/main/docs/guide/firestore.rst
    ds = None
    # Realtime database https://github.com/AsifArmanRahman/firebase-rest-api/blob/main/docs/guide/database.rst
    db = None

    # reload = False

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Cloud, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        # Instantiates a Firebase 
        self.app = firebase.initialize_app(self.config.get_config()["firebase"])
        # Firebase Auth
        self.auth = self.app.auth()
        # Firestore
        self.ds = self.app.firestore()
        # Realtime database
        self.db = self.app.database()

    # Authentication
    def get_authenticated_device_account(self):
        # handle initial authentication
        if self.authenticated_device_account == None:
            app_log.info("Perform initial device authentication")
            device = self.auth.sign_in_with_email_and_password(self.config.device_email, self.config.device_password)
            self.authenticated_device_account = {
                "uid": device["localId"],
                "serial_number": device["displayName"],
                "serial_number_as_email": device["email"],
                "idToken": device["idToken"],
                "refreshToken": device["refreshToken"],
                "expiresAt": device["expiresAt"]
            }
        # handle refresh
        if datetime.datetime.now() > datetime.datetime.fromtimestamp(self.authenticated_device_account["expiresAt"]):
            app_log.info("Refreshing authentication at %s" % datetime.datetime.now())
            device = self.auth.refresh(self.authenticated_device_account['refreshToken'])
            self.authenticated_device_account["idToken"] = device["idToken"]
            self.authenticated_device_account["expiresAt"] = device["expiresAt"]
        # finally, return authenticated_device_account, which may just be the cached values
        return self.authenticated_device_account
        # TODO handle error case

    @property
    def idtoken(self):
        return self.get_authenticated_device_account()["idToken"]
    
    # Firestore
    def device_get(self):
        # handle initial authentication
        if self.device_details == None or self.device_details_reload:
            self.device_details = self.ds.collection(u'devices').document(self.config.device_email).get(token=self.idtoken)
        return self.device_details

    def device_update(self, device):
        return self.ds.collection(u'devices').document(self.config.device_email).update(device, token=self.idtoken)

    def write_spray_occurence_ds(self, spraydata):
        # TODO this is probably too optimistic, add error handling
        self.ds.collection(u'devices').document(self.config.device_email).collection(u'sprayoccurrences').add(spraydata, token=self.idtoken)

    # Firebase realtime database (used for messaging)
    def _build_message(self, event, info, action):
        msg = {
            "sender": self.get_authenticated_device_account()["uid"],
            "recipient": self.device_get()["owner"],
            "message": {
                "event": event,
                "info": info
            },
            "time": datetime.datetime.now().strftime("%m-%d-%Y, %H:%M:%S")
        }
        return msg

    def send_message(self, event, info="", action=None):
        message = self._build_message(event, info, action)
        self.db.child("messages").push(message, token=self.idtoken)
        app_log.info("Sent message with event: %s" % event)

    def listen_for_messages_url(self):
        url = self.config.get_config()["firebase"]["databaseURL"] + "/messages.json?auth=" + self.idtoken
        return url
    
    def listen_for_messages(self, callback):
        self.message_processor = callback
        message_reader_thread = threading.Thread(target=asyncio.run, args=(self.message_reader(),))
        message_reader_thread.start()

        def listener_manager(self, message_reader_thread):    
            while True:
                if message_reader_thread.is_alive():
                    app_log.debug("Still reading messages")
                    sleep(30)
                else:
                    message_reader_thread.join()
                    message_reader_thread = threading.Thread(target=asyncio.run, args=(self.message_reader(),))
                    message_reader_thread.start()

        message_auth_manager = threading.Thread(target=listener_manager, args=(self, message_reader_thread,))
        message_auth_manager.start()
        return
    
    async def message_reader(self):
        async for event in aiosseclient(self.listen_for_messages_url()):
            if event.event == "auth_revoked":   # event.data == "credential is no longer valid"
                app_log.info("Encountered %s. restart listening" % event.event)
            elif event.event == "stream_failed":
                app_log.info("Encountered %s: %s" % (event.event, event.data))
            elif event.event == "keep-alive":
                app_log.debug("Received %s" % event.event)
            else:
                self.message_capture(event.data)

    # def listen_for_messages_refresh(self):
    #     try:
    #         self.my_stream.close()
    #     except Exception as err:
    #         app_log.error("Failed to close stream with error: %s" % err)
    #     self.my_stream = self.db.child("messages").stream(self.message_capture, token=self.idtoken)
    #     app_log.info("Refreshed messages stream")        

    def archive_message(self, key, message):
        self.db.child("processed").push(message, token=self.idtoken)
        self.db.child("messages").child(key).remove(token=self.idtoken)
        app_log.info("Message %s move to processed" % key)

    def message_capture(self, message):
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except:
                pass

        # ignore strings that aren't JSON documents
        if isinstance(message["data"], str):
            app_log.debug("'data' is a str: %s", message)

        # identify empty message and ignore
        elif message["data"] == None:
            app_log.debug("Empty message: %s", message)
        
        # identify single message and evaluate
        elif "message" in message["data"].keys():
            # if message intended for this device, process
            if message["data"]["recipient"] == self.device_get()["uid"]:
                if self.message_processor(message["data"]):
                    self.archive_message(message["path"][1:], message["data"])
            else:
                app_log.debug("Message intended for %s", message["data"]["recipient"])
        
        # identify multiple messages and evaluate
        else:
            for key in message["data"].keys():
                # if message intended for this device, process
                if message["data"][key]["recipient"] == self.device_get()["uid"]:
                    if self.message_processor(message["data"][key]):
                        self.archive_message(key, message["data"][key])
                else:
                    app_log.debug("Message intended for %s", message["data"][key]["recipient"])

if __name__ == '__main__':
    cloud = Cloud()
    print(cloud.get_authenticated_device_account())
    spraydata = {"spraydetails": "lots of data here"}
    cloud.write_spray_occurence_ds(spraydata)
    mydevice = cloud.device_get()
    print(mydevice)

    # test messages
    def message_processor(message):
        app_log.info("Received message: %s", message)
        # TODO do something with the message
        return True

    cloud.listen_for_messages(message_processor)
    cloud.send_message("SPRAY_NOTIFICATION", "Spray started 1")
    cloud.send_message("SPRAY_NOTIFICATION", "Spray started 2")
    x = input("Press any key when messaging done")
    print(x)
# Import Firebase REST API 
import json
import os
from string import Template
import threading
from time import sleep
import firebase
import datetime
# from aiosseclient import aiosseclient
import asyncio
from aiohttp_sse_client2 import client as sse_client
import requests
import urllib.request
import traceback
# import logging
# sse_client._LOGGER.setLevel(logging.INFO)

from mm_controller.utils import Config, app_log
from mm_controller.constants import mm_api_host, mm_api_latest_release, mm_api_latest_release_download

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
        try:
            # TODO errors here cause the entire app to stop responding
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
            # return authenticated_device_account, which may just be the cached values
            return self.authenticated_device_account
        # TODO handle error case
        except:
            app_log.error("Error: %s" % traceback.format_exc())

    @property
    def idtoken(self):
        return self.get_authenticated_device_account()["idToken"]
    
    # mm_api
    def get_latest_release(self):
        headers = {"X-ID-Token": self.idtoken, "Content-Type": "application/json"}
        try:
            latest_release = requests.get(mm_api_host + mm_api_latest_release, headers=headers)
            version = latest_release.json()
        except:
            app_log.error("Call to %s failed" % mm_api_host + mm_api_latest_release)
            app_log.error(latest_release.content)
        return version["version"]

    def download_latest_release(self, path=None):
        filename = Template(r"mm_controller-$version-py3-none-any.whl")
        version = self.get_latest_release()
        if path != None:
            filepath = os.path.join(path, filename.substitute(version=version))
        else:
            filepath = filename.substitute(version=version)
        if not os.path.exists(filepath):
            opener = urllib.request.build_opener()
            opener.addheaders = [("X-ID-Token", self.idtoken)]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(mm_api_host + mm_api_latest_release_download, filepath)

    # Firestore
    def device_get(self):
        # handle initial authentication
        if self.device_details == None or self.device_details_reload:
            self.device_details = self.ds.collection(u'devices').document(self.config.device_email).get(token=self.idtoken)
            self.device_details_reload = False
        return self.device_details

    def device_update(self, device):
        try:
            self.ds.collection(u'devices').document(self.config.device_email).update(device, token=self.idtoken)
        except Exception as err:
            app_log.error("device update failed with: %s" % err)

    def write_spray_occurence_ds(self, spraydata):
        try:
            self.ds.collection(u'devices').document(self.config.device_email).collection(u'sprayoccurrences').add(spraydata, token=self.idtoken)
        except Exception as err:
            app_log.error("telemtry write failed with: %s" % err)

    # Firebase realtime database (used for messaging)
    # TODO this fails when the device is not associated with a user: KeyError on ["onwer"]
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
        message_path_template = Template("/messages.json?auth=$idtoken&orderBy=\"$orderby\"&equalTo=\"$equalto\"")
        message_path = message_path_template.substitute(idtoken=self.idtoken, orderby="recipient", equalto=self.device_get()["uid"] )
        url = self.config.get_config()["firebase"]["databaseURL"] + message_path
        return url
    
    def listen_for_messages(self, callback):
        self.message_processor = callback
        message_reader_thread = threading.Thread(target=asyncio.run, args=(self.message_reader(),))
        message_reader_thread.start()

        def listener_manager(self, message_reader_thread):    
            while True:
                if not message_reader_thread.is_alive():
                    app_log.debug("Restarting message listener with new idtoken")
                    message_reader_thread.join()
                    message_reader_thread = threading.Thread(target=asyncio.run, args=(self.message_reader(),))
                    message_reader_thread.start()
                sleep(5)

        message_auth_manager = threading.Thread(target=listener_manager, args=(self, message_reader_thread,))
        message_auth_manager.start()
        return
    
    # async def message_reader(self):
    #     # more details about SSE https://html.spec.whatwg.org/multipage/server-sent-events.html
    #     async for event in aiosseclient(self.listen_for_messages_url(), valid_http_codes=[200], exit_events=["cancel", "auth_revoked"], timeout_total=1200):
    #         # expected events and data https://firebase.google.com/docs/reference/rest/database#section-streaming
    #         app_log.debug("Received SSE %s with data %s" % (event.event, event.data))
    #         # only process put and patch events
    #         if event.event in ["put", "patch"]:
    #             self.message_capture(event.data)
    async def message_reader(self):
        try:
           async with sse_client.EventSource(self.listen_for_messages_url()) as event_source:
                async for event in event_source:
                    app_log.debug("Received SSE %s with data %s" % (event.type, event.data))
                    # only process put and patch events
                    if event.type in ["put", "patch"]:
                        self.message_capture(event.data)
        except ConnectionError:
            app_log.error("ConnectionError: %s" % traceback.format_exc())
        except TimeoutError:
            app_log.error("TimeoutError: %s" % traceback.format_exc())
        except Exception:
            app_log.error("UnexpectedError: %s" % traceback.format_exc())

    def archive_message(self, key, message):
        self.db.child("processed").child(datetime.date.today()).push(message, token=self.idtoken)
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
    status_update = {"status": 
                        {
                            "line_in_pressure": 50,
                            "solution_weight": 12.5,
                            "version": "0.1.0",
                            "next_spray": datetime.datetime.now(),
                            "timestamp": datetime.datetime.now()
                        }
    }
    cloud.device_update(status_update)

    # test getting version and download
    version = cloud.get_latest_release()
    print(version)
    cloud.download_latest_release()

    # test messages
    def message_processor(message):
        app_log.info("Received message: %s", message)
        # TODO do something with the message
        return True

    cloud.listen_for_messages(message_processor)
    cloud.send_message("SPRAY_NOTIFICATION", "Spray started 1")
    cloud.send_message("SPRAY_NOTIFICATION", "Spray started 2")
    try:
        while True:
            sleep(5)
    except KeyboardInterrupt:
        pass
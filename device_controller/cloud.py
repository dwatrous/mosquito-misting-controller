# Import Firebase REST API 
import atexit
import firebase
import requests
import utils
import datetime
import sys

class Cloud(object):
    # get Config
    config = utils.Config()
    authenticated_device_account = None

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
            user = self.auth.sign_in_with_email_and_password(self.config.device_email, self.config.device_password)
            self.authenticated_device_account = {
                "uid": user["localId"],
                "serial_number": user["displayName"],
                "serial_number_as_email": user["email"],
                "idToken": user["idToken"],
                "refreshToken": user["refreshToken"],
                "expiresAt": user["expiresAt"]
            }
        # handle refresh
        if datetime.datetime.now() > datetime.datetime.fromtimestamp(self.authenticated_device_account["expiresAt"]):
            user = self.auth.refresh(self.authenticated_device_account['refreshToken'])
            self.authenticated_device_account["idToken"] = user["idToken"]
            self.authenticated_device_account["expiresAt"] = user["expiresAt"]
        # finally, return authenticated_device_account, which may just be the cached values
        return self.authenticated_device_account
        # TODO handle error case

    # Firestore
    def device_get(self):
        return self.ds.collection(u'devices').document(self.config.device_email).get(token=self.get_authenticated_device_account()["idToken"])

    def device_update(self, device):
        return self.ds.collection(u'devices').document(self.config.device_email).update(device, token=self.get_authenticated_device_account()["idToken"])

    def write_spray_occurence_ds(self, spraydata):
        # TODO this is probably too optimistic, add error handling
        self.ds.collection(u'devices').document(self.config.device_email).collection(u'sprayoccurrences').add(spraydata, token=self.get_authenticated_device_account()["idToken"])

    def account_get(self, account_id):
        try:
            account = self.ds.collection(u"Users").document(account_id).get(token=self.get_authenticated_device_account()["idToken"])
        except requests.exceptions.HTTPError:
            # TODO cleanup...assume 404, but it could be something else, like a 403, which might be confusing
            the_type, the_value, the_traceback = sys.exc_info()
            return the_value
        return account

    def account_update(self, account_id, account):
        try:
            self.ds.collection()(u"Users").document(account_id).update(account, token=self.get_authenticated_device_account()["idToken"])
        except:
            pass    # TODO add error handling here
    

    # Firebase realtime database (used for messaging)
    def _build_message(self, event, info, action, sender):
        msg = {
            "sender": sender,
            "message": {
                "event": event,
                "action": action,
                "info": info
            },
            "time": datetime.datetime.now().strftime("%m-%d-%Y, %H:%M:%S")
        }
        return msg

    def send_message(self, event, info="", action=None, sender="device"):
        message = self._build_message(event, info, action, sender)
        self.db.child("devices").child(self.get_authenticated_device_account()["uid"]).child("messages").push(message, token=self.get_authenticated_device_account()["idToken"])

    def listen_for_messages(self, callback):
        self.my_stream = self.db.child("devices").child(self.get_authenticated_device_account()["uid"]).child("messages").stream(callback, token=self.get_authenticated_device_account()["idToken"])
        atexit.register(self.my_stream.close)

    def mark_message_read(self, message):
        message_key = message["path"][1:]
        self.db.child("devices").child(self.get_authenticated_device_account()["uid"]).child("messages").child(message_key).remove(token=self.get_authenticated_device_account()["idToken"])
        self.db.child("devices").child(self.get_authenticated_device_account()["uid"]).child("processed").push(message["data"], token=self.get_authenticated_device_account()["idToken"])

if __name__ == '__main__':
    cloud = Cloud()
    print(cloud.get_authenticated_device_account())
    spraydata = {"spraydetails": "lots of data here"}
    cloud.write_spray_occurence_ds(spraydata)
    mydevice = cloud.device_get()
    print(mydevice)
    
    account = cloud.account_get('t8abTKbDoCY8lf3q6XeRcl2H3fA3')
    print(account)
    notaccount = cloud.account_get('fake')
    print(notaccount)

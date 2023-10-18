# Import Firebase REST API 
import atexit
import firebase
import requests
import utils
import datetime

class Cloud(object):
    # get Config
    config = utils.Config()
    authenticated_user = None

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
    def get_authenticated_user(self):
        # handle initial authentication
        if self.authenticated_user == None:
            user = self.auth.sign_in_with_email_and_password(self.config.device_email, self.config.device_password)
            self.authenticated_user = {
                "uid": user["localId"],
                "serial_number": user["displayName"],
                "serial_number_as_email": user["email"],
                "idToken": user["idToken"],
                "refreshToken": user["refreshToken"],
                "expiresAt": user["expiresAt"]
            }
        # handle refresh
        if datetime.datetime.now() > datetime.datetime.fromtimestamp(self.authenticated_user["expiresAt"]):
            user = self.auth.refresh(self.authenticated_user['refreshToken'])
            self.authenticated_user["idToken"] = user["idToken"]
            self.authenticated_user["expiresAt"] = user["expiresAt"]
        # finally, return authenticated_user, which may just be the cached values
        return self.authenticated_user

    # Firestore
    def write_spray_occurence_ds(self, spraydata):
        # TODO this is probably too optimistic, add error handling
        self.ds.collection(u'devices').document(self.config.device_email).collection(u'sprayoccurrences').add(spraydata, token=self.get_authenticated_user()["idToken"])

    def account_get(self, account_id):
        try:
            account = self.ds.collection(u"accounts").document(account_id).get(token=self.get_authenticated_user()["idToken"])
        except requests.exceptions.HTTPError:
            # TODO cleanup...assume 404, but it could be something else, like a 403, which might be confusing
            return None
        return account

    def account_update(self, account_id, account):
        try:
            self.ds.collection()(u"accounts").document(account_id).update(account, token=self.get_authenticated_user()["idToken"])
        except:
            pass    # TODO add error handling here

    # Firebase (used for messaging)
    def _build_message(self, event, info, action, origin):
        msg = {
            "origin": origin,
            "data": {
                "event": event,
                "action": action,
                "info": info
            },
            "time": datetime.datetime.now()
        }
        return msg

    def send_message(self, event, info="", action=None, origin="device"):
        message = self._build_message(event, info, action, origin)
        self.db.child("devices").child(self.get_authenticated_user()["uid"]).child("messages").push(message, token=self.get_authenticated_user()["idToken"])

    def listen_for_messages(self, callback):
        self.my_stream = self.db.child("devices").child(self.get_authenticated_user()["uid"]).child("messages").stream(callback, token=self.get_authenticated_user()["idToken"])
        atexit.register(self.my_stream.close)

    def mark_message_read(self, message):
        document_key = list(message.keys())[0]  # should only ever get one message at a time
        self.db.child("devices").child(self.get_authenticated_user()["uid"]).child("messages").child(document_key).remove(token=self.get_authenticated_user()["idToken"])
        self.db.child("devices").child(self.get_authenticated_user()["uid"]).child("processed").push(message, token=self.get_authenticated_user()["idToken"])

if __name__ == '__main__':
    cloud = Cloud()
    print(cloud.get_authenticated_user())
    spraydata = {"spraydetails": "lots of data here"}
    cloud.write_spray_occurence_ds(spraydata)
    account = cloud.account_get('dwmaillist@gmail.com')
    print(account)
    notaccount = cloud.account_get('fake')
    print(notaccount)

# Import Firebase REST API 
import firebase
import utils
import datetime

class Cloud(object):
    # get Config
    config = utils.Config()
    authenticated_user = None

    # Firebase app
    app = None
    # Firebase Auth
    auth = None
    # Firestore
    ds = None
    # Realtime database
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

    def get_authenticated_user(self):
        # handle initial authentication
        if self.authenticated_user == None:
            user = self.auth.sign_in_with_email_and_password(self.config.get_config()["device"]["email"], self.config.get_config()["device"]["password"])
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

    def write_spray_occurence_ds(self, spraydata):
        self.ds.collection(u'devices').document(self.config.get_config()["device"]["email"]).collection(u'sprayoccurrences').add(spraydata)

if __name__ == '__main__':
    cloud = Cloud()
    print(cloud.get_authenticated_user())
    spraydata = {"spraydetails": "lots of data here"}
    cloud.write_spray_occurence_ds(spraydata)

# cloud interactions
from firebase_admin import firestore
# on Raspberry pi may need sudo apt-get install build-essential libssl-dev libffi-dev python3-dev cargo before installing python requirements
import firebase_admin
app = firebase_admin.initialize_app()
db = firestore.client()

def write_to_cloud(func):
    def execute_and_write(myobj):
        # logging.info("Ready to run spray execution and log in cloud")
        func(myobj)
        doc_ref = db.collection(u'sprayoccurrences').document()
        doc_ref.set(myobj.spraydata)
    return execute_and_write

# cloud interactions
from firebase_admin import firestore
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

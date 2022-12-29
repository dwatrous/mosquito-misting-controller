import firebase_admin
from firebase_admin import firestore

# Application Default credentials are automatically created.
app = firebase_admin.initialize_app()
db = firestore.client()

# Account details
account_id = u'dwmaillist@gmail.com'
account_details = {
    u'street1': u'11402 Rothglen Dr', 
    u'street2': u'', 
    u'city': u'Houston', 
    u'state': u'TX', 
    u'zip': u'77070',
    u'phone': u'8322283551',
    u'phone_preferences': {u'text': True, u'call': False}
    }

doc_ref = db.collection(u'accounts').document(account_id)
doc_ref.set({
    u'details': account_details,
    u'devices': {},
    u'subscription': 1815
})


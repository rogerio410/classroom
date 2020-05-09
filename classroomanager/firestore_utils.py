import firebase_admin
from firebase_admin import credentials, firestore


def get_firestore_client():

    try:
        credential = credentials.Certificate(
            'firestore-auth.json')

        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app(
            credential, {
                'project_id': 'classroom-ifpi-c-1588257756754',
            }
        )

    return firestore.client()

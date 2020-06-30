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


def get_firestore_timestamp():
    return firestore.SERVER_TIMESTAMP


def save_batch(disciplinas, errors, profile_email):

    firestore = get_firestore_client()

    # limite de 500 por request - timestamp, increment and ArrayUnion is like 1
    PER_REQUEST = 250
    batch_slots = len(disciplinas) // PER_REQUEST
    if len(disciplinas) % PER_REQUEST > 0:
        batch_slots += 1

    for i in range(batch_slots):
        batch = firestore.batch()
        start = i * PER_REQUEST
        end = start + PER_REQUEST
        for disc in disciplinas[start:end]:
            print('disciplinas: ', disciplinas)
            print('\n\nDisc: ', disc)
            id = f"{disc['id']}-{profile_email}"
            disc['user'] = profile_email
            disc['timestamp'] = get_firestore_timestamp()
            disc['courseId'] = disc['id']

            ref = firestore.collection('courses').document(id)
            batch.set(ref, disc)

        try:
            batch.commit()
        except Exception as e:
            errors.extend(disciplinas[start:end])

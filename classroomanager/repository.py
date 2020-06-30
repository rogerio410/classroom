from abc import ABC, abstractmethod
from .core.firestore_utils import get_firestore_client, get_firestore_timestamp
from .core.classroom_operacoes import CourseState
from .core.models import Course
import flask
import google
from firebase_admin import firestore


class AbstractRepository(ABC):

    @abstractmethod
    def get(self, id=None):
        raise NotImplementedError

    @abstractmethod
    def list(self):
        raise NotImplementedError

    @abstractmethod
    def save(self, entity):
        raise NotImplementedError


class FirestoreRepository(AbstractRepository):

    def __init__(self, collection_name, model, limit=100):
        self._Model = model
        self._collection_name = collection_name
        self._collection_ref = get_firestore_client()\
            .collection(self._collection_name)\
            .where('user', '==', get_user_email())\
            .order_by('updateTime', direction=firestore.Query.DESCENDING).order_by('section')\
            .limit(limit)

    def get(self, id):
        course_id = f'{id}-{get_user_email()}'

        doc = get_firestore_client().collection(
            self._collection_name).document(course_id).get()

        if not doc.to_dict() or doc.to_dict()['user'] != get_user_email():
            raise google.cloud.exceptions.NotFound('Doc not found!')

        return self._Model.from_dict(doc.to_dict())

    def save(self, entity):
        pass

    def list(self, courseStates=[CourseState.ACTIVE.value, CourseState.PROVISIONED.value, ], limit=None):
        collection_ref = self._collection_ref

        if limit:
            collection_ref = collection_ref.limit(limit)

        if courseStates:
            for cs in courseStates:
                collection_ref_cs = collection_ref.where(
                    'courseState', '==', cs)

                for doc in collection_ref_cs.stream():
                    yield self._Model.from_dict(doc.to_dict())


def get_user_email():
    return flask.session.get('profile').get('email')

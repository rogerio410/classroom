from abc import ABC, abstractmethod
from .core.firestore_utils import get_firestore_client, get_firestore_timestamp
from .core.classroom_operacoes import CourseState
import flask


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

    def __init__(self, collection_name):
        self._collection_name = collection_name
        self._collection_ref = get_firestore_client().collection(
            self._collection_name).where('user', '==', get_user())

    def get(self):
        pass

    def save(self, entity):
        pass

    def list(self, courseState=CourseState.ACTIVE.value):
        if courseState:
            self._collection_ref = self._collection_ref.where(
                'courseState', '==', courseState)

        return self._collection_ref.stream()


def get_user():
    return flask.session.get('profile').get('email')

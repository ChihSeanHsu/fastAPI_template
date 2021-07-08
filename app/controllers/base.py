import abc

from pydantic import BaseModel

from sqlalchemy.orm import sessionmaker


class BaseController(abc.ABC):
    def __init__(self, db: sessionmaker):
        self.db = db

    @abc.abstractmethod
    def get(self, user_id: int, **kwargs):
        raise NotImplemented

    @abc.abstractmethod
    def list(self, user_id: int, **kwargs):
        raise NotImplemented

    @abc.abstractmethod
    def create(self, obj: BaseModel, **kwargs):
        raise NotImplemented

    @abc.abstractmethod
    def delete(self, user_id: int, target_id: int, *args, **kwargs):
        raise NotImplemented

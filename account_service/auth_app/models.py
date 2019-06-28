import enum
import bson
from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP, func

from account_service.models import BaseModel, JsonSerializable


__all__ = ['Role', 'User', 'tables']


class Role(enum.Enum):
    USER = 'user'
    ADMIN = 'admin'


class User(BaseModel, JsonSerializable):
    id = Column(String(255), primary_key=True)
    email = Column(String(1000), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(Role), nullable=False)
    created = Column(TIMESTAMP, server_default=func.now())
    updated = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())

    serialize_fields = [id, role, created, updated]

    def __init__(self, email: str, role: Role, encrypted_password: str):
        self.role = role
        self.email = email
        self.password = encrypted_password
        self.id = str(bson.ObjectId())

    def __repr__(self):
        return f'<User({self.id} {self.role})>'


tables = [User.__table__]

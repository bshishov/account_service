from decimal import Decimal
import bson

from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, func
from account_service.models import BaseModel, JsonSerializable

__all__ = ['Account', 'tables']


class CreatedUpdatedMixin(object):
    created = Column(TIMESTAMP, server_default=func.now())
    updated = Column(TIMESTAMP, server_default=func.now(), onupdate=func.current_timestamp())


class Account(BaseModel, CreatedUpdatedMixin, JsonSerializable):
    id = Column(String(255), primary_key=True)
    user_id = Column(String(255), nullable=False)
    balance = Column(DECIMAL(19, 4), nullable=False)
    state = Column(Integer, nullable=False, default=0)

    serialize_fields = [id, user_id, balance]

    def __init__(self, user_id, balance: Decimal = Decimal('0')):
        self.id = str(bson.ObjectId())
        self.balance = balance
        self.user_id = user_id

    def __repr__(self):
        return f'<Account({self.id} {self.user_id}, {self.balance})>'


tables = [Account.__table__]

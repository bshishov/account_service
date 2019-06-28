import json

from sqlalchemy import MetaData, Column
from sqlalchemy.ext.declarative import as_declarative, declared_attr


__all__ = ['BaseModel', 'JsonSerializable']


@as_declarative(metadata=MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
      }))
class BaseModel(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


class JsonSerializable(object):
    serialize_fields = None

    def __prepare_value(self, val):
        if isinstance(val, (int, str, float)):
            return val
        elif isinstance(val, JsonSerializable):
            return val.to_dict()
        elif isinstance(val, (list, tuple, set)):
            result = []
            for item in result:
                result.append(self.__prepare_value(item))
            return result
        elif isinstance(val, dict):
            result = {}
            for key, item in result.items():
                result[key] = self.__prepare_value(item)
            return result
        return str(val)

    def __get_serialized_dict(self):
        result = {}
        for field in self.serialize_fields:
            if isinstance(field, str):
                result[field] = self.__prepare_value(getattr(self, field))
            elif isinstance(field, Column):
                result[field.name] = self.__prepare_value(getattr(self, field.name))
        return result

    def to_json(self):
        if self.serialize_fields is None:
            return json.dumps(self.__dict__)
        return json.dumps(self.__get_serialized_dict(), default=str)

    def to_dict(self):
        if self.serialize_fields is None:
            return self.__dict__
        return self.__get_serialized_dict()

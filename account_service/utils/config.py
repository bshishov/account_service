import os
import json
import configparser
import re
import logging

__all__ = ['Config']


class Config(object):
    def as_dict(self):
        # Merged class properties and instance properties
        self_dict = self.__class__.__dict__.copy()
        self_dict.update(self.__dict__)

        # Remove magic/system properties and methods
        def valid_kvp(k, v):
            if k.startswith('__'):
                return False
            if isinstance(v, classmethod):
                return False
            if callable(v):
                return False
            return True

        return {k.upper(): v for k, v in self_dict.items() if valid_kvp(k, v)}

    def update(self, config: 'Config', only_existing=True):
        current = self.as_dict()
        target_dict = config.as_dict()

        if only_existing:
            for k, v in target_dict.items():
                if k in current:
                    current[k] = v
        else:
            current.update(target_dict)

        self.__dict__ = current

    def get(self, attr_name: str, default=None):
        return getattr(self, attr_name.upper(), default=default)

    def set(self, attr_name: str, value):
        self.__setattr__(attr_name.upper(), value)

    def update_from_env(self):
        current = self.as_dict()
        for k, v in current.items():
            try:
                current[k] = os.environ[k]
            except KeyError:
                pass
        self.__dict__ = current

    @classmethod
    def from_dict(cls, obj: dict) -> 'Config':
        valid_key = re.compile('^[a-zA-Z_][a-zA-Z_0-9]*$')

        cfg = Config()
        # Why not cfg.__dict__ = json_cfg ?
        for k, v in obj.items():
            if valid_key.match(k):
                cfg.set(k, v)
            else:
                logging.warning('Invalid configuration key {0}'.format(k))
        return cfg

    @classmethod
    def from_properties_file(cls, path: str) -> 'Config':
        if not os.path.exists(path):
            raise RuntimeError('File {0} does not exist')

        cfg_parser = configparser.ConfigParser()

        with open(path, 'r') as f:
            config_string = '[dummy_section]\n' + f.read()

        cfg_parser.read_string(config_string)

        cfg_dict = dict(cfg_parser.items(section='dummy_section'))
        return cls.from_dict(cfg_dict)

    @classmethod
    def from_cfg_file(cls, path: str, section='DEFAULT') -> 'Config':
        if not os.path.exists(path):
            raise RuntimeError('File {0} does not exist')

        cfg_parser = configparser.ConfigParser()
        cfg_parser.read(path)

        cfg_dict = dict(cfg_parser.items(section=section))
        return cls.from_dict(cfg_dict)

    @classmethod
    def from_json_file(cls, path: str) -> 'Config':
        if not os.path.exists(path):
            raise RuntimeError('File {0} does not exist')
        with open(path, 'r', encoding='utf-8') as fp:
            json_cfg = json.load(fp)
        assert isinstance(json_cfg, dict), 'Incorrect Json configuration file'
        return cls.from_dict(json_cfg)

    @classmethod
    def from_file(cls, path: str) -> 'Config':
        if not os.path.exists(path):
            raise RuntimeError('File {0} does not exist')

        if path.endswith('.json'):
            return cls.from_json_file(path)
        if path.endswith('.cfg') or path.endswith('.ini'):
            return cls.from_cfg_file(path)
        if path.endswith('.properties'):
            return cls.from_properties_file(path)

        raise RuntimeError('File should end with .json, .cfg, .properties or .ini')

    @classmethod
    def from_env_filename(cls, var_name: str) -> 'Config':
        val = os.environ.get(var_name, None)
        if not val:
            raise RuntimeError('Environmental variable {0} is not set'.format(var_name))
        return cls.from_file(val)

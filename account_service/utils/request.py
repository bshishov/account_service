from urllib.parse import parse_qs
import cgi

from .errors import HttpError, Status


__all__ = ['Request']


class Request(object):
    _headers = {}

    def __init__(self, wsgi_env: dict):
        self._wsgi_env = wsgi_env

        self._path = wsgi_env.get('PATH_INFO')
        self._uri = wsgi_env.get('REQUEST_URI')
        self._method = wsgi_env.get('REQUEST_METHOD')
        self._query_string = wsgi_env.get('QUERY_STRING')
        self._content_len_header = wsgi_env.get('CONTENT_LENGTH', None)
        self._content_type_header = wsgi_env.get('CONTENT_TYPE', None)

        self._parsed_qs = None
        self._parsed_data = None

        # Parse WSGI HTTP headers
        # All HTTP headers starts with HTTP_ (5 symbols) in WSGI env
        self._headers = {k[5:].lower(): wsgi_env[k] for k in wsgi_env if k.startswith('HTTP_')}
        if self._content_len_header is not None:
            self._headers['content-length'] = self._content_len_header
        if self._content_type_header is not None:
            self._headers['content-type'] = self._content_type_header

    @property
    def method(self):
        return self._method

    @property
    def path(self):
        return self._path

    @property
    def uri(self):
        return self._uri

    @property
    def query_parameters(self):
        if self._parsed_qs is None:
            self._parsed_qs = parse_qs(self._query_string)
        return self._parsed_qs

    @property
    def data(self):
        if self._parsed_data is None:
            # Parse query parameters first
            self._parsed_data = self.query_parameters

            if self.method in ['POST', 'PUT']:
                if self._content_type_header is not None:
                    try:
                        headers = cgi.Message()
                        headers.set_type(self._content_type_header)
                        headers['Content-Length'] = self._content_len_header
                        fields = cgi.FieldStorage(self._wsgi_env.get('wsgi.input'),
                                                  headers=headers,
                                                  encoding='utf-8',
                                                  errors='replace',
                                                  environ={'REQUEST_METHOD': 'POST'})
                        for key in fields:
                            if key in self._parsed_data:
                                self._parsed_data[key] += _get_post_values(fields, key)
                            else:
                                self._parsed_data[key] = _get_post_values(fields, key)
                    except Exception:
                        raise HttpError(Status.BAD_REQUEST)
            for key in self._parsed_data:
                val = self._parsed_data[key]
                if isinstance(val, list) and len(val) == 1:
                    self._parsed_data[key] = val[0]
        return self._parsed_data

    def get_header_value(self, header_name: str, default=None) -> str:
        return self._headers.get(header_name.lower(), default)

    def get_arg_or_bad_request(self, key):
        if key in self.data:
            return self.data[key]
        raise HttpError(Status.BAD_REQUEST)


def _get_post_values(fields: cgi.FieldStorage, key):
    def _get_value(f: cgi.FieldStorage):
        if f.filename is not None:
            return f
        return f.value

    """ Return list of received values."""
    if key in fields:
        value = fields[key]
        if isinstance(value, list):
            return [_get_value(x) for x in value]
        else:
            return [_get_value(value)]
    else:
        return []

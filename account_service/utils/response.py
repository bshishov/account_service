import json
import os
import mimetypes
from io import RawIOBase
from http.client import responses


__all__ = ['Response', 'JsonResponse', 'FileResponse', 'StreamedResponse', 'FileResponse']

ENCODING = 'utf-8'
JSON_CONTENT_TYPE = 'application/json; charset={}'.format(ENCODING)
CONTENT_LENGTH = 'Content-Length'
CONTENT_TYPE = 'Content-Type'


class Response(object):
    def __init__(self, data=None,
                 status_code: int=200,
                 status_message=None,
                 content_type='application/json',
                 content_len=None,
                 headers: dict=None):
        if not headers:
            self.headers = {}
        else:
            self.headers = headers
        self.status = status_code

        if not status_message:
            # Get default status message
            self.status_message = responses.get(status_code, '')
        else:
            self.status_message = status_message

        if content_len is not None:
            self.headers[CONTENT_LENGTH] = content_len
        elif CONTENT_LENGTH not in self.headers:
            self.headers[CONTENT_LENGTH] = len(data)

        if content_type is not None and CONTENT_TYPE not in self.headers:
            self.headers[CONTENT_TYPE] = content_type

        self.body = data

    @property
    def status_string(self):
        return '{0} {1}'.format(self.status, self.status_message)

    @property
    def content_len(self):
        return self.headers.get('Content-Length', None)

    @content_len.setter
    def content_len(self, value):
        self.headers['Content-Length'] = value

    def headers_as_tuples(self):
        return [(k, str(v)) for k, v in self.headers.items()]

    def __iter__(self):
        yield self.body


class JsonResponse(Response):
    def __init__(self, data,
                 status_code: int=200,
                 status_message=None,
                 headers: dict=None):
        super().__init__(json.dumps(data).encode(ENCODING),
                         status_code=status_code,
                         status_message=status_message,
                         headers=headers,
                         content_len=None,
                         content_type=JSON_CONTENT_TYPE)
        # Nosniff header for security purposes:
        # see: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options
        self.headers['X-Content-Type-Options'] = 'nosniff'


class StreamedResponse(Response):
    def __init__(self, stream: RawIOBase, chunk_size=4096, *args, **kwargs):
        self.chunk_size = chunk_size

        # Get content-size
        stream.seek(0, os.SEEK_END)
        content_length = stream.tell()
        stream.seek(0, os.SEEK_SET)

        super().__init__(stream, content_len=content_length, *args, **kwargs)

    def __iter__(self):
        return self

    def __next__(self):
        data = self.body.read(self.chunk_size)
        if not data:
            self.body.close()
            raise StopIteration
        return data


class FileResponse(StreamedResponse):
    def __init__(self, path: str, *args, **kwargs):
        stream = open(path, 'rb')
        mime_type = mimetypes.guess_type(path)[0]
        if mime_type is None:
            mime_type = 'application/octet-stream'

        super().__init__(stream, content_type=mime_type, *args, **kwargs)

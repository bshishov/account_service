from typing import List
from . import Request, Status, HttpError, Response


__all__ = ['allow_methods', 'allow_cors', 'cache_control']


def allow_methods(*methods: List[str]):
    def decorator(fn):
        def wrapper(request: Request, *args, **kwargs):
            if request.method in methods:
                return fn(request, *args, **kwargs)
            raise HttpError(Status.METHOD_NOT_ALLOWED)
        return wrapper
    return decorator


def allow_cors(origin='*',
               methods=('POST', 'GET', 'OPTIONS'),
               headers=('Content-Type', 'Authorization'),
               max_age: int=86400):
    def decorator(fn):
        def wrapper(request: Request, *args, **kwargs):
            if request.method == 'OPTIONS':
                response = Response(data='',
                                    status_code=Status.OK,
                                    content_type='text/plain',
                                    content_len=0,
                                    headers={
                                        'Access-Control-Allow-Methods': ', '.join(methods),
                                        'Access-Control-Allow-Headers': ', '.join(headers),
                                        'Access-Control-Max-Age': str(max_age)
                                    })
            else:
                response = fn(request, *args, **kwargs)

            if response:
                response.headers['Access-Control-Allow-Origin'] = origin
            return response
        return wrapper
    return decorator


def cache_control(control: str='public', max_age: int=86400):
    def decorator(fn):
        def wrapper(request: Request, *args, **kwargs):
            response = fn(request, *args, **kwargs)
            if response:
                if 'Cache-Control' not in response.headers:
                    response.headers['Cache-Control'] = '{0}, max_age={1}'.format(control, max_age)
            return response
        return wrapper
    return decorator

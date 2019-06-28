import re
from typing import Callable
from urllib.parse import unquote
from account_service.utils import HttpError, Status, Request, Response


__all__ = ['Router']


class Router(object):
    def __init__(self):
        self._routes = []
        self._nested_routers = []

    def add_route(self, route_pattern: str, handler: Callable):
        self._routes.append((re.compile(route_pattern), handler))

    def nested_route(self, prefix: str, router: 'Router'):
        self._nested_routers.append((prefix, router))

    def dispatch(self, path: str, request: Request) -> Response:
        if not path:
            raise HttpError(Status.BAD_REQUEST, 'Invalid path')

        # First - try nested routers if any
        for prefix, router in self._nested_routers:
            if not prefix or prefix == '/':
                return router.dispatch(path, request)
            elif path.startswith(prefix):
                relative_path = path[len(prefix):]
                if not relative_path.startswith('/'):
                    relative_path = f'/{relative_path}'
                return router.dispatch(relative_path, request)

        # Then try all the routes
        for compiled_pattern, handler in self._routes:
            match = compiled_pattern.match(path)
            if not match:
                continue

            # Resolve named path arguments
            kwargs = match.groupdict()  # type: dict
            kwargs = {k: unquote(v) for k, v in kwargs.items() if v}

            # Invoke actual request handler
            return handler(request, **kwargs)

        # No route found
        raise HttpError(Status.NOT_FOUND)

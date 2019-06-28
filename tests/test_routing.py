import pytest
from contextlib import contextmanager

from account_service.utils import Router, HttpError, Request


@contextmanager
def does_not_raise(*args):
    yield tuple(args)


def dummy_request_handler(route_name):
    def _handler(request, **kwargs):
        return route_name, kwargs
    return _handler


@pytest.fixture
def router() -> Router:
    router = Router()
    router.add_route('^/foo/bar$', dummy_request_handler('foo_bar_route'))
    router.add_route('^/foo$', dummy_request_handler('foo_route'))
    router.add_route('^/$', dummy_request_handler('index_route'))
    return router


@pytest.fixture
def parametric_router() -> Router:
    router = Router()
    router.add_route('^/int_id/(?P<id>[0-9]+)$', dummy_request_handler('int_id'))
    router.add_route('^/optional/(?P<arg>.+)?$', dummy_request_handler('optional'))
    router.add_route('^/$', dummy_request_handler('index_route'))
    return router


@pytest.fixture
def empty_request() -> Request:
    return Request({})


test_data = [
    (None, pytest.raises(HttpError)),
    ('random non existing path', pytest.raises(HttpError)),
    ('/?a=b', pytest.raises(HttpError)),
    ('/foo', does_not_raise('foo_route', {})),
    ('/foo/bar', does_not_raise('foo_bar_route', {})),
    ('/', does_not_raise('index_route', {})),
]


@pytest.mark.parametrize('path,expectation', test_data)
def test_basic_routing(router: Router, empty_request: Request, path, expectation):
    with expectation as expected_return:
        assert router.dispatch(path, empty_request) == expected_return


parametric_test_data = [
    ('/int_id/', pytest.raises(HttpError)),
    ('/int_id', pytest.raises(HttpError)),
    ('/int_id/0', does_not_raise('int_id', {'id': '0'})),
    ('/int_id/12312312412412', does_not_raise('int_id', {'id': '12312312412412'})),
    ('/int_id/0000001', does_not_raise('int_id', {'id': '0000001'})),
    ('/int_id/0asd123ksd-', pytest.raises(HttpError)),
    ('/int_id/just a string / / // /', pytest.raises(HttpError)),
    ('/int_id/00000000000', does_not_raise('int_id', {'id': '00000000000'})),
    ('/optional/', does_not_raise('optional', {})),
    ('/optional/literally anything @#(%*(', does_not_raise('optional', {'arg': 'literally anything @#(%*('})),
    ('/optional', pytest.raises(HttpError)),
]


@pytest.mark.parametrize('path,expectation', parametric_test_data)
def test_parametric_routing(parametric_router: Router, empty_request: Request, path, expectation):
    with expectation as expected_return:
        assert parametric_router.dispatch(path, empty_request) == expected_return

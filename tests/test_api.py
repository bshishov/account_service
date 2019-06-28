import pytest
import json
from decimal import Decimal
from urllib.request import urlopen, Request, HTTPError
from urllib.parse import urlencode
from contextlib import contextmanager

from account_service.service import config
from account_service.utils import Config


HOST = '127.0.0.1'
PORT = 8088


class TestConfig(Config):
    DATABASE_URI = 'sqlite:///test.db'


class Response(object):
    def __init__(self, status: int, body: str, headers: dict):
        self.status = status
        self.body = body
        self.headers = headers

    def json(self):
        if not self.body:
            return None
        return json.loads(self.body, encoding='utf-8')


@pytest.fixture(autouse=True)
def wsgi_app():
    import wsgiserver
    import threading
    from account_service.service import config, configure
    from account_service.wsgi import application_handler

    def _run():
        config.update(TestConfig())
        configure()
        server = wsgiserver.WSGIServer(application_handler, host=HOST, port=PORT)
        server.start()

    thread = threading.Thread(target=_run)
    thread.daemon = True
    thread.start()
    yield thread


def request(path: str, method: str='GET', data=None, auth_token: str=None, headers=None) -> Response:
    url = f'http://{HOST}:{PORT}{path}'
    if headers is None:
        headers = {}

    if auth_token is not None:
        headers['Authorization'] = f'Bearer {auth_token}'

    def __to_tuples(d: dict):
        return [(k, v) for k, v in d.items()]

    if isinstance(data, dict):
        data = urlencode(__to_tuples(data), encoding='utf-8').encode('ascii')
    elif isinstance(data, str):
        data = urlencode(data, encoding='utf-8').encode('ascii')

    req = Request(url, data=data, method=method, headers=headers)
    try:
        response = urlopen(req)
        return Response(status=response.status, body=response.read(), headers=response.headers)
    except HTTPError as e:
        return Response(status=e.code, body=e.reason, headers=e.headers)


@contextmanager
def does_not_raise(*args):
    yield tuple(args)


def get_user_token(email='user1@mail.mail', pwd='qweqwe'):
    """ User 1 """
    response = request('/auth', method='POST', data={
        'email': email,
        'password': pwd
    })
    assert response.status == 200 or response.status == 201, str(response.body)
    return response.json()['access_token']


def create_account_and_get_id(token):
    response = request('/accounts', method='POST', auth_token=token)
    assert 201 == response.status
    return response.json().get('id')


def assert_balance(account, token, balance) -> Response:
    response = request(f'/accounts/{account}', method='GET', auth_token=token)
    assert response.status == 200
    assert Decimal(response.json()['balance']) == Decimal(balance)
    return response


def deposit(account, token, amount) -> Response:
    response = request(f'/accounts/{account}', method='PUT', auth_token=token, data={'amount': amount})
    return response


def transfer(account, account2, token, amount) -> Response:
    response = request(f'/accounts/{account}/transfer',
                       method='POST',
                       auth_token=token,
                       data={
                           'receiver': account2,
                           'amount': amount
                       })
    return response


def test_create_account():
    token = get_user_token('create_account@mail')
    response = request('/accounts', method='POST', auth_token=token)
    assert response.status == 201
    account = response.json()
    assert 'id' in account
    assert 'balance' in account

    response = request('/accounts', method='GET', auth_token=token)
    assert response.status == 200
    accounts = response.json()
    assert account['id'] in map(lambda x: x['id'], accounts)


deposit_test_data = [
    (100, 200, 100),
    ('100', 200, 100),
    (10, 200, 10),
    ('not a correct number', 400, 0),
    (0, 400, 0),
    (-1, 400, 0),
    (0.00001, 200, 0),
]


@pytest.mark.parametrize('amount,expected_code,expected_balance', deposit_test_data)
def test_deposit(amount, expected_code, expected_balance):
    token = get_user_token('test_deposit@mail')
    account = create_account_and_get_id(token)
    response = deposit(account, token, amount)
    assert expected_code == response.status
    assert_balance(account, token, expected_balance)


@pytest.mark.parametrize('amount,expected_code,expected_balance', deposit_test_data)
def test_fail_to_deposit_foreign_account(amount, expected_code, expected_balance):
    token1 = get_user_token('test_deposit@mail')
    token2 = get_user_token('test_deposit2@mail')
    account2 = create_account_and_get_id(token2)
    response = deposit(account2, token1, amount)
    assert 404 == response.status
    assert_balance(account2, token2, 0)


def test_transfer_between_own_accounts():
    token1 = get_user_token('test_transfer@mail')
    account1 = create_account_and_get_id(token1)
    account2 = create_account_and_get_id(token1)
    deposit(account1, token1, 1000)
    response = transfer(account1, account2, token1, 100)
    assert 200 == response.status, response.body
    assert_balance(account1, token1, 900)
    assert_balance(account2, token1, 100)


def test_fail_transfer_between_same_accounts():
    token1 = get_user_token('test_transfer@mail')
    account1 = create_account_and_get_id(token1)
    deposit(account1, token1, 1000)
    response = transfer(account1, account1, token1, 100)
    assert 400 == response.status, response.body
    assert_balance(account1, token1, 1000)


def test_transfer_to_unknown():
    token1 = get_user_token('test_transfer@mail')
    account1 = create_account_and_get_id(token1)
    deposit(account1, token1, 1000)
    response = transfer(account1, 'completely invalid id', token1, 100)
    assert 400 == response.status, response.body
    assert_balance(account1, token1, 1000)


def test_fail_transfer_when_no_money():
    token1 = get_user_token('test_transfer@mail')
    account1 = create_account_and_get_id(token1)
    deposit(account1, token1, 1000)
    response = transfer(account1, 'completely invalid id', token1, 1001)
    assert 400 == response.status, response.body
    assert_balance(account1, token1, 1000)


def test_fail_transfer_when_target_is_too_rich():
    token1 = get_user_token('test_transfer@mail')
    token2 = get_user_token('test_transfer2@mail')
    account1 = create_account_and_get_id(token1)
    account2 = create_account_and_get_id(token2)
    deposit(account1, token1, 1000)
    deposit(account2, token2, config.ACCOUNT_RECEIVER_MAX_AMOUNT + 1)
    response = transfer(account1, account2, token1, 100)
    assert 400 == response.status, response.body
    assert_balance(account1, token1, 1000)
    assert_balance(account2, token2, config.ACCOUNT_RECEIVER_MAX_AMOUNT + 1)


def test_accounts():
    token = get_user_token('test_accounts@mail')
    response = request('/accounts', auth_token=token)
    assert response.status == 200


if __name__ == "__main__":
    pytest.main(['-v', '-m', 'test', 'api.py'])

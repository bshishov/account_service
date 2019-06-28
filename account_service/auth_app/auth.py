from typing import List
import jwt

from account_service.utils import Request, HttpError, Status
from account_service.service import config


__all__ = ['AuthError',
           'get_auth_token',
           'get_token_payload',
           'get_user_from_request',
           'get_user_from_token',
           'requires_auth']


class AuthError(HttpError):
    def __init__(self, message, status_code=Status.UNAUTHORIZED):
        super().__init__(status_code=status_code, message=message)


def get_auth_token(request: Request, raise_if_none=True):
    auth_header = request.get_header_value('Authorization', None)
    if not auth_header:
        if raise_if_none:
            raise AuthError('Token is missing')
        return None

    parts = auth_header.split(' ')
    if len(parts) != 2:
        raise AuthError('Invalid token')

    if parts[0].lower() != 'bearer':
        raise AuthError('Bearer token required')

    return parts[1]


def get_token_payload(token: str):
    try:
        return jwt.decode(token, config.JWT_SECRET, issuer=config.JWT_ISSUER, algorithms=[config.JWT_ALGORITHM])
    except jwt.InvalidTokenError as err:
        raise AuthError('Invalid token: {0}'.format(err.args[0]))


def get_user_from_token(token: str=None, kind='access'):
    if not token:
        return None

    token_payload = get_token_payload(token)
    token_kind = token_payload.get(config.JWT_KIND_CLAIM, None)
    role = token_payload.get(config.JWT_ROLE_CLAIM, None)
    user_id = token_payload.get(config.JWT_USER_ID_CLAIM, None)
    if not token_kind or not user_id:
        raise AuthError('Invalid token')
    if kind != token_kind:
        raise AuthError('Invalid token')
    return dict(id=user_id, role=role)


def get_user_from_request(request: Request, raise_if_no_token=False):
    return get_user_from_token(get_auth_token(request, raise_if_none=raise_if_no_token))


def requires_auth(permited_roles: List[str]=None, allowed_roles: List[str]=None):
    def decorator(fn):
        def wrapper(request: Request, *args, **kwargs):
            user = get_user_from_request(request)
            if user is None:
                raise HttpError(Status.UNAUTHORIZED)

            if permited_roles is not None and user['role'] in permited_roles:
                raise HttpError(Status.FORBIDDEN)

            if allowed_roles is not None and user['role'] not in allowed_roles:
                raise HttpError(Status.FORBIDDEN)

            return fn(request, *args, **kwargs)
        return wrapper
    return decorator
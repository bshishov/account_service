import logging
import datetime

import bcrypt
import jwt

from account_service.utils import Request, JsonResponse, allow_methods, allow_cors, HttpError, Status
from account_service.service import config, db_session
from .models import User, Role
from .auth import *

__all__ = ['auth_view']
_logger = logging.getLogger(__name__)


def create_user_token(user: User, kind: str, encoding='utf-8', expire_seconds=60 * 60 * 24):
    iat = datetime.datetime.utcnow()  # Issued at
    exp = iat + datetime.timedelta(seconds=expire_seconds)  # Expire at

    payload = {
        'iat': iat,
        'exp': exp,
        'iss': config.JWT_ISSUER,
        config.JWT_USER_ID_CLAIM: user.id,
        config.JWT_ROLE_CLAIM: user.role.value,
        config.JWT_KIND_CLAIM: kind
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM).decode(encoding)


def create_access_token(user: User):
    return create_user_token(user=user, expire_seconds=config.JWT_ACCESS_EXPIRATION_SECONDS, kind='access')


def create_refresh_token(user: User):
    return create_user_token(user=user, expire_seconds=config.JWT_REFRESH_EXPIRATION_SECONDS, kind='refresh')


def tokens_response(user: User, status_code=200):
    return JsonResponse({
        'access_token': create_access_token(user),
        'access_token_expiration': config.JWT_ACCESS_EXPIRATION_SECONDS,
        'refresh_token': create_refresh_token(user),
        'refresh_token_expiration': config.JWT_REFRESH_EXPIRATION_SECONDS,
    }, status_code=status_code)


@allow_cors()
@allow_methods('POST', 'PUT', 'DELETE')
def auth_view(request: Request) -> JsonResponse:
    if request.method == 'POST':
        # authorize
        user = get_user_from_request(request)
        if user is not None:
            # User is already authorized
            raise HttpError(Status.BAD_REQUEST, message='Already logged in')

        email = request.get_arg_or_bad_request('email').strip()  # type: str
        pwd_raw = request.get_arg_or_bad_request('password').strip()  # type: str

        with db_session() as session:
            existing_user = session.query(User).filter(User.email == email).first()

            # Create new user
            if existing_user is None:
                pwd_hashed = bcrypt.hashpw(password=pwd_raw.encode('utf-8'),
                                           salt=bcrypt.gensalt(config.AUTH_BCRYPT_ROUNDS))
                user = User(email=email, role=Role.USER, encrypted_password=pwd_hashed)
                session.add(user)
                _logger.info(f'Created new user: {user}')

                # Issue new tokens
                return tokens_response(user, Status.CREATED)

            # Authorize existing user
            if bcrypt.checkpw(pwd_raw.encode('utf-8'), existing_user.password):
                # Issue new tokens
                return tokens_response(existing_user, status_code=Status.OK)

            _logger.info(f'Invalid authentication attempt: {user}')
            raise HttpError(Status.BAD_REQUEST)

    if request.method == 'DELETE':
        # Logout
        raise HttpError(Status.NOT_IMPLEMENTED)

    if request.method == 'PUT':
        # Refresh tokens
        raise HttpError(Status.NOT_IMPLEMENTED)

    raise HttpError(Status.NOT_IMPLEMENTED)

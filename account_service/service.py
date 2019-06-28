import logging
from typing import Optional
from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine

from .utils import Config, Router

__all__ = ['config', 'configure', 'db_session', 'router', 'create_tables']
_logger = logging.getLogger(__name__)


class ServiceConfig(Config):
    """
     Main configuration class with default values
    """
    DEBUG = True
    DATABASE_URI = 'sqlite:///database.db'

    # Logging
    LOG_LEVEL = logging.DEBUG

    # Account settings
    ACCOUNT_RECEIVER_MAX_AMOUNT = 100000

    # Auth and security settings
    AUTH_USE_INTERNAL = True
    AUTH_BCRYPT_ROUNDS = 10

    # JWT
    JWT_SECRET = 'CHANGE_ME'
    JWT_ALGORITHM = 'HS256'
    JWT_ISSUER = 'sber_account_app'
    JWT_ROLE_CLAIM = 'role'
    JWT_USER_ID_CLAIM = 'sub'
    JWT_KIND_CLAIM = 'kind'
    JWT_ACCESS_EXPIRATION_SECONDS = 60 * 60 * 48  # 48-hours token
    JWT_REFRESH_EXPIRATION_SECONDS = 60 * 60 * 24 * 30  # 30-days token
    JWT_EMAIL_CONFIRMATION_SECONDS = 60 * 60 * 24 * 30  # 30-days token


config = ServiceConfig()  # type: ServiceConfig
_Session = None  # type: callable()
router = Router()


@contextmanager
def db_session():
    """Provide a transactional scope around a series of operations."""
    session = _Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        _logger.warning(f'Reverting database transaction due to exception: {e}')
        session.rollback()
        raise e
    finally:
        session.close()


def configure(config_file: Optional[str] = None):
    # Load configuration first
    if config_file:
        # First - try to update from configuration file
        config.update(Config.from_file(config_file))

    # Override values from environment
    config.update_from_env()

    # Set up logging (basic)
    logging.basicConfig(level=config.LOG_LEVEL)

    # Establish database connection factory
    _logger.debug('Initializing database connection factory')
    session_factory = sessionmaker(bind=create_engine(config.DATABASE_URI))
    global _Session
    _Session = scoped_session(session_factory)

    create_tables()

    # App routing
    _logger.debug('Initializing routing')
    if config.AUTH_USE_INTERNAL:
        from .auth_app.routing import router as auth_router
        router.nested_route('/auth', auth_router)

    from .account_app.routing import router as account_router
    router.nested_route('/', account_router)


def create_tables():
    from .account_app.models import tables as account_tables
    from account_service.models import BaseModel

    # Create database tables if not exist
    _logger.debug('Attempting to create tables')
    engine = create_engine(config.DATABASE_URI)
    BaseModel.metadata.create_all(engine, tables=account_tables)

    if config.AUTH_USE_INTERNAL:
        from .auth_app.models import tables as auth_tables
        BaseModel.metadata.create_all(engine, tables=auth_tables)

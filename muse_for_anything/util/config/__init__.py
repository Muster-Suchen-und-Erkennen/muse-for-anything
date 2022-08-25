"""Module containing default config values."""
from logging import INFO, WARNING
from os import urandom

from .oso_config import OsoDebugConfig, OsoProductionConfig
from .passwords_config import PasswordsDebugConfig, PasswordsProductionConfig
from .smorest_config import SmorestDebugConfig, SmorestProductionConfig
from .sqlalchemy_config import SQLAchemyDebugConfig, SQLAchemyProductionConfig


class ProductionConfig(
    SQLAchemyProductionConfig,
    SmorestProductionConfig,
    OsoProductionConfig,
    PasswordsProductionConfig,
):
    ENV = "production"
    SECRET_KEY = urandom(
        32
    )  # set this to a stable key to prevent tokens from expiring on server restart

    REVERSE_PROXY_COUNT = 0

    DEBUG = False
    TESTING = False

    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False

    LOG_CONFIG = None  # if set this is preferred

    DEFAULT_LOG_SEVERITY = WARNING
    DEFAULT_LOG_FORMAT_STYLE = "{"
    DEFAULT_LOG_FORMAT = "{asctime} [{levelname:^7}] [{module:<30}] {message}    <{funcName}, {lineno}; {pathname}>"
    DEFAULT_LOG_DATE_FORMAT = None


class DebugConfig(
    ProductionConfig,
    SQLAchemyDebugConfig,
    SmorestDebugConfig,
    OsoDebugConfig,
    PasswordsDebugConfig,
):
    ENV = "debug"
    DEBUG = True
    SECRET_KEY = "debug_secret"  # FIXME make sure this NEVER! gets used in production!!!

    DEFAULT_LOG_SEVERITY = INFO

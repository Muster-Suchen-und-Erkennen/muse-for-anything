"""Root module containing the flask app factory."""

from json import load as load_json
from logging import WARNING, Formatter, Logger, getLogger
from logging.config import dictConfig
from os import environ, makedirs
from pathlib import Path
from typing import Any, Dict, Optional

import click
from flask import Flask
from flask.cli import FlaskGroup
from flask.logging import default_handler
from flask_cors import CORS
from flask_static_digest import FlaskStaticDigest
from tomli import load as load_toml

from . import api, babel, db, licenses, oso_helpers, password_helpers
from .api import jwt
from .root_routes import register_root_routes
from .util.config import DebugConfig, ProductionConfig

# from .util.gc_settings import register_gc_handler
from .util.reverse_proxy_fix import apply_reverse_proxy_fix

ENV_PREFIX = "M4A"
ENV_VAR_SETTINGS = (
    ("SQLALCHEMY_DATABASE_URI", str),
    ("SECRET_KEY", str),
    ("REVERSE_PROXY_COUNT", int),
    ("DEFAULT_LOG_SEVERITY", int),
)


def create_app(test_config: Optional[Dict[str, Any]] = None):
    """Flask app factory."""
    instance_path: str | None = environ.get(f"{ENV_PREFIX}_INSTANCE_PATH", None)
    if instance_path:
        if Path(instance_path).is_file():
            instance_path = None

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True, instance_path=instance_path)

    # Start Loading config #################

    # load defaults
    flask_debug = (
        app.config.get("DEBUG", False)
        or environ.get("FLASK_ENV", "production").lower() == "development"
    )
    if flask_debug:
        app.config.from_object(DebugConfig)
    elif not test_config:
        # only load production defaults if no special test config is given
        app.config.from_object(ProductionConfig)

    unchanged_secret_key = app.config.get("SECRET_KEY")

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
        # also try to load json config
        app.config.from_file("config.json", load=load_json, silent=True)
        # also try to load toml config
        app.config.from_file("config.toml", load=load_toml, silent=True)
        # load config from file specified in env var
        app.config.from_envvar(f"{__name__}_SETTINGS", silent=True)
        # TODO load some config keys directly from env vars
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # load settings from env vars
    settings_from_env_var = []
    bad_env_var = []
    for setting, class_ in ENV_VAR_SETTINGS:
        setting_env_var = f"{ENV_PREFIX}_{setting}"
        value = environ.get(setting_env_var, None)
        if value is not None:
            try:
                cast_value = class_(value)
                settings_from_env_var.append((setting_env_var, setting))
                app.config[setting] = cast_value
            except:
                bad_env_var.append((setting_env_var, setting))

    # End Loading config #################

    # Configure logging
    log_config: Optional[Dict] = app.config.get("LOG_CONFIG")
    if log_config:
        # Apply full log config from dict
        dictConfig(log_config)
    else:
        # Apply smal log config to default handler
        log_severity = max(0, app.config.get("DEFAULT_LOG_SEVERITY", WARNING))
        log_format_style = app.config.get(
            "DEFAULT_LOG_FORMAT_STYLE", "%"
        )  # use percent for backwards compatibility in case of errors
        log_format = app.config.get("DEFAULT_LOG_FORMAT")
        date_format = app.config.get("DEFAULT_LOG_DATE_FORMAT")
        if log_format:
            formatter = Formatter(log_format, style=log_format_style, datefmt=date_format)
            default_handler.setFormatter(formatter)
            default_handler.setLevel(log_severity)
            root = getLogger()
            root.addHandler(default_handler)
            app.logger.removeHandler(default_handler)

    try:
        # if gunicorn is installed try to add its logging handlers
        import gunicorn  # noqa

        # tie the flask app logger to the gunicorn error logger
        gunicorn_logger = getLogger("gunicorn.error")
        for handler in gunicorn_logger.handlers:
            app.logger.addHandler(handler)
        if gunicorn_logger.level < app.logger.level:
            app.logger.setLevel(gunicorn_logger.level)
    except ImportError:
        pass

    logger: Logger = app.logger
    logger.info(
        f"Configuration loaded, instance folder located at '{app.instance_path}'."
    )

    if settings_from_env_var:
        logger.info(
            f"The settings {', '.join(v[1] for v in settings_from_env_var)}"
            f" were loaded from the environment variables {', '.join(v[0] for v in settings_from_env_var)}"
        )
    if bad_env_var:
        logger.warning(
            f"The settings {', '.join(v[1] for v in bad_env_var)}"
            f" could not be loaded from the environment variables {', '.join(v[0] for v in settings_from_env_var)}"
        )

    if app.config.get("SECRET_KEY") == "debug_secret":
        logger.error(
            'The configured SECRET_KEY="debug_secret" is unsafe and must not be used in production!'
        )
    elif app.config.get("SECRET_KEY") == unchanged_secret_key:
        logger.error(
            "The SECRET_KEY was not changed from the provided default! This is unsafe for production!"
        )
    if not app.config.get("SECRET_KEY"):
        logger.critical("No secret key configured! Aborting!")
        exit(1)

    # ensure the instance folder exists
    try:
        makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Begin loading extensions and routes

    apply_reverse_proxy_fix(app)

    password_helpers.register_password_helper(app)
    oso_helpers.register_oso(app)

    babel.register_babel(app)

    licenses.register_licenses(app)

    db.register_db(app)

    jwt.register_jwt(app)
    api.register_root_api(app)

    # register_gc_handler(app)

    # allow cors requests everywhere
    CORS(app)

    # setup static digest for SPA
    static_digest = FlaskStaticDigest(app)

    register_root_routes(app, static_digest)

    if app.config.get("DEBUG", False):
        # Register debug routes when in debug mode
        from .util.debug_routes import register_debug_routes

        register_debug_routes(app)

    return app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Cli entry point for autodoc tooling."""
    pass

"""CLI functions for the db module."""

import click
from flask import Blueprint, Flask, current_app
from flask.cli import with_appcontext

from .db import DB
from .models.users import User, UserRole
from ..util.logging import get_logger

# make sure all models are imported for CLI to work properly
from . import models  # noqa


DB_CLI_BLP = Blueprint("db_cli", __name__, cli_group=None)
DB_CLI = DB_CLI_BLP.cli  # expose as attribute for autodoc generation

DB_COMMAND_LOGGER = "db"


@DB_CLI.command("create-db")
@with_appcontext
def create_db():
    """Create all db tables."""
    create_db_function(current_app)
    click.echo("Database created.")


def create_db_function(app: Flask):
    DB.create_all()
    get_logger(app, DB_COMMAND_LOGGER).info("Database created.")


@DB_CLI.command("create-admin-user")
@click.option("-f", "--force", is_flag=True, default=False)
@with_appcontext
def create_admin_user_cli(force: bool = False):
    """Create an admin user with username and password 'admin'."""
    result = create_admin_user(current_app, force)
    if result:
        click.echo("User 'admin' created.")
    else:
        click.echo(
            "User 'admin' was not created. Use -f or --force to force the creation of an admin user."
        )


def create_admin_user(app: Flask, force: bool = False):
    if not force:
        # do not force create admin user when db contains users!
        if User.exists():
            get_logger(app, DB_COMMAND_LOGGER).debug(
                "User 'admin' was not created because a user already exists."
            )
            return False
    admin_user = User(username="admin", password="admin")
    admin_role = UserRole(user=admin_user, role="admin")
    DB.session.add(admin_user)
    DB.session.add(admin_role)
    DB.session.commit()
    get_logger(app, DB_COMMAND_LOGGER).info("User 'admin' created.")
    return True


@DB_CLI.command("drop-db")
@with_appcontext
def drop_db():
    """Drop all db tables."""
    drop_db_function(current_app)
    click.echo("Database dropped.")


def drop_db_function(app: Flask):
    DB.drop_all()
    get_logger(app, DB_COMMAND_LOGGER).info("Dropped Database.")


def register_cli_blueprint(app: Flask):
    """Method to register the DB CLI blueprint."""
    app.register_blueprint(DB_CLI_BLP)
    app.logger.info("Registered DB CLI blueprint.")

"""CLI functions for the db module."""

from email.policy import default
from typing import Optional

import click
from flask import Blueprint, Flask, current_app
from flask.cli import with_appcontext

from .db import DB
from .models.users import ALLOWED_USER_ROLES, User, UserRole
from ..util.logging import get_logger
from .models.namespace import Namespace 
from .models.taxonomies import Taxonomy
from .models.ontology_objects import OntologyObject
from .models.ontology_objects import OntologyObjectType
from .models.owl import OWL

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


@DB_CLI.command("create-user")
@click.option("-u", "--username")
@click.password_option("--password")
@click.option("-r", "--role", default = None)
@click.option("-f", "--force", is_flag=True, default=False)
@with_appcontext
def create_user_cli(username: str, password: str, role: Optional[str] = None, force: bool = False):
    """Create a user with given username and password.
    
    If the user already exists this method does nothing.
    If ``force`` is true and the user exists this method updates the user password.
    """
    result = create_user(current_app, username, password, role, force)
    if result:
        click.echo(f"User '{username}' created or updated.")
    else:
        click.echo(
            f"User '{username}' was not created. Use -f or --force to change the current user password."
        )

def create_user(app: Flask, username: str, password: str, role: Optional[str]=None, force: bool = False):
    if User.exists((User.username == username,)):
        if not force:
        # do not force create user when db contains a user with that name!
            get_logger(app, DB_COMMAND_LOGGER).debug(
                f"User '{username}' was not created because a user already exists."
            )
            return False
        # force can be used to update password of existing users but will not change roles!
        new_user: Optional[User] = User.query.filter(User.username == username).first()
        if new_user is not None:
            new_user.set_new_password(password=password)
            DB.session.add(new_user)
    else:
        new_user = User(username=username, password=password)
        DB.session.add(new_user)
        if role:
            user_role = UserRole(user=new_user, role=role)
            DB.session.add(user_role)
    DB.session.commit()
    get_logger(app, DB_COMMAND_LOGGER).info(f"User '{username}' created or updated.")
    return True


@DB_CLI.command("delete-user")
@click.option("-u", "--username")
@with_appcontext
def delete_user_cli(username: str):
    """Delete the user with the given username."""
    click.confirm(f"This will permanently delete the user '{username}'. Do you want to continue?", default=False, abort=True)
    result = delete_user(current_app, username)
    if result:
        click.echo(f"User '{username}' deleted.")
    else:
        click.echo(
            f"User '{username}' could not be deleted."
        )

def delete_user(app: Flask, username: str):
    user_to_delete: Optional[User] = User.query.filter(User.username == username).first()
    if user_to_delete:
        for role in user_to_delete.roles:
            DB.session.delete(role)
        for grant in user_to_delete.grants:
            DB.session.delete(grant)
        DB.session.delete(user_to_delete)
    
        DB.session.commit()
        get_logger(app, DB_COMMAND_LOGGER).info(f"User '{username}' was deleted.")
    return True


@DB_CLI.command("list-roles")
@click.option("-u", "--username", default=None)
@with_appcontext
def list_roles_cli(username: Optional[str]):
    """List all user roles.
    
    If a username is given list only the roles the user has.
    """
    if username is None:
        click.echo("\n".join(sorted(ALLOWED_USER_ROLES)))
        return
    user: Optional[User] = User.query.filter(User.username == username).first()
    if user:
        click.echo(f"User '{username}' has the following roles:")
        click.echo("\n".join(sorted(r.role for r in user.roles)))
    else:
        click.echo(f"could not find user with name {username}")



@DB_CLI.command("add-role")
@click.option("-u", "--username")
@click.option("-r", "--role")
@with_appcontext
def add_user_role_cli(username: str, role: str):
    """Add a role to an existing user."""
    user: Optional[User] = User.query.filter(User.username == username).first()
    if user:
        new_role = UserRole(user, role)
        DB.session.add(new_role)
        DB.session.commit()
        click.echo(f"Added role '{role}' to user '{username}'.")
    else:
        click.echo(f"could not find user with name {username}")



@DB_CLI.command("remove-role")
@click.option("-u", "--username")
@click.option("-r", "--role")
@with_appcontext
def remove_user_role_cli(username: str, role: str):
    """Remove a role from an existing user."""
    user: Optional[User] = User.query.filter(User.username == username).first()
    if user:
        for r in user.roles:
            if r.role == role:
                DB.session.delete(r)
        DB.session.commit()
        click.echo(f"Removed role '{role}' from user '{username}'.")
    else:
        click.echo(f"could not find user with name {username}")



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

@DB_CLI.command("export-namespace")
@click.option("-n", "--namespace")
@with_appcontext
def map_namespace_to_owl_cli(namespace: int):
    click.echo(f"export {namespace}")
    # get data from db
    if namespace is None:
        return 
    found_namespace = Namespace.query.filter(Namespace.id==namespace).first()

    found_taxonomy = Taxonomy.query.filter(
            Taxonomy.deleted_on == None,
            Taxonomy.namespace_id == found_namespace.id,
        ).all()
    
    found_object_type = OntologyObjectType.query.filter(
            OntologyObjectType.deleted_on == None,
            OntologyObjectType.namespace_id == found_namespace.id,
        ).all()
    
    found_object = OntologyObject.query.filter(
        OntologyObject.deleted_on == None,
        OntologyObject.namespace_id == found_namespace.id,
    ).all()
       
    owl_namespace = OWL._map_namespace_to_owl(current_app, found_namespace, found_taxonomy, found_object_type, found_object)
   
    # owl_ontology = _map_ontology_object_to_owl(ontology_object)

    # click.echo(owl_ontology)
    click.echo(found_namespace)
    click.echo(found_taxonomy)
    click.echo(found_object)
    click.echo(found_object_type)
    # click.echo(dir(found_namespace))
    # For later: move source code to an API endpoint

    click.echo(owl_namespace)


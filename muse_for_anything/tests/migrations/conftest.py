import os
from pathlib import Path
from shutil import rmtree
import tempfile

from flask import Flask
import pytest

from muse_for_anything import create_app
from muse_for_anything.db.db import DB
from muse_for_anything.db.cli import create_db_function
from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.db.models.ontology_objects import (
    OntologyObjectType,
    OntologyObjectTypeVersion,
)
from muse_for_anything.tests.migrations.schemas_for_db_test import (
    INTEGER_SCHEMA,
    OBJECT_SCHEMA,
    UNRESOLVED_COMPLEX_SCHEMA,
    UNRESOLVED_LOCAL_SCHEMA,
    UNRESOLVED_SCHEMA,
)


def tempdir():
    tempdir = tempfile.mkdtemp(prefix="muse-for-anything-test-")
    yield tempdir
    tdir = Path(tempdir)
    rmtree(tdir)


@pytest.fixture(name="tempdir")
def tempdir_fixture():
    yield from tempdir()


def app():
    key = os.urandom(12)
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SECRET_KEY": key,
        "OPENAPI_VERSION": "3.0.2",
    }

    app = create_app(test_config)
    with app.app_context():
        # create db tables and initial values
        create_db_function(app=app)
        set_up_db_values()
    yield app


@pytest.fixture(name="app", scope="session")
def app_fixture():
    yield from app()


@pytest.fixture(name="app_with_temp", scope="session")
def app_with_temp_fixture():
    yield from app()


def client(app: Flask):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(name="client")
def client_fixture(app: Flask):
    return client(app)


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


def set_up_db_values():
    namespace = Namespace(name="testingnamespace", description="no description")
    DB.session.add(namespace)

    ont_type = OntologyObjectType(
        namespace=namespace,
        name="integer_schema",
        description="no description",
        is_top_level_type=True,
    )
    DB.session.add(ont_type)

    ont_type_version = OntologyObjectTypeVersion(
        ontology_type=ont_type, version=1, data=INTEGER_SCHEMA
    )
    DB.session.add(ont_type_version)

    ont_type = OntologyObjectType(
        namespace=namespace,
        name="object_schema",
        description="no description",
        is_top_level_type=True,
    )
    DB.session.add(ont_type)

    ont_type_version = OntologyObjectTypeVersion(
        ontology_type=ont_type, version=1, data=OBJECT_SCHEMA
    )
    DB.session.add(ont_type_version)

    ont_type = OntologyObjectType(
        namespace=namespace,
        name="unresolved_schema",
        description="no description",
        is_top_level_type=True,
    )
    DB.session.add(ont_type)

    ont_type_version = OntologyObjectTypeVersion(
        ontology_type=ont_type, version=1, data=UNRESOLVED_SCHEMA
    )
    DB.session.add(ont_type_version)

    ont_type = OntologyObjectType(
        namespace=namespace,
        name="unresolved_complex_schema",
        description="no description",
        is_top_level_type=True,
    )
    DB.session.add(ont_type)

    ont_type_version = OntologyObjectTypeVersion(
        ontology_type=ont_type, version=1, data=UNRESOLVED_COMPLEX_SCHEMA
    )
    DB.session.add(ont_type_version)

    ont_type = OntologyObjectType(
        namespace=namespace,
        name="unresolved_local_schema",
        description="no description",
        is_top_level_type=True,
    )
    DB.session.add(ont_type)

    ont_type_version = OntologyObjectTypeVersion(
        ontology_type=ont_type, version=1, data=UNRESOLVED_LOCAL_SCHEMA
    )
    DB.session.add(ont_type_version)

    DB.session.commit()

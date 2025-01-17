from flask import Flask
from flask.testing import FlaskClient
from muse_for_anything.json_migrations.data_migration import migrate_data
from muse_for_anything.json_migrations.jsonschema_validator import (
    resolve_schema_reference,
)
from muse_for_anything.tests.migrations.schemas_for_db_test import (
    UNRESOLVED_COMPLEX_SCHEMA,
    UNRESOLVED_LOCAL_SCHEMA,
    UNRESOLVED_SCHEMA,
)


def test_resolve_ref(client: FlaskClient, app: Flask):
    unresolved_reference = UNRESOLVED_SCHEMA["definitions"]["root"]
    referenced_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {"root": {"minimum": 1, "type": ["integer", "null"]}},
        "title": "IntegerType",
    }
    resolved_schema = referenced_schema["definitions"]["root"]
    resolved_reference = None
    with app.app_context():
        with app.test_request_context("http://localhost:5000/", method="GET"):
            resolved_reference, root_schema = resolve_schema_reference(
                unresolved_reference, UNRESOLVED_SCHEMA
            )
    assert resolved_schema == resolved_reference
    assert referenced_schema == root_schema


def test_complex_to_ref_migration(client: FlaskClient, app: Flask):
    source_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "properties": {
                    "one": {
                        "properties": {
                            "one": {"type": ["string"]},
                            "two": {"type": ["integer"]},
                        },
                        "type": ["object"],
                    },
                    "three": {"type": ["number"]},
                    "two": {"type": ["integer"]},
                },
                "type": ["object"],
            }
        },
        "title": "Type",
    }
    data = {"one": {"one": "42", "two": 555}, "two": 42, "three": 53.23}
    updated_data = None
    with app.app_context():
        with app.test_request_context("http://localhost:5000/", method="GET"):
            updated_data = migrate_data(data, source_schema, UNRESOLVED_COMPLEX_SCHEMA)
    assert {"one": {"one": 42, "two": 555}, "two": "42", "three": 53.23} == updated_data


def test_complex_from_ref_migration_(client: FlaskClient, app: Flask):
    target_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "properties": {
                    "one": {
                        "properties": {
                            "one": {"type": ["string"]},
                            "two": {"type": ["integer"]},
                        },
                        "type": ["object"],
                    },
                    "three": {"type": ["number"]},
                    "two": {"type": ["integer"]},
                },
                "type": ["object"],
            }
        },
        "title": "Type",
    }
    data = {"one": {"one": 42, "two": 555}, "two": "42", "three": 53.23}
    updated_data = None
    with app.app_context():
        with app.test_request_context("http://localhost:5000/", method="GET"):
            updated_data = migrate_data(data, UNRESOLVED_COMPLEX_SCHEMA, target_schema)
    assert {"one": {"one": "42", "two": 555}, "two": 42, "three": 53.23} == updated_data


def test_resolve_local_ref(client: FlaskClient, app: Flask):
    unresolved_reference = UNRESOLVED_LOCAL_SCHEMA["definitions"]["root"]
    resolved_schema = {"type": ["integer"]}
    resolved_reference = None
    with app.app_context():
        with app.test_request_context("http://localhost:5000/", method="GET"):
            resolved_reference, root_schema = resolve_schema_reference(
                unresolved_reference, UNRESOLVED_LOCAL_SCHEMA
            )
    assert resolved_schema == resolved_reference
    assert UNRESOLVED_LOCAL_SCHEMA == root_schema

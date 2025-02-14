from flask import Flask
from flask.testing import FlaskClient
from schemas_for_db_test import (
    UNRESOLVED_COMPLEX_SCHEMA,
    UNRESOLVED_LOCAL_SCHEMA,
    UNRESOLVED_SCHEMA,
)

from muse_for_anything.json_migrations import DataMigrator, JsonSchema

_ROOT_URL = "http://localhost:5000/test-schemas/"


def test_resolve_ref(client: FlaskClient, app: Flask):
    unresolved_reference = JsonSchema(
        "http://localhost:5000/api/v1/namespaces/1/types/3/versions/1/#/definitions/root",
        UNRESOLVED_SCHEMA["definitions"]["root"],
        "http://localhost:5000/api/v1/namespaces/1/types/3/versions/1/",
        UNRESOLVED_SCHEMA,
    )
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
            resolved_reference, _, _ = DataMigrator.resolve_references(
                unresolved_reference, set()
            )
    assert resolved_schema == resolved_reference.schema
    assert referenced_schema == resolved_reference.root


def test_complex_to_ref_migration(client: FlaskClient, app: Flask):
    source_schema = JsonSchema(
        _ROOT_URL,
        {
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
        },
    )
    target_schema = JsonSchema(
        "http://localhost:5000/api/v1/namespaces/1/types/4/versions/1/",
        UNRESOLVED_COMPLEX_SCHEMA,
    )
    data = {"one": {"one": "42", "two": 555}, "two": 42, "three": 53.23}
    updated_data = None
    with app.app_context():
        with app.test_request_context("http://localhost:5000/", method="GET"):
            updated_data = DataMigrator.migrate_data(data, source_schema, target_schema)
    assert {"one": {"one": 42, "two": 555}, "two": "42", "three": 53.23} == updated_data


def test_complex_from_ref_migration_(client: FlaskClient, app: Flask):
    source_schema = JsonSchema(
        "http://localhost:5000/api/v1/namespaces/1/types/4/versions/1/",
        UNRESOLVED_COMPLEX_SCHEMA,
    )
    target_schema = JsonSchema(
        _ROOT_URL,
        {
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
        },
    )
    data = {"one": {"one": 42, "two": 555}, "two": "42", "three": 53.23}
    updated_data = None
    with app.app_context():
        with app.test_request_context("http://localhost:5000/", method="GET"):
            updated_data = DataMigrator.migrate_data(data, source_schema, target_schema)
    assert {"one": {"one": "42", "two": 555}, "two": 42, "three": 53.23} == updated_data


def test_resolve_local_ref(client: FlaskClient, app: Flask):
    unresolved_reference = JsonSchema(
        "http://localhost:5000/api/v1/namespaces/1/types/5/versions/1/",
        UNRESOLVED_LOCAL_SCHEMA,
    )
    resolved_schema = {"type": ["integer"]}
    resolved_reference = None
    with app.app_context():
        with app.test_request_context("http://localhost:5000/", method="GET"):
            resolved_reference, _, _ = DataMigrator.resolve_references(
                unresolved_reference, set()
            )
    assert resolved_schema == resolved_reference.schema
    assert UNRESOLVED_LOCAL_SCHEMA == resolved_reference.root

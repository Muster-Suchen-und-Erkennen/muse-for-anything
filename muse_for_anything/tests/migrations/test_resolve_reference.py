from muse_for_anything.json_migrations.jsonschema_matcher import *
from muse_for_anything.json_migrations.data_migration import *

import unittest

app = None


def get_app():
    from muse_for_anything import create_app

    global app
    if app is None:
        app = create_app()
    return app


class TestMigrationReference(unittest.TestCase):

    unresolved_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "$ref": "http://localhost:5000/api/v1/namespaces/3/types/3/versions/2/#/definitions/root"
            }
        },
        "title": "Type",
    }

    unresolved_complex_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "properties": {
                    "one": {
                        "$ref": "http://localhost:5000/api/v1/namespaces/3/types/36/versions/1/#/definitions/root"
                    },
                    "three": {"type": ["number"]},
                    "two": {"type": ["string"]},
                },
                "type": ["object"],
            }
        },
        "title": "Type",
    }

    unresolved_local_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {"$ref": "#/definitions/1"},
            "1": {"type": ["integer"]},
        },
        "title": "Type",
    }

    def test_resolve_ref(self):
        current_app = get_app()
        unresolved_reference = self.unresolved_schema["definitions"]["root"]
        resolved_schema = {"minimum": 1, "type": ["integer", "null"]}
        resolved_reference = None
        with current_app.app_context():
            with current_app.test_request_context("http://localhost:5000/", method="GET"):
                resolved_reference = resolve_schema_reference(
                    unresolved_reference, self.unresolved_schema
                )
        self.assertEqual(resolved_schema, resolved_reference)

    def test_complex_to_ref_migration(self):
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
        current_app = get_app()
        data = {"one": {"one": "42", "two": 555}, "two": 42, "three": 53.23}
        updated_data = None
        with current_app.app_context():
            with current_app.test_request_context("http://localhost:5000/", method="GET"):
                updated_data = migrate_data(
                    data, source_schema, self.unresolved_complex_schema
                )
        self.assertEqual(
            {"one": {"one": 42, "two": 555}, "two": "42", "three": 53.23}, updated_data
        )

    def test_complex_from_ref_migration_(self):
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
        current_app = get_app()
        data = {"one": {"one": 42, "two": 555}, "two": "42", "three": 53.23}
        updated_data = None
        with current_app.app_context():
            with current_app.test_request_context("http://localhost:5000/", method="GET"):
                updated_data = migrate_data(
                    data, self.unresolved_complex_schema, target_schema
                )
        self.assertEqual(
            {"one": {"one": "42", "two": 555}, "two": 42, "three": 53.23}, updated_data
        )

    def test_resolve_local_ref(self):
        current_app = get_app()
        unresolved_reference = self.unresolved_local_schema["definitions"]["root"]
        resolved_schema = {"type": ["integer"]}
        resolved_reference = None
        with current_app.app_context():
            with current_app.test_request_context("http://localhost:5000/", method="GET"):
                resolved_reference = resolve_schema_reference(
                    unresolved_reference, self.unresolved_local_schema
                )
        self.assertEqual(resolved_schema, resolved_reference)


if __name__ == "__main__":
    unittest.main()

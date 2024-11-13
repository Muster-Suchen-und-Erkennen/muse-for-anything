from muse_for_anything.json_migrations.data_migration import *

import unittest


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
        unresolved_reference = self.unresolved_schema["definitions"]["root"]
        resolved_schema = {"minimum": 1, "type": ["integer", "null"]}
        resolved_reference = resolve_schema_reference(
            unresolved_reference, self.unresolved_schema
        )
        self.assertEqual(resolved_schema, resolved_reference)

    def test_resolve_local_ref(self):
        unresolved_reference = self.unresolved_local_schema["definitions"]["root"]
        resolved_schema = {"type": ["integer"]}
        resolved_reference = resolve_schema_reference(
            unresolved_reference, self.unresolved_local_schema
        )
        self.assertEqual(resolved_schema, resolved_reference)


if __name__ == "__main__":
    unittest.main()

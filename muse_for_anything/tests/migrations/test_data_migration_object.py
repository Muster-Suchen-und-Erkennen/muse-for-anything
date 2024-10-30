from muse_for_anything.json_migrations.data_migration import *

import unittest


class TestMigrationToObject(unittest.TestCase):

    target_schema_simple_string = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "properties": {"stringprop": {"type": ["string"]}},
                "type": ["object"],
            }
        },
        "title": "Type",
    }

    target_schema_simple_number = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "properties": {"numberprop": {"type": ["number"]}},
                "type": ["object"],
            }
        },
        "title": "Type",
    }

    target_schema_complex = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "properties": {
                    "one": {"type": ["integer"]},
                    "three": {"type": ["boolean"]},
                    "two": {"type": ["string"]},
                },
                "type": ["object"],
            }
        },
        "title": "Type",
    }

    def test_from_str_to_object(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "15"
        updated_data = migrate_data(
            data, source_schema, self.target_schema_simple_string
        )
        self.assertEqual({"stringprop": "15"}, updated_data)

    def test_from_str_to_object_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "hello world!"
        updated_data = migrate_data(data, source_schema, self.target_schema_complex)
        self.assertEqual("hello world!", updated_data)

    def test_from_bool_to_object(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data = True
        updated_data = migrate_data(
            data, source_schema, self.target_schema_simple_number
        )
        self.assertEqual({"numberprop": 1.0}, updated_data)

    def test_from_bool_to_object_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data = False
        updated_data = migrate_data(data, source_schema, self.target_schema_complex)
        self.assertEqual(False, updated_data)

    def test_from_int_to_object(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data = 1944
        updated_data = migrate_data(
            data, source_schema, self.target_schema_simple_string
        )
        self.assertEqual({"stringprop": "1944"}, updated_data)

    def test_from_int_to_object_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data = 1944
        updated_data = migrate_data(data, source_schema, self.target_schema_complex)
        self.assertEqual(1944, updated_data)

    def test_from_number_to_object(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data = 24.987
        updated_data = migrate_data(
            data, source_schema, self.target_schema_simple_number
        )
        self.assertEqual({"numberprop": 24.987}, updated_data)

    def test_from_number_to_object_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data = 45.8763
        updated_data = migrate_data(data, source_schema, self.target_schema_complex)
        self.assertEqual(45.8763, updated_data)

    def test_to_object_error(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {"$ref": "#/definitions/0"},
                "0": {"type": ["integer"]},
            },
            "title": "Type",
        }
        data = 1944
        with self.assertRaises(ValueError):
            migrate_data(data, source_schema, self.target_schema_complex)


if __name__ == "__main__":
    unittest.main()

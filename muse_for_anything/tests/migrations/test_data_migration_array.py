from muse_for_anything.json_migrations.data_migration import *

import unittest

from muse_for_anything.json_migrations.jsonschema_matcher import match_schema


class TestMigrationToArray(unittest.TestCase):

    target_schema_number = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "arrayType": "array",
                "items": {"type": ["number"]},
                "type": ["array"],
            }
        },
        "title": "Type",
    }

    target_schema_string = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "arrayType": "array",
                "items": {"type": ["string"]},
                "type": ["array"],
            }
        },
        "title": "Type",
    }

    target_schema_boolean = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "arrayType": "array",
                "items": {"type": ["boolean"]},
                "type": ["array"],
            }
        },
        "title": "Type",
    }

    target_schema_integer = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "arrayType": "array",
                "items": {"type": ["integer"]},
                "type": ["array"],
            }
        },
        "title": "Type",
    }

    def test_from_str_to_array_number(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "15"
        updated_data = migrate_data(data, source_schema, self.target_schema_number)
        self.assertEqual([15.0], updated_data)

    def test_from_str_to_array_string(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "15"
        updated_data = migrate_data(data, source_schema, self.target_schema_string)
        self.assertEqual(["15"], updated_data)

    def test_from_str_to_array_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "hello world!"
        with self.assertRaises(ValueError):
            migrate_data(data, source_schema, self.target_schema_number)

    def test_from_bool_to_array_number(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data = True
        updated_data = migrate_data(data, source_schema, self.target_schema_number)
        self.assertEqual([1.0], updated_data)

    def test_from_bool_to_array_string(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data = False
        updated_data = migrate_data(data, source_schema, self.target_schema_string)
        self.assertEqual(["False"], updated_data)

    def test_from_int_to_array_number(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data = 1944
        updated_data = migrate_data(data, source_schema, self.target_schema_number)
        self.assertEqual([1944.0], updated_data)

    def test_from_int_to_array_string(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data = 1944
        updated_data = migrate_data(data, source_schema, self.target_schema_string)
        self.assertEqual(["1944"], updated_data)

    def test_from_number_to_array_boolean(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data = 24.987
        updated_data = migrate_data(data, source_schema, self.target_schema_boolean)
        self.assertEqual([True], updated_data)

    def test_from_number_to_array_integer(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data = 45.8763
        updated_data = migrate_data(data, source_schema, self.target_schema_integer)
        self.assertEqual([45], updated_data)

    def test_from_tuple_to_array(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "tuple",
                    "items": [
                        {"type": ["number"]},
                        {"type": ["integer"]},
                        {"type": ["integer"]},
                        {"type": ["boolean"]},
                    ],
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        data = [0.0, 54, 42, True]
        updated_data = migrate_data(data, source_schema, self.target_schema_string)
        self.assertEqual(["0.0", "54", "42", "True"], updated_data)

    def test_from_array_to_array_simple_one(self):
        data = [False, True, False, True]
        updated_data = migrate_data(
            data, self.target_schema_boolean, self.target_schema_integer
        )
        self.assertEqual([0, 1, 0, 1], updated_data)

    def test_from_array_to_array_simple_two(self):
        data = [42, 187, 1944, 555, 968, 6742]
        updated_data = migrate_data(
            data, self.target_schema_integer, self.target_schema_string
        )
        self.assertEqual(["42", "187", "1944", "555", "968", "6742"], updated_data)

    def test_to_array_invalid(self):
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
        migration_plan = match_schema(source_schema, self.target_schema_boolean)
        self.assertEqual(True, migration_plan["unsupported_conversion"])


if __name__ == "__main__":
    unittest.main()

from muse_for_anything.json_migrations.data_migration import *

import unittest


class TestMigrationToTuple(unittest.TestCase):

    target_schema_simple_string = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "arrayType": "tuple",
                "items": [
                    {"type": ["string"]},
                ],
                "type": ["array"],
            }
        },
        "title": "Type",
    }

    target_schema_simple_integer = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {
            "root": {
                "arrayType": "tuple",
                "items": [
                    {"type": ["integer"]},
                ],
                "type": ["array"],
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
                "arrayType": "tuple",
                "items": [
                    {"type": ["boolean"]},
                    {"type": ["integer"]},
                    {"type": ["string"]},
                ],
                "type": ["array"],
            }
        },
        "title": "Type",
    }

    def test_from_str_to_tuple(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "15"
        updated_data = migrate_data(data, source_schema, self.target_schema_simple_string)
        self.assertEqual(["15"], updated_data)

    def test_from_str_to_tuple_invalid(self):
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

    def test_from_bool_to_tuple(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data = True
        updated_data = migrate_data(
            data, source_schema, self.target_schema_simple_integer
        )
        self.assertEqual([1], updated_data)

    def test_from_bool_to_tuple_invalid(self):
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

    def test_from_int_to_tuple(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data = 1944
        updated_data = migrate_data(data, source_schema, self.target_schema_simple_string)
        self.assertEqual(["1944"], updated_data)

    def test_from_int_to_tuple_invalid(self):
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

    def test_from_number_to_tuple(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data = 24.987
        updated_data = migrate_data(
            data, source_schema, self.target_schema_simple_integer
        )
        self.assertEqual([24], updated_data)

    def test_from_number_to_tuple_invalid(self):
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

    def test_from_tuple_to_tuple_type_change(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "tuple",
                    "items": [
                        {"type": ["integer"]},
                        {"type": ["integer"]},
                        {"type": ["string"]},
                    ],
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        data = [0, 54, "hello world"]
        updated_data = migrate_data(data, source_schema, self.target_schema_complex)
        self.assertEqual([False, 54, "hello world"], updated_data)

    def test_to_tuple_error(self):
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

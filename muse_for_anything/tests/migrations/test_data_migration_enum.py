from muse_for_anything.json_migrations.data_migration import *

import unittest


class TestMigrationToInteger(unittest.TestCase):

    target_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {"root": {"enum": [False, None, 1944, "hello world"]}},
        "title": "Type",
    }

    def test_from_array_to_enum_valid(self):
        source_schema = {
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
        data = [False]
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_array_to_enum_invalid(self):
        source_schema = {
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
        data = [13, 16, 18]
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual([13, 16, 18], updated_data)

    def test_from_boolean_to_enum_valid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data = False
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_boolean_to_enum_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data = True
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_enum_to_enum_valid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": [False, "hello world"]}},
            "title": "Type",
        }
        data = False
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_enum_to_enum_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": [True, None, 1944, "hello world"]}},
            "title": "Type",
        }
        data = True
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_integer_to_enum_valid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data = 1944
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(1944, updated_data)

    def test_from_integer_to_enum_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data = 944
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(944, updated_data)

    def test_from_number_to_enum_valid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data = 1944.4491
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(1944, updated_data)

    def test_from_number_to_enum_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data = 123456789
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(123456789, updated_data)

    def test_from_object_to_enum_invalid(self):
        source_schema = {
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
        data = {"one": 42, "three": True, "two": "Hello World!"}
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(
            {"one": 42, "three": True, "two": "Hello World!"},
            updated_data,
        )

    def test_from_string_to_enum_valid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "hello world"
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual("hello world", updated_data)

    def test_from_string_to_enum_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "hellow orld"
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual("hellow orld", updated_data)

    def test_from_tuple_to_enum_valid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "tuple",
                    "items": [{"type": ["string"]}],
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        data = "hello world"
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual("hello world", updated_data)

    def test_from_tuple_to_enum_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "tuple",
                    "items": [{"type": ["string"]}, {"type": ["float"]}],
                    "type": ["array"],
                }
            },
            "title": "Type",
        }

        data = ["hello world", 42.42]
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(["hello world", 42.42], updated_data)

    def test_to_enum_error(self):
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
            migrate_data(data, source_schema, self.target_schema)


if __name__ == "__main__":
    unittest.main()

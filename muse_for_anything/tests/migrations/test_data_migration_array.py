from muse_for_anything.json_migrations.data_migration import *

import unittest


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

    def test_from_str_to_list_number(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data_object = "15"
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema_number
        )
        self.assertEqual([15.0], updated_data_object)

    def test_from_str_to_list_string(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data_object = "15"
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema_string
        )
        self.assertEqual(["15"], updated_data_object)

    def test_from_str_to_list_error(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data_object = "hello world!"
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema_number
        )
        self.assertEqual("hello world!", updated_data_object)

    def test_from_bool_to_list_number(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data_object = True
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema_number
        )
        self.assertEqual([1.0], updated_data_object)

    def test_from_bool_to_list_string(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data_object = False
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema_string
        )
        self.assertEqual(["False"], updated_data_object)

    def test_from_int_to_list_number(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data_object = 1944
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema_number
        )
        self.assertEqual([1944.0], updated_data_object)

    def test_from_int_to_list_string(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data_object = 1944
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema_string
        )
        self.assertEqual(["1944"], updated_data_object)

    def test_from_number_to_list_boolean(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data_object = 24.987
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema_boolean
        )
        self.assertEqual([True], updated_data_object)

    def test_from_number_to_list_integer(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data_object = 45.8763
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema_integer
        )
        self.assertEqual([45], updated_data_object)

    def test_to_array_error(self):
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
        data_object = 1944
        with self.assertRaises(ValueError):
            migrate_object(data_object, source_schema, self.target_schema_number)


if __name__ == "__main__":
    unittest.main()

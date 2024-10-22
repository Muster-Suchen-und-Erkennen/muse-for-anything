from muse_for_anything.json_migrations.data_migration import *

import unittest


class TestMigrationToString(unittest.TestCase):

    target_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {"root": {"type": ["string"]}},
        "title": "Type",
    }

    def test_from_int_to_str(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data_object = 1944
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual("1944", updated_data_object)

    def test_from_number_to_str(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data_object = 3.14159265359
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual("3.14159265359", updated_data_object)

    def test_from_bool_to_str(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data_object = True
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual("True", updated_data_object)

    def test_from_enum_to_str_one(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
            "title": "Type",
        }
        data_object = 1234.56789
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual("1234.56789", updated_data_object)

    def test_from_enum_to_str_two(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
            "title": "Type",
        }
        data_object = "hello world"
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual("hello world", updated_data_object)

    def test_from_array_to_str(self):
        source_schema = {
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
        data_object = [2, 9, 44]
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual("[2, 9, 44]", updated_data_object)

    def test_from_obj_to_str(self):
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
        data_object = {"one": 42, "three": True, "two": "Hello World!"}
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual(
            "{'one': 42, 'three': True, 'two': 'Hello World!'}",
            updated_data_object,
        )

    def test_from_tuple_to_str(self):
        source_schema = {
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
        data_object = [True, 12, "Hello"]
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual("[True, 12, 'Hello']", updated_data_object)

    def test_from_res_ref_to_str(self):
        pass

    def test_from_schema_ref_to_str(self):
        pass

    def test_to_string_error(self):
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
            migrate_object(data_object, source_schema, self.target_schema)


if __name__ == "__main__":
    unittest.main()

from muse_for_anything.json_migrations.data_migration import *

import unittest

from muse_for_anything.json_migrations.jsonschema_matcher import match_schema


class TestMigrationToNumber(unittest.TestCase):

    target_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {"root": {"type": ["number"]}},
        "title": "Type",
    }

    def test_from_str_to_number_valid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "15.8765"
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(15.8765, updated_data)

    def test_from_str_to_number_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "HELLO WORLD!"
        with self.assertRaises(ValueError):
            migrate_data(data, source_schema, self.target_schema)

    def test_from_bool_to_number_true(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data = True
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(1, updated_data)

    def test_from_bool_to_number_false(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data = False
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(0, updated_data)

    def test_from_int_to_number(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data = 2984
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(2984.0, updated_data)

    def test_from_enum_to_number_valid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
            "title": "Type",
        }
        data = 1234.56789
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(1234.56789, updated_data)

    def test_from_enum_to_number_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
            "title": "Type",
        }
        data = "hello world"
        with self.assertRaises(ValueError):
            migrate_data(data, source_schema, self.target_schema)

    def test_from_array_to_number_array_valid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "array",
                    "items": {"type": ["float"]},
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        data = [13.4334]
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(13.4334, updated_data)

    def test_from_array_to_number_array_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "array",
                    "items": {"type": ["float"]},
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        data = [13.21, 14, 15.142]
        with self.assertRaises(ValueError):
            migrate_data(data, source_schema, self.target_schema)

    def test_from_obj_to_number_simple_object(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {
                        "intprop": {
                            "type": ["string"],
                        },
                    },
                    "type": ["object"],
                }
            },
            "title": "Type",
        }
        data = {"intprop": "42"}
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(42.0, updated_data)

    def test_from_obj_to_number_no_object(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {},
                    "type": ["object"],
                }
            },
            "title": "Type",
        }
        data = {}
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(0.0, updated_data)

    def test_from_obj_to_number_complex_object(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {
                        "numberprop": {
                            "type": ["number"],
                        },
                        "stringprop": {
                            "type": ["string"],
                        },
                    },
                    "type": ["object"],
                }
            },
            "title": "Type",
        }
        data = {"numberprop": 42.213, "stringprop": "this is not an integer"}
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(42.213, updated_data)

    def test_from_obj_to_number_complex_object_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {
                        "stringpropone": {
                            "type": ["string"],
                        },
                        "stringproptwo": {
                            "type": ["string"],
                        },
                    },
                    "type": ["object"],
                }
            },
            "title": "Type",
        }
        data = {
            "stringpropone": "this is a test",
            "stringproptwo": "hello world",
        }
        with self.assertRaises(ValueError):
            migrate_data(data, source_schema, self.target_schema)

    def test_from_tuple_to_number_valid(self):
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
        data = ["hello world", 123.456]
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(123.456, updated_data)

    def test_from_tuple_to_number_invalid(self):
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
        data = [True, False, "hello world"]
        with self.assertRaises(ValueError):
            migrate_data(data, source_schema, self.target_schema)

    def test_from_res_ref_to_number(self):
        pass

    def test_from_schema_ref_to_number(self):
        pass

    def test_to_number_error(self):
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
        self.assertEqual(
            False,
            match_schema(
                (source_schema, self.target_schema), source_schema, self.target_schema
            ),
        )


if __name__ == "__main__":
    unittest.main()

from muse_for_anything.json_migrations.data_migration import *

import unittest


class TestMigrationToInteger(unittest.TestCase):

    target_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {"root": {"type": ["integer"]}},
        "title": "Type",
    }

    def test_valid_from_str_to_int_one(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "15"
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(15, updated_data)

    def test_valid_from_str_to_int_two(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "15.79"
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(15, updated_data)

    def test_invalid_from_str_to_int(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "HELLO WORLD!"
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual("HELLO WORLD!", updated_data)

    def test_from_bool_to_int_true(self):
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

    def test_from_bool_to_int_false(self):
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

    def test_from_number_to_int(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data = 5.7436555
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(5, updated_data)

    def test_from_enum_to_int_valid(self):  #
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
            "title": "Type",
        }
        data = 1234
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(1234, updated_data)

    def test_from_enum_to_int_invalid(self):  #
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
            "title": "Type",
        }
        data = "hello world"
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual("hello world", updated_data)

    def test_from_array_to_int_valid(self):
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
        data = [13]
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(13, updated_data)

    def test_from_array_to_int_invalid(self):
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
        data = [13, 14, 15]
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual([13, 14, 15], updated_data)

    def test_from_obj_to_int_simple_object(self):
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
        self.assertEqual(42, updated_data)

    def test_from_obj_to_int_no_object(self):
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
        self.assertEqual(0, updated_data)

    def test_from_obj_to_int_complex_object(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {
                        "intprop": {
                            "type": ["integer"],
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
        data = {"intprop": 42, "stringprop": "this is not an integer"}
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(42, updated_data)

    def test_from_obj_to_bool_complex_object_invalid(self):
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
        data = {"stringpropone": "this is a test", "stringproptwo": "hello world"}
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(
            {"stringpropone": "this is a test", "stringproptwo": "hello world"},
            updated_data,
        )

    def test_from_tuple_to_int_valid(self):
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
        self.assertEqual(123, updated_data)

    def test_from_tuple_to_int_invalid(self):
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
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual([True, False, "hello world"], updated_data)

    def test_from_res_ref_to_int(self):
        pass

    def test_from_schema_ref_to_int(self):
        pass

    def test_to_integer_error(self):
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

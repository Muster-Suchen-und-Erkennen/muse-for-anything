from muse_for_anything.json_migrations.data_migration import *

import unittest

from muse_for_anything.json_migrations.jsonschema_matcher import match_schema


class TestMigrationToInteger(unittest.TestCase):

    target_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {"root": {"type": ["boolean"]}},
        "title": "Type",
    }

    def test_from_str_to_bool_true(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = "15"
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_str_to_bool_false(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data = ""
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_int_to_bool_true(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data = 23
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_int_to_bool_false(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data = 0
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_number_to_bool(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data = 5.7436555
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_enum_to_bool_true(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
            "title": "Type",
        }
        data = True
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_enum_to_bool_false(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
            "title": "Type",
        }
        data = None
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_enum_to_bool_string(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
            "title": "Type",
        }
        data = "all"
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_array_to_bool_true(self):
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
        data = [2, 9, 44]
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_array_to_bool_false(self):
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
        data = []
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_obj_to_bool_simple_object(self):
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
                    },
                    "type": ["object"],
                }
            },
            "title": "Type",
        }
        data = {"intprop": 42}
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_obj_to_bool_no_object(self):
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
        self.assertEqual(False, updated_data)

    def test_from_obj_to_bool_complex_object_true(self):
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
                        "boolprop": {
                            "type": ["boolean"],
                        },
                    },
                    "type": ["object"],
                }
            },
            "title": "Type",
        }
        data = {"intprop": 42, "boolprop": True}
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_obj_to_bool_complex_object_false(self):
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
                        "boolprop": {
                            "type": ["boolean"],
                        },
                    },
                    "type": ["object"],
                }
            },
            "title": "Type",
        }
        data = {"intprop": 42, "boolprop": False}
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_obj_to_bool_complex_object_invalid(self):
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
        data = {"intprop": 42, "stringprop": "hello world"}
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(
            {"intprop": 42, "stringprop": "hello world"},
            updated_data,
        )

    def test_from_tuple_to_bool_true(self):
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
        data = [True, 12, "Hello"]
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_tuple_to_bool_false(self):
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
        data = [False, 42, "Test"]
        updated_data = migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_res_ref_to_bool(self):
        pass

    def test_from_schema_ref_to_bool(self):
        pass

    def test_to_boolean_error(self):
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
            match_schema(source_schema, self.target_schema),
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from muse_for_anything.json_migrations import DataMigrator, JsonSchema

_ROOT_URL = "http://localhost:5000/test-schemas/"


class TestMigrationToInteger(unittest.TestCase):

    target_schema = JsonSchema(
        _ROOT_URL,
        {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        },
    )

    def test_valid_from_str_to_int_one(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {"root": {"type": ["string"]}},
                "title": "Type",
            },
        )
        data = "15"
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(15, updated_data)

    def test_from_str_to_int_two_valid(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {"root": {"type": ["string"]}},
                "title": "Type",
            },
        )
        data = "15.79"
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(15, updated_data)

    def test_from_str_to_int_invalid(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {"root": {"type": ["string"]}},
                "title": "Type",
            },
        )
        data = "HELLO WORLD!"
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_bool_to_int_true(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {"root": {"type": ["boolean"]}},
                "title": "Type",
            },
        )
        data = True
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(1, updated_data)

    def test_from_bool_to_int_false(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {"root": {"type": ["boolean"]}},
                "title": "Type",
            },
        )
        data = False
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(0, updated_data)

    def test_from_number_to_int(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {"root": {"type": ["number"]}},
                "title": "Type",
            },
        )
        data = 5.7436555
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(5, updated_data)

    def test_from_enum_to_int_valid(self):  #
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
                "title": "Type",
            },
        )
        data = 1234
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(1234, updated_data)

    def test_from_enum_to_int_invalid(self):  #
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
                "title": "Type",
            },
        )
        data = "hello world"
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_array_to_int_valid(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = [13]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(13, updated_data)

    def test_from_array_to_int_empty(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = []
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_long_array_to_int(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = [13, 14, 15]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(13, updated_data)

    def test_from_obj_to_int_simple_object(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {
                    "root": {
                        "properties": {
                            "stringprop": {
                                "type": ["string"],
                            },
                        },
                        "type": ["object"],
                    }
                },
                "title": "Type",
            },
        )
        data = {"stringprop": "42.21"}
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(42, updated_data)

    def test_from_obj_to_int_no_object(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = {}
        self.assertFalse(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_obj_to_int_complex_object_invalid(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = {"stringpropone": "this is a test", "stringproptwo": "hello world"}
        self.assertFalse(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_tuple_to_int_valid(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {
                    "root": {
                        "arrayType": "tuple",
                        "items": [{"type": ["number"]}],
                        "type": ["array"],
                    }
                },
                "title": "Type",
            },
        )
        data = [123.456]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(123, updated_data)

    def test_from_long_tuple_to_int(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {
                    "root": {
                        "arrayType": "tuple",
                        "items": [{"type": ["string"]}, {"type": ["number"]}],
                        "type": ["array"],
                    }
                },
                "title": "Type",
            },
        )
        data = [True, False, "hello world"]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(1, updated_data)


if __name__ == "__main__":
    unittest.main()

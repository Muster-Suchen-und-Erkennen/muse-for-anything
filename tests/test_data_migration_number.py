import unittest

from muse_for_anything.json_migrations import DataMigrator, JsonSchema

_ROOT_URL = "http://localhost:5000/test-schemas/"


class TestMigrationToNumber(unittest.TestCase):

    target_schema = JsonSchema(
        _ROOT_URL,
        {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        },
    )

    def test_from_str_to_number_valid(self):
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
        data = "15.8765"
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(15.8765, updated_data)

    def test_from_str_to_number_invalid(self):
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

    def test_from_bool_to_number_true(self):
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

    def test_from_bool_to_number_false(self):
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

    def test_from_int_to_number(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {"root": {"type": ["integer"]}},
                "title": "Type",
            },
        )
        data = 2984
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(2984.0, updated_data)

    def test_from_enum_to_number_valid(self):
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
        data = 1234.56789
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(1234.56789, updated_data)

    def test_from_enum_to_number_invalid(self):
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

    def test_from_array_to_number_array_valid(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = [13.4334]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(13.4334, updated_data)

    def test_from_array_to_number_empty(self):
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

    def test_from_long_array_to_number(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = [13.21, 14, 15.142]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(13.21, updated_data)

    def test_from_obj_to_number_simple_object(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = {"intprop": "42"}
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(42.0, updated_data)

    def test_from_obj_to_number_no_object(self):
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

    def test_from_obj_to_number_complex_object_invalid(self):
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
        data = {
            "stringpropone": "this is a test",
            "stringproptwo": "hello world",
        }
        self.assertFalse(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_tuple_to_number_valid(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = ["3.1587945"]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(3.1587945, updated_data)

    def test_from_long_tuple_to_number(self):
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

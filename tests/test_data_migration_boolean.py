import unittest

from muse_for_anything.json_migrations import DataMigrator, JsonSchema

_ROOT_URL = "http://localhost:5000/test-schemas/"


class TestMigrationToBoolean(unittest.TestCase):

    target_schema = JsonSchema(
        _ROOT_URL,
        {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        },
    )

    def test_from_str_to_bool_true(self):
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
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_str_to_bool_false(self):
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
        data = ""
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_int_to_bool_true(self):
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
        data = 23
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_int_to_bool_false(self):
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
        data = 0
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_number_to_bool(self):
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
        self.assertEqual(True, updated_data)

    def test_from_enum_to_bool_true(self):
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
        data = True
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_enum_to_bool_false(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {"root": {"enum": ["all", True, 1234.56, False, None]}},
                "title": "Type",
            },
        )
        data = False
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_enum_to_bool_invalid(self):
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
        data = None
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_enum_to_bool_string(self):
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
        data = "all"
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_array_to_bool_true(self):
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
        data = [2, 9, 44]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_array_to_bool_false(self):
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
        data = [0]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_obj_to_bool_simple_object(self):
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
                                "type": ["integer"],
                            },
                        },
                        "type": ["object"],
                    }
                },
                "title": "Type",
            },
        )
        data = {"intprop": 42}
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_obj_to_bool_no_object(self):
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

    def test_from_obj_to_bool_complex_object(self):
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
            },
        )
        data = {"intprop": 42, "boolprop": False}
        self.assertFalse(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_obj_to_bool_complex_object_invalid(self):
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
            },
        )
        data = {"intprop": 42, "stringprop": "hello world"}
        self.assertFalse(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_tuple_to_bool_true_one(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = [True, 12, "Hello"]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(True, updated_data)

    def test_from_tuple_to_bool_true_two(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = [False, 42, "Test"]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)


if __name__ == "__main__":
    unittest.main()

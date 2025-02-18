import unittest

from muse_for_anything.json_migrations import DataMigrator, JsonSchema

_ROOT_URL = "http://localhost:5000/test-schemas/"


class TestMigrationToEnum(unittest.TestCase):

    target_schema = JsonSchema(
        _ROOT_URL,
        {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": [False, None, 1944.123, "hello world"]}},
            "title": "Type",
        },
    )

    def test_from_simple_array_to_enum_invalid(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = [1944]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_array_to_enum_invalid(self):
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
        data = [13, 16, 18]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_boolean_to_enum_valid(self):
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
        self.assertEqual(False, updated_data)

    def test_from_boolean_to_enum_not_exact(self):
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
        self.assertEquals(1944.123, updated_data)

    def test_from_enum_to_enum_valid(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {"root": {"enum": [False, "hello world"]}},
                "title": "Type",
            },
        )
        data = False
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(False, updated_data)

    def test_from_enum_to_enum_invalid(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
                "$ref": "#/definitions/root",
                "$schema": "http://json-schema.org/draft-07/schema#",
                "abstract": False,
                "definitions": {"root": {"enum": [True, None, 1944, "hello world"]}},
                "title": "Type",
            },
        )
        data = 1944
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_integer_to_enum_invalid(self):
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
        data = 1944
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_integer_to_enum_invalid_two(self):
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
        data = 944
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_number_to_enum_valid(self):
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
        data = 1944.123
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual(1944.123, updated_data)

    def test_from_number_to_enum_invalid(self):
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
        data = 123456789
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_object_to_enum_invalid(self):
        source_schema = JsonSchema(
            _ROOT_URL,
            {
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
            },
        )
        data = {"one": 42, "three": True, "two": "Hello World!"}
        self.assertFalse(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_string_to_enum_valid(self):
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
        data = "hello world"
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual("hello world", updated_data)

    def test_from_string_to_enum_invalid(self):
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
        data = "hellow orld"
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)

    def test_from_tuple_to_enum_valid(self):
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
        data = ["hello world"]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        updated_data = DataMigrator.migrate_data(data, source_schema, self.target_schema)
        self.assertEqual("hello world", updated_data)

    def test_from_tuple_to_enum_invalid(self):
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

        data = ["HELLO WORLD", 42.42]
        self.assertTrue(
            DataMigrator.check_schema_changes(source_schema, self.target_schema)
        )
        with self.assertRaises(ValueError):
            DataMigrator.migrate_data(data, source_schema, self.target_schema)


if __name__ == "__main__":
    unittest.main()

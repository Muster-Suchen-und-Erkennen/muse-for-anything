from muse_for_anything.json_migrations.data_migration import migrate_data
import unittest


class TestRecursiveMigration(unittest.TestCase):

    def test_object_to_object(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {
                        "one": {
                            "properties": {
                                "one": {"type": ["boolean"]},
                                "two": {"type": ["string"]},
                            },
                            "type": ["object"],
                        },
                        "three": {"type": ["integer"]},
                        "two": {"type": ["string"]},
                    },
                    "type": ["object"],
                }
            },
            "title": "Type",
        }
        target_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {
                        "one": {
                            "properties": {
                                "one": {"type": ["integer"]},
                                "two": {"type": ["integer"]},
                            },
                            "type": ["object"],
                        },
                        "three": {"type": ["number"]},
                        "two": {"type": ["string"]},
                    },
                    "type": ["object"],
                }
            },
            "title": "Type",
        }
        data = {"one": {"one": True, "two": "3"}, "two": "hello world", "three": 1944}
        updated_data = migrate_data(data, source_schema, target_schema)
        self.assertEqual(
            {"one": {"one": 1, "two": 3}, "two": "hello world", "three": 1944.0},
            updated_data,
        )

    def test_array_to_array(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "array",
                    "items": {
                        "arrayType": "array",
                        "items": {"type": ["boolean"]},
                        "type": ["array"],
                    },
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        target_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "array",
                    "items": {
                        "arrayType": "array",
                        "items": {"type": ["integer"]},
                        "type": ["array"],
                    },
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        data = [
            [False, True, False],
            [False, False, False],
            [True, True, True, False, False, True],
        ]
        updated_data = migrate_data(data, source_schema, target_schema)
        self.assertEqual(
            [
                [0, 1, 0],
                [0, 0, 0],
                [1, 1, 1, 0, 0, 1],
            ],
            updated_data,
        )


if __name__ == "__main__":
    unittest.main()

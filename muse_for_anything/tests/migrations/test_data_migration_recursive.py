from muse_for_anything.json_migrations.data_migration import migrate_data
import unittest

from muse_for_anything.json_migrations.jsonschema_validator import validate_schema


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

    def test_array_to_array_one(self):
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

    def test_array_to_array_two(self):
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
                    "items": {"type": ["integer"]},
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        data = [
            [False],
            [False],
            [True],
        ]
        updated_data = migrate_data(data, source_schema, target_schema)
        self.assertEqual(
            [0, 0, 1],
            updated_data,
        )

    def test_array_to_array_three(self):
        source_schema = {
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
        data = [True, False, False, True]
        updated_data = migrate_data(data, source_schema, target_schema)
        self.assertEqual(
            [[1], [0], [0], [1]],
            updated_data,
        )

    def test_tuple_to_tuple_one(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "tuple",
                    "items": [
                        {
                            "arrayType": "array",
                            "items": {"type": ["integer"]},
                            "type": ["array"],
                        },
                        {"type": ["integer"]},
                        {"type": ["string", "null"]},
                    ],
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
                    "arrayType": "tuple",
                    "items": [
                        {
                            "arrayType": "array",
                            "items": {"type": ["string"]},
                            "type": ["array"],
                        },
                        {"type": ["integer"]},
                        {"type": ["string", "null"]},
                    ],
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        data = [[1, 2, 3, 4, 5], 42, "hello world"]
        updated_data = migrate_data(data, source_schema, target_schema)
        self.assertEqual(
            [["1", "2", "3", "4", "5"], 42, "hello world"],
            updated_data,
        )

    def test_tuple_to_tuple_two(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "tuple",
                    "items": [
                        {
                            "arrayType": "array",
                            "items": {
                                "arrayType": "tuple",
                                "items": [
                                    {"type": ["boolean"]},
                                    {"type": ["integer"]},
                                    {"type": ["string", "null"]},
                                ],
                                "type": ["array"],
                            },
                            "type": ["array"],
                        },
                        {"type": ["integer"]},
                    ],
                    "type": ["array"],
                },
            },
            "title": "Type",
        }
        target_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "tuple",
                    "items": [
                        {
                            "arrayType": "array",
                            "items": {
                                "arrayType": "tuple",
                                "items": [
                                    {"type": ["integer"]},
                                    {"type": ["boolean"]},
                                    {"type": ["string", "null"]},
                                ],
                                "type": ["array"],
                            },
                            "type": ["array"],
                        },
                        {"type": ["string"]},
                    ],
                    "type": ["array"],
                },
            },
            "title": "Type",
        }
        data = [[[False, 0, "hi"], [True, 3, "bye"], [False, 9, "sun"]], 42]
        updated_data = migrate_data(data, source_schema, target_schema)
        self.assertEqual(
            [[[0, False, "hi"], [1, True, "bye"], [0, True, "sun"]], "42"],
            updated_data,
        )

    def test_self_recursive_schema(self):
        unresolved_local_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {"$ref": "#/definitions/1"},
                "1": {"$ref": "#/definitions/1"},
            },
            "title": "Type",
        }
        valid = validate_schema(unresolved_local_schema, unresolved_local_schema)
        self.assertEqual(True, valid)


if __name__ == "__main__":
    unittest.main()

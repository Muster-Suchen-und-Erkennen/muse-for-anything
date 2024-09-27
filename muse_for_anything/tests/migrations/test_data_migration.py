from muse_for_anything.json_migrations.data_migration import migrate_object
from muse_for_anything.json_migrations.jsonschema_matcher import match_schema

import unittest

# TODO a lot more cases


class TestMigrationSameType(unittest.TestCase):

    def test_migration_same_type(self):
        source_schema = """
            {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": false,
            "definitions": {
                "root": {
                "type": [
                    "string"
                ]
                }
            },
            "title": "Type"
            }
            """
        target_schema = """
            {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": false,
            "definitions": {
                "root": {
                "type": [
                    "string"
                ]
                }
            },
            "title": "StringType"
            }
            """
        transformations = match_schema(source_schema, target_schema)
        self.assertEqual(["No type changes!"], transformations)


class TestMigrationToNumber(unittest.TestCase):

    target_schema = """
        {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": false,
        "definitions": {
            "root": {
            "type": [
                "number"
            ]
            }
        },
        "title": "Type"
        }
    """

    def test_valid_from_str_to_number(self):
        source_schema = """
        {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": false,
        "definitions": {
            "root": {
            "type": [
                "string"
            ]
            }
        },
        "title": "Type"
        }
        """
        data_object_valid = """
        {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": "15",
                "deletedOn": null,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "IntObject",
                    "rel": [],
                    "resourceKey": {
                        "namespaceId": "1",
                        "objectId": "13"
                    },
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/"
                }
            },
            "updatedOn": "2024-09-27T08:02:44.213790",
            "version": 1
        }
        """
        transformations = match_schema(source_schema, self.target_schema)
        updated_valid_data_object = migrate_object(
            data_object_valid, self.target_schema, transformations
        )
        self.assertEqual(15, updated_valid_data_object["data"]["data"])
        self.assertEqual(2, updated_valid_data_object["version"])

    def test_invalid_from_str_to_number(self):
        source_schema = """
        {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": false,
        "definitions": {
            "root": {
            "type": [
                "string"
            ]
            }
        },
        "title": "Type"
        }
        """
        data_object_invalid = """
        {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": "HELLO WORLD!",
                "deletedOn": null,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "IntObject",
                    "rel": [],
                    "resourceKey": {
                        "namespaceId": "1",
                        "objectId": "13"
                    },
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/"
                }
            },
            "updatedOn": "2024-09-27T08:02:44.213790",
            "version": 1
        }
        """
        transformations = match_schema(source_schema, self.target_schema)
        with self.assertRaises(ValueError):
            migrate_object(data_object_invalid, self.target_schema, transformations)

    def test_from_bool_to_number(self):
        source_schema = """
        {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": false,
        "definitions": {
            "root": {
            "type": [
                "boolean"
            ]
            }
        },
        "title": "Type"
        }
        """
        data_object_true = """
        {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": true,
                "deletedOn": null,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "IntObject",
                    "rel": [],
                    "resourceKey": {
                        "namespaceId": "1",
                        "objectId": "13"
                    },
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/"
                }
            },
            "updatedOn": "2024-09-27T08:02:44.213790",
            "version": 1
        }
        """
        data_object_false = """
        {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": false,
                "deletedOn": null,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "IntObject",
                    "rel": [],
                    "resourceKey": {
                        "namespaceId": "1",
                        "objectId": "13"
                    },
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/"
                }
            },
            "updatedOn": "2024-09-27T08:02:44.213790",
            "version": 1
        }
        """
        transformations = match_schema(source_schema, self.target_schema)
        updated_data_object_true = migrate_object(
            data_object_true, self.target_schema, transformations
        )
        updated_data_object_false = migrate_object(
            data_object_false, self.target_schema, transformations
        )
        self.assertEqual(1, updated_data_object_true["data"]["data"])
        self.assertEqual(2, updated_data_object_true["version"])
        self.assertEqual(0, updated_data_object_false["data"]["data"])
        self.assertEqual(2, updated_data_object_false["version"])

    def test_from_int_to_number(self):
        source_schema = """
            {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": false,
            "definitions": {
                "root": {
                "type": [
                    "integer"
                ]
                }
            },
            "title": "Type"
            }
            """
        data_object_true = """
            {
                "data": {
                    "createdOn": "2024-09-27T08:02:44.203024",
                    "data": 2984,
                    "deletedOn": null,
                    "description": "",
                    "name": "Object",
                    "self": {
                        "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                        "name": "IntObject",
                        "rel": [],
                        "resourceKey": {
                            "namespaceId": "1",
                            "objectId": "13"
                        },
                        "resourceType": "ont-object",
                        "schema": "http://localhost:5000/api/v1/schemas/ontology/27/"
                    }
                },
                "updatedOn": "2024-09-27T08:02:44.213790",
                "version": 1
            }
            """
        transformations = match_schema(source_schema, self.target_schema)
        updated_data_object_true = migrate_object(
            data_object_true, self.target_schema, transformations
        )
        self.assertEqual(2984.0, updated_data_object_true["data"]["data"])
        self.assertEqual(2, updated_data_object_true["version"])

    def test_from_enum_to_number(self):
        pass

    def test_from_array_to_number(self):
        pass

    def test_from_obj_to_number(self):
        pass

    def test_from_tuple_to_number(self):
        pass

    def test_from_res_ref_to_number(self):
        pass

    def test_from_schema_ref_to_number(self):
        pass


class TestMigrationToString(unittest.TestCase):

    target_schema = """
        {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": false,
        "definitions": {
            "root": {
            "type": [
                "string"
            ]
            }
        },
        "title": "Type"
        }
    """

    def test_from_int_to_str(self):
        source_schema = """
            {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": false,
            "definitions": {
                "root": {
                "type": [
                    "integer"
                ]
                }
            },
            "title": "Type"
            }
            """
        data_object = """
        {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": 1944,
                "deletedOn": null,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "IntObject",
                    "rel": [],
                    "resourceKey": {
                        "namespaceId": "1",
                        "objectId": "13"
                    },
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/"
                }
            },
            "updatedOn": "2024-09-27T08:02:44.213790",
            "version": 1
        }
        """
        transformations = match_schema(source_schema, self.target_schema)
        updated_data_object_true = migrate_object(
            data_object, self.target_schema, transformations
        )
        self.assertEqual("1944", updated_data_object_true["data"]["data"])
        self.assertEqual(2, updated_data_object_true["version"])

    def test_from_number_to_str(self):
        source_schema = """
            {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": false,
            "definitions": {
                "root": {
                "type": [
                    "number"
                ]
                }
            },
            "title": "Type"
            }
            """
        data_object = """
        {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": 3.14159265359,
                "deletedOn": null,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "IntObject",
                    "rel": [],
                    "resourceKey": {
                        "namespaceId": "1",
                        "objectId": "13"
                    },
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/"
                }
            },
            "updatedOn": "2024-09-27T08:02:44.213790",
            "version": 1
        }
        """
        transformations = match_schema(source_schema, self.target_schema)
        updated_data_object_true = migrate_object(
            data_object, self.target_schema, transformations
        )
        self.assertEqual("3.14159265359", updated_data_object_true["data"]["data"])
        self.assertEqual(2, updated_data_object_true["version"])

    def test_from_bool_to_str(self):
        source_schema = """
            {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": false,
            "definitions": {
                "root": {
                "type": [
                    "boolean"
                ]
                }
            },
            "title": "Type"
            }
            """
        data_object = """
        {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": true,
                "deletedOn": null,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "IntObject",
                    "rel": [],
                    "resourceKey": {
                        "namespaceId": "1",
                        "objectId": "13"
                    },
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/"
                }
            },
            "updatedOn": "2024-09-27T08:02:44.213790",
            "version": 1
        }
        """
        transformations = match_schema(source_schema, self.target_schema)
        updated_data_object_true = migrate_object(
            data_object, self.target_schema, transformations
        )
        self.assertEqual("True", updated_data_object_true["data"]["data"])
        self.assertEqual(2, updated_data_object_true["version"])

    def test_from_enum_to_str(self):
        pass

    def test_from_array_to_str(self):
        pass

    def test_from_obj_to_str(self):
        pass

    def test_from_tuple_to_str(self):
        pass

    def test_from_res_ref_to_str(self):
        pass

    def test_from_schema_ref_to_str(self):
        pass


if __name__ == "__main__":
    unittest.main()

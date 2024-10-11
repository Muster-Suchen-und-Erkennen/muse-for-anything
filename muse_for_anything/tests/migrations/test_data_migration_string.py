from muse_for_anything.json_migrations.data_migration import migrate_object
from muse_for_anything.json_migrations.jsonschema_matcher import match_schema

import unittest

# TODO a lot more cases


class TestMigrationToString(unittest.TestCase):

    target_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {"root": {"type": ["string"]}},
        "title": "Type",
    }

    def test_from_int_to_str(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": 1944,
                "deletedOn": None,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "Object",
                    "rel": [],
                    "resourceKey": {"namespaceId": "1", "objectId": "13"},
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/",
                },
                "updatedOn": "2024-09-27T08:02:44.213790",
                "version": 1,
            }
        }
        transformations = match_schema(source_schema, self.target_schema)
        updated_data_object_true = migrate_object(
            data_object, "integer", self.target_schema, transformations
        )
        self.assertEqual("1944", updated_data_object_true["data"]["data"])

    def test_from_number_to_str(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": 3.14159265359,
                "deletedOn": None,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "Object",
                    "rel": [],
                    "resourceKey": {"namespaceId": "1", "objectId": "13"},
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/",
                },
                "updatedOn": "2024-09-27T08:02:44.213790",
                "version": 1,
            }
        }
        transformations = match_schema(source_schema, self.target_schema)
        updated_data_object_true = migrate_object(
            data_object, "number", self.target_schema, transformations
        )
        self.assertEqual("3.14159265359", updated_data_object_true["data"]["data"])

    def test_from_bool_to_str(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": True,
                "deletedOn": None,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "Object",
                    "rel": [],
                    "resourceKey": {"namespaceId": "1", "objectId": "13"},
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/",
                },
                "updatedOn": "2024-09-27T08:02:44.213790",
                "version": 1,
            }
        }
        transformations = match_schema(source_schema, self.target_schema)
        updated_data_object_true = migrate_object(
            data_object, "boolean", self.target_schema, transformations
        )
        self.assertEqual("True", updated_data_object_true["data"]["data"])

    def test_from_enum_to_str(self):
        pass

    def test_from_array_to_str(self):
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
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": [2, 9, 44],
                "deletedOn": None,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "Object",
                    "rel": [],
                    "resourceKey": {"namespaceId": "1", "objectId": "13"},
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/",
                },
                "updatedOn": "2024-09-27T08:02:44.213790",
                "version": 1,
            }
        }
        transformations = match_schema(source_schema, self.target_schema)
        updated_data_object_true = migrate_object(
            data_object, "array", self.target_schema, transformations
        )
        self.assertEqual("[2, 9, 44]", updated_data_object_true["data"]["data"])

    def test_from_obj_to_str(self):
        source_schema = {
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
        }
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": {"one": 42, "three": True, "two": "Hello World!"},
                "deletedOn": None,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "Object",
                    "rel": [],
                    "resourceKey": {"namespaceId": "1", "objectId": "13"},
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/",
                },
                "updatedOn": "2024-09-27T08:02:44.213790",
                "version": 1,
            }
        }
        transformations = match_schema(source_schema, self.target_schema)
        updated_data_object = migrate_object(
            data_object, "object", self.target_schema, transformations
        )
        self.assertEqual(
            "{'one': 42, 'three': True, 'two': 'Hello World!'}",
            updated_data_object["data"]["data"],
        )

    def test_from_tuple_to_str(self):
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
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": [True, 12, "Hello"],
                "deletedOn": None,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "Object",
                    "rel": [],
                    "resourceKey": {"namespaceId": "1", "objectId": "13"},
                    "resourceType": "ont-object",
                    "schema": "http://localhost:5000/api/v1/schemas/ontology/27/",
                },
                "updatedOn": "2024-09-27T08:02:44.213790",
                "version": 1,
            }
        }
        transformations = match_schema(source_schema, self.target_schema)
        updated_data_object_true = migrate_object(
            data_object, "tuple", self.target_schema, transformations
        )
        self.assertEqual("[True, 12, 'Hello']", updated_data_object_true["data"]["data"])

    def test_from_res_ref_to_str(self):
        pass

    def test_from_schema_ref_to_str(self):
        pass


if __name__ == "__main__":
    unittest.main()

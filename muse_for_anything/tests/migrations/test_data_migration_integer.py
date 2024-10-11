from muse_for_anything.json_migrations.data_migration import migrate_object
from muse_for_anything.json_migrations.jsonschema_matcher import match_schema

import unittest

# TODO a lot more cases


class TestMigrationToInteger(unittest.TestCase):

    target_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {"root": {"type": ["integer"]}},
        "title": "Type",
    }

    def test_valid_from_str_to_int(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data_object_valid_one = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": "15",
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
        data_object_valid_two = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": "15.79",
                "deletedOn": None,
                "description": "",
                "name": "Object",
                "self": {
                    "href": "http://localhost:5000/api/v1/namespaces/1/objects/13/",
                    "name": "IntObject",
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
        updated_valid_data_object = migrate_object(
            data_object_valid_one, "string", self.target_schema, transformations
        )
        self.assertEqual(15, updated_valid_data_object["data"]["data"])
        updated_valid_data_object = migrate_object(
            data_object_valid_two, "string", self.target_schema, transformations
        )
        self.assertEqual(15, updated_valid_data_object["data"]["data"])

    def test_invalid_from_str_to_int(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data_object_invalid = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": "HELLO WORLD!",
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
        updated_data_object = migrate_object(data_object_invalid, "string", self.target_schema, transformations)
        self.assertEqual("HELLO WORLD!", updated_data_object["data"]["data"])

    def test_from_bool_to_int(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        data_object_true = {
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
        data_object_false = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": False,
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
            data_object_true, "boolean", self.target_schema, transformations
        )
        updated_data_object_false = migrate_object(
            data_object_false, "boolean", self.target_schema, transformations
        )
        self.assertEqual(1, updated_data_object_true["data"]["data"])
        self.assertEqual(0, updated_data_object_false["data"]["data"])

    def test_from_number_to_int(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        data_object_true = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": 5.7436555,
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
            data_object_true, "number", self.target_schema, transformations
        )
        self.assertEqual(5, updated_data_object_true["data"]["data"])

    def test_from_enum_to_int(self):
        pass

    def test_from_array_to_int(self):
        pass

    def test_from_obj_to_int(self):
        pass

    def test_from_tuple_to_int(self):
        pass

    def test_from_res_ref_to_int(self):
        pass

    def test_from_schema_ref_to_int(self):
        pass


if __name__ == "__main__":
    unittest.main()

from muse_for_anything.json_migrations.data_migration import *

import unittest

# TODO a lot more cases


class TestMigrationToInteger(unittest.TestCase):

    target_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {"root": {"type": ["boolean"]}},
        "title": "Type",
    }

    def test_from_str_to_bool(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data_object_true = {
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
        data_object_false = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": "",
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
        updated_true_data_object = migrate_object(
            data_object_true, "string", source_schema, self.target_schema
        )
        self.assertEqual(True, updated_true_data_object["data"]["data"])
        updated_false_data_object = migrate_object(
            data_object_false, "string", source_schema, self.target_schema
        )
        self.assertEqual(False, updated_false_data_object["data"]["data"])

    def test_from_int_to_bool(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        data_object_true = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": 23,
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
                "data": 0,
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
        updated_data_object_true = migrate_object(
            data_object_true, "integer", source_schema, self.target_schema
        )
        updated_data_object_false = migrate_object(
            data_object_false, "integer", source_schema, self.target_schema
        )
        self.assertEqual(True, updated_data_object_true["data"]["data"])
        self.assertEqual(False, updated_data_object_false["data"]["data"])

    def test_from_number_to_bool(self):
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
        updated_data_object_true = migrate_object(
            data_object_true, "number", source_schema, self.target_schema
        )
        self.assertEqual(True, updated_data_object_true["data"]["data"])

    def test_from_enum_to_bool(self):
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
        """
        updated_data_object_true = migrate_object(
            data_object_true, "number", source_schema, self.target_schema
        )
        self.assertEqual(True, updated_data_object_true["data"]["data"])
        """
        self.assertEqual(
            True, migrate_to_boolean(data_object_true["data"]["data"], "enum")
        )

    def test_from_array_to_bool(self):
        pass

    def test_from_obj_to_bool(self):
        pass

    def test_from_tuple_to_bool(self):
        pass

    def test_from_res_ref_to_bool(self):
        pass

    def test_from_schema_ref_to_bool(self):
        pass


if __name__ == "__main__":
    unittest.main()

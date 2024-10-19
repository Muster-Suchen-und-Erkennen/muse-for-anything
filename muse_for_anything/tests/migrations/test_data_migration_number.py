from muse_for_anything.json_migrations.data_migration import *

import unittest


class TestMigrationToNumber(unittest.TestCase):

    target_schema = {
        "$ref": "#/definitions/root",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "abstract": False,
        "definitions": {"root": {"type": ["number"]}},
        "title": "Type",
    }

    def test_valid_from_str_to_number(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": "15.8765",
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
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual(15.8765, updated_data_object["data"]["data"])

    def test_invalid_from_str_to_number(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        data_object = {
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
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual("HELLO WORLD!", updated_data_object["data"]["data"])

    def test_from_bool_to_number_true(self):
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
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual(1, updated_data_object["data"]["data"])

    def test_from_bool_to_number_false(self):
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
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual(0, updated_data_object["data"]["data"])

    def test_from_int_to_number(self):
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
                "data": 2984,
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
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual(2984.0, updated_data_object["data"]["data"])

    def test_from_enum_to_number_valid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
            "title": "Type",
        }
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": 1234.56789,
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
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual(1234.56789, updated_data_object["data"]["data"])

    def test_from_enum_to_number_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
            "title": "Type",
        }
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": "hello world",
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
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual("hello world", updated_data_object["data"]["data"])

    def test_from_array_to_number_array_valid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "array",
                    "items": {"type": ["float"]},
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": [13.4334],
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
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual(13.4334, updated_data_object["data"]["data"])

    def test_from_array_to_number_array_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "array",
                    "items": {"type": ["float"]},
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": [13.21, 14, 15.142],
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
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual([13.21, 14, 15.142], updated_data_object["data"]["data"])

    def test_from_obj_to_number(self):
        pass

    def test_from_tuple_to_number_valid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "tuple",
                    "items": [{"type": ["string"]}, {"type": ["float"]}],
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": ["hello world", 123.456],
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
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual(123.456, updated_data_object["data"]["data"])

    def test_from_tuple_to_number_invalid(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "arrayType": "tuple",
                    "items": [{"type": ["string"]}, {"type": ["float"]}],
                    "type": ["array"],
                }
            },
            "title": "Type",
        }
        data_object = {
            "data": {
                "createdOn": "2024-09-27T08:02:44.203024",
                "data": [True, False, "hello world"],
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
        updated_data_object = migrate_object(
            data_object, source_schema, self.target_schema
        )
        self.assertEqual(
            [True, False, "hello world"], updated_data_object["data"]["data"]
        )

    def test_from_res_ref_to_number(self):
        pass

    def test_from_schema_ref_to_number(self):
        pass

    def test_to_number_error(self):
        source_schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {"$ref": "#/definitions/0"},
                "0": {"type": ["integer"]},
            },
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
        with self.assertRaises(ValueError):
            migrate_object(data_object, source_schema, self.target_schema)


if __name__ == "__main__":
    unittest.main()

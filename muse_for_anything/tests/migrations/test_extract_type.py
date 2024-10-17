from muse_for_anything.json_migrations.jsonschema_matcher import *
import unittest


class TestTypeExtraction(unittest.TestCase):

    def test_extract_string(self):
        schema = {
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
        self.assertEqual(("array", False), extract_type(schema))

    def test_extract_boolean(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["boolean"]}},
            "title": "Type",
        }
        self.assertEqual(("boolean", False), extract_type(schema))

    def test_extract_enum(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"enum": ["all", True, 1234.56, None]}},
            "title": "Type",
        }
        self.assertEqual(("enum", False), extract_type(schema))

    def test_extract_integer(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["integer"]}},
            "title": "Type",
        }
        self.assertEqual(("integer", False), extract_type(schema))

    def test_extract_number(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["number"]}},
            "title": "Type",
        }
        self.assertEqual(("number", False), extract_type(schema))

    def test_extract_object(self):
        schema = {
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
        self.assertEqual(("object", False), extract_type(schema))

    def test_extract_resource_reference(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {"customType": "resourceReference", "type": ["object"]}
            },
            "title": "Type",
        }
        self.assertEqual(("resourceReference", False), extract_type(schema))

    def test_extract_schema_ref(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "$ref": "http://localhost:5000/api/v1/namespaces/4/types/8/versions/1/#/definitions/root"
                }
            },
            "title": "Type",
        }
        self.assertEqual(("schemaReference", False), extract_type(schema))

    def test_extract_string(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string"]}},
            "title": "Type",
        }
        self.assertEqual(("string", False), extract_type(schema))

    def test_extract_tuple(self):
        schema = {
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
        self.assertEqual(("tuple", False), extract_type(schema))

    def test_extract_unknown_object_type(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["object"], "customType": "customObject"}},
            "title": "Type",
        }
        with self.assertRaises(ValueError):
            extract_type(schema)

    def test_extract_unknown_array_type(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["array"]}},
            "title": "Type",
        }
        with self.assertRaises(ValueError):
            extract_type(schema)

    def test_extract_wrong_array_type(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["array"], "arrayType": "StringArray"}},
            "title": "Type",
        }
        with self.assertRaises(ValueError):
            extract_type(schema)

    def test_extract_unknown_type(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["person"]}},
            "title": "Type",
        }
        with self.assertRaises(ValueError):
            extract_type(schema)

    def test_extract_no_type(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"age": 42}},
            "title": "Type",
        }
        with self.assertRaises(ValueError):
            extract_type(schema)


    def test_extract_nullable_type(self):
        schema = {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {"root": {"type": ["string", "null"]}},
            "title": "Type",
        }
        self.assertEqual(("string", True), extract_type(schema))

if __name__ == "__main__":
    unittest.main()

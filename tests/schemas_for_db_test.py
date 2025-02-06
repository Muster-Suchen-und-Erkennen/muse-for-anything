INTEGER_SCHEMA = {
    "$ref": "#/definitions/root",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "abstract": False,
    "definitions": {"root": {"minimum": 1, "type": ["integer", "null"]}},
    "title": "IntegerType",
}

OBJECT_SCHEMA = {
    "$ref": "#/definitions/root",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "abstract": False,
    "definitions": {
        "root": {
            "properties": {
                "one": {"type": ["integer"]},
                "two": {"type": ["integer"]},
            },
            "type": ["object"],
        }
    },
    "title": "Type",
}

UNRESOLVED_SCHEMA = {
    "$ref": "#/definitions/root",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "abstract": False,
    "definitions": {
        "root": {
            "$ref": "http://localhost:5000/api/v1/namespaces/1/types/1/versions/1/#/definitions/root"
        }
    },
    "title": "Type",
}

UNRESOLVED_COMPLEX_SCHEMA = {
    "$ref": "#/definitions/root",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "abstract": False,
    "definitions": {
        "root": {
            "properties": {
                "one": {
                    "$ref": "http://localhost:5000/api/v1/namespaces/1/types/2/versions/1/#/definitions/root"
                },
                "three": {"type": ["number"]},
                "two": {"type": ["string"]},
            },
            "type": ["object"],
        }
    },
    "title": "Type",
}

UNRESOLVED_LOCAL_SCHEMA = {
    "$ref": "#/definitions/root",
    "$schema": "http://json-schema.org/draft-07/schema#",
    "abstract": False,
    "definitions": {
        "root": {"$ref": "#/definitions/1"},
        "1": {"type": ["integer"]},
    },
    "title": "Type",
}

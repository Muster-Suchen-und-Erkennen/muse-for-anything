"""Module containing all API schemas for the schema API."""

from typing import Any, Dict
from dataclasses import dataclass

from flask import request
import marshmallow as ma

from ....util.import_helpers import get_all_classes_of_module

from ...base_models import BaseApiObject, MaBaseSchema, ApiResponseSchema, ApiObjectSchema


__all__ = []


class SchemaField(ma.fields.Field):
    """Field for serializing schema dicts."""

    def _serialize(self, value: Any, attr: str, obj: Any, **kwargs):
        if not value:
            return value
        schema_dict = dict(value)
        schema_dict["$id"] = f"{request.url}#"
        if schema_dict.get("definitions"):
            definitions_dict = {}
            for key, value in schema_dict.get("definitions", {}).items():
                value_dict = dict(value)
                value_dict["$id"] = f"#/definitions/{key}"
                definitions_dict[key] = value_dict
            schema_dict["definitions"] = definitions_dict
        return schema_dict

    def _deserialize(self, value: Any, attr: str, data: Any, **kwargs):
        return value


class SchemaApiObjectSchema(ApiObjectSchema):
    schema = SchemaField(required=True, allow_none=False)


@dataclass()
class SchemaApiObject(BaseApiObject):
    schema: Dict[str, Any]


JSON_SCHEMA_ROOT_SCHEMA_REF = {"$ref": "#/definitions/root"}

JSON_SCHEMA_REF = {"$ref": "#/definitions/schema"}

NESTED_JSON_SCHEMA_REF = {"$ref": "#/definitions/nestedSchema"}

JSON_META_PROPERTIES_SCHEMA_REF = {"$ref": "#/definitions/meta"}

JSON_OBJECT_PROPERTIES_SCHEMA_REF = {"$ref": "#/definitions/object"}

JSON_ARRAY_PROPERTIES_BASE_SCHEMA_REF = {"$ref": "#/definitions/arrayBase"}

JSON_ARRAY_PROPERTIES_SCHEMA_REF = {"$ref": "#/definitions/array"}

JSON_TUPLE_PROPERTIES_SCHEMA_REF = {"$ref": "#/definitions/tuple"}

JSON_STRING_PROPERTIES_SCHEMA_REF = {"$ref": "#/definitions/string"}

JSON_NUMBER_PROPERTIES_BASE_SCHEMA_REF = {"$ref": "#/definitions/numericBase"}

JSON_NUMBER_PROPERTIES_SCHEMA_REF = {"$ref": "#/definitions/number"}

JSON_INTEGER_PROPERTIES_SCHEMA_REF = {"$ref": "#/definitions/integer"}

JSON_BOOLEAN_PROPERTIES_SCHEMA_REF = {"$ref": "#/definitions/boolean"}

JSON_ENUM_PROPERTIES_SCHEMA_REF = {"$ref": "#/definitions/enum"}

JSON_REF_PROPERTIES_SCHEMA_REF = {"$ref": "#/definitions/ref"}


JSON_BASE_TYPE_NULL_REF = {"$ref": "#/definitions/typeNull"}

JSON_BASE_TYPE_BOOLEAN_REF = {"$ref": "#/definitions/typeBoolean"}

JSON_BASE_TYPE_INTEGER_REF = {"$ref": "#/definitions/typeInteger"}

JSON_BASE_TYPE_NUMBER_REF = {"$ref": "#/definitions/typeNumber"}

JSON_BASE_TYPE_STRING_REF = {"$ref": "#/definitions/typeString"}


JSON_META_PROPERTIES_SCHEMA = {
    "$id": JSON_META_PROPERTIES_SCHEMA_REF["$ref"],
    "type": ["object"],
    "properties": {
        "$comment": {"type": "string"},
        "$id": {"type": "string", "format": "uri-reference"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "default": NESTED_JSON_SCHEMA_REF,
        "deprecated": {"type": "boolean", "default": False},
        "readOnly": {"type": "boolean", "default": False},
        "writeOnly": {"type": "boolean", "default": False},
        "allOf": {
            "type": "array",
            "minItems": 1,
            "items": NESTED_JSON_SCHEMA_REF,
        },
    },
    "hiddenProperties": ["$id", "default", "readOnly", "writeOnly"],
}

JSON_OBJECT_PROPERTIES_SCHEMA = {
    "$id": JSON_OBJECT_PROPERTIES_SCHEMA_REF["$ref"],
    "type": ["object"],
    "default": {"type": ["object"]},
    "required": ["type"],
    "allOf": [JSON_META_PROPERTIES_SCHEMA_REF],
    "properties": {
        "type": {
            "type": "array",
            "items": {
                "enum": [
                    "null",
                    "object",
                ]
            },
            "contains": {
                "const": "object",
            },
            "minItems": 1,
            "uniqueItems": True,
        },
        "customType": {
            "enum": [
                None,
                "typeRoot",
                "typeDefinition",
            ],
        },
        "maxProperties": {"type": "integer", "minimum": 0},
        "minProperties": {"type": "integer", "minimum": 0, "default": 0},
        "required": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
            "default": [],
        },
        "properties": {
            "type": "object",
            "additionalProperties": NESTED_JSON_SCHEMA_REF,
            "default": {},
        },
        "patternProperties": {
            "type": "object",
            "additionalProperties": NESTED_JSON_SCHEMA_REF,
            "propertyNames": {"type": "string", "format": "regex"},
            "default": {},
        },
        "propertyNames": JSON_SCHEMA_REF,  # TODO
        "additionalProperties": NESTED_JSON_SCHEMA_REF,
        # custom properties
        "hiddenProperties": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True,
            "default": [],
        },
        "propertyOrder": {
            "type": "object",
            "additionalProperties": {
                "name": {"type": ["number", "integer"]},
            },
        },
        "showAdditionalProperties": {
            "type": "boolean",
            "default": False,
        },
    },
}

JSON_ARRAY_PROPERTIES_BASE_SCHEMA = {
    "$id": JSON_ARRAY_PROPERTIES_BASE_SCHEMA_REF["$ref"],
    "type": ["object"],
    "default": {"type": ["array"]},
    "required": ["type"],
    "allOf": [JSON_META_PROPERTIES_SCHEMA_REF],
    "properties": {
        "type": {
            "type": "array",
            "items": {
                "enum": [
                    "null",
                    "array",
                ]
            },
            "contains": {
                "const": "array",
            },
            "minItems": 1,
            "uniqueItems": True,
        },
        "maxItems": {"type": "integer", "minimum": 0},
        "minItems": {"type": "integer", "minimum": 0, "default": 0},
        "uniqueItems": {"type": "boolean", "default": False},
        "items": {
            "anyOf": [
                NESTED_JSON_SCHEMA_REF,
                {
                    "type": "array",
                    "minItems": 1,
                    "items": NESTED_JSON_SCHEMA_REF,
                },
            ]
        },
        "contains": NESTED_JSON_SCHEMA_REF,
        "additionalItems": NESTED_JSON_SCHEMA_REF,
    },
}

JSON_ARRAY_PROPERTIES_SCHEMA = {
    "$id": JSON_ARRAY_PROPERTIES_SCHEMA_REF["$ref"],
    "type": ["object"],
    "default": {"type": ["array"]},
    "required": ["type", "arrayType"],
    "allOf": [JSON_ARRAY_PROPERTIES_BASE_SCHEMA_REF],
    "properties": {
        "items": NESTED_JSON_SCHEMA_REF,
        "arrayType": {"const": "array"},
        "orderedItems": {"type": "boolean", "default": True},
    },
}

JSON_TUPLE_PROPERTIES_SCHEMA = {
    "$id": JSON_TUPLE_PROPERTIES_SCHEMA_REF["$ref"],
    "type": ["object"],
    "default": {"type": ["array"]},
    "required": ["type", "arrayType"],
    "allOf": [JSON_ARRAY_PROPERTIES_BASE_SCHEMA_REF],
    "properties": {
        "items": {
            "type": "array",
            "minItems": 1,
            "items": NESTED_JSON_SCHEMA_REF,
        },
        "arrayType": {"const": "tuple"},
    },
}

JSON_STRING_PROPERTIES_SCHEMA = {
    "$id": JSON_STRING_PROPERTIES_SCHEMA_REF["$ref"],
    "type": ["object"],
    "default": {"type": ["string"]},
    "required": ["type"],
    "allOf": [JSON_META_PROPERTIES_SCHEMA_REF],
    "properties": {
        "type": {
            "type": "string",
            "items": {
                "enum": [
                    "null",
                    "string",
                ]
            },
            "contains": {
                "const": "string",
            },
            "minItems": 1,
            "uniqueItems": True,
        },
        "maxLength": {"type": "integer", "minimum": 0},
        "minLength": {"type": "integer", "minimum": 0, "default": 0},
        "pattern": {"type": "string", "format": "regex"},
        "format": {"type": "string"},
        "contentMediaType": {"type": "string"},
        "contentEncoding": {"type": "string"},
        "contentSchema": NESTED_JSON_SCHEMA_REF,
    },
}

JSON_NUMBER_PROPERTIES_BASE_SCHEMA = {
    "$id": JSON_NUMBER_PROPERTIES_BASE_SCHEMA_REF["$ref"],
    "type": ["object"],
    "allOf": [JSON_META_PROPERTIES_SCHEMA_REF],
    "properties": {
        "multipleOf": {"type": "number", "exclusiveMinimum": 0},
        "maximum": {"type": "number"},
        "exclusiveMaximum": {"type": "number"},
        "minimum": {"type": "number"},
        "exclusiveMinimum": {"type": "number"},
    },
}

JSON_NUMBER_PROPERTIES_SCHEMA = {
    "$id": JSON_NUMBER_PROPERTIES_SCHEMA_REF["$ref"],
    "type": ["object"],
    "default": {"type": ["number"]},
    "required": ["type"],
    "allOf": [JSON_NUMBER_PROPERTIES_BASE_SCHEMA_REF],
    "properties": {
        "type": {
            "type": "number",
            "items": {
                "enum": [
                    "null",
                    "number",
                ]
            },
            "contains": {
                "const": "number",
            },
            "minItems": 1,
            "uniqueItems": True,
        },
    },
}

JSON_INTEGER_PROPERTIES_SCHEMA = {
    "$id": JSON_INTEGER_PROPERTIES_SCHEMA_REF["$ref"],
    "type": ["object"],
    "default": {"type": ["integer"]},
    "required": ["type"],
    "allOf": [JSON_NUMBER_PROPERTIES_BASE_SCHEMA_REF],
    "properties": {
        "type": {
            "type": "integer",
            "items": {
                "enum": [
                    "null",
                    "integer",
                ]
            },
            "contains": {
                "const": "integer",
            },
            "minItems": 1,
            "uniqueItems": True,
        },
    },
}

JSON_BOOLEAN_PROPERTIES_SCHEMA = {
    "$id": JSON_BOOLEAN_PROPERTIES_SCHEMA_REF["$ref"],
    "type": ["object"],
    "default": {"type": ["boolean"]},
    "required": ["boolean"],
    "allOf": [JSON_META_PROPERTIES_SCHEMA_REF],
    "properties": {
        "type": {
            "type": "boolean",
            "items": {
                "enum": [
                    "null",
                    "boolean",
                ]
            },
            "contains": {
                "const": "boolean",
            },
            "minItems": 1,
            "uniqueItems": True,
        },
    },
}

JSON_BASE_TYPE_NULL = {
    "$id": JSON_BASE_TYPE_NULL_REF["$ref"],
    "type": "null",
    "const": None,
}

JSON_BASE_TYPE_BOOLEAN = {"$id": JSON_BASE_TYPE_BOOLEAN_REF["$ref"], "type": "boolean"}

JSON_BASE_TYPE_INTEGER = {"$id": JSON_BASE_TYPE_INTEGER_REF["$ref"], "type": "integer"}

JSON_BASE_TYPE_NUMBER = {"$id": JSON_BASE_TYPE_NUMBER_REF["$ref"], "type": "number"}

JSON_BASE_TYPE_STRING = {"$id": JSON_BASE_TYPE_STRING_REF["$ref"], "type": "string"}


JSON_ENUM_PROPERTIES_SCHEMA = {
    "$id": JSON_ENUM_PROPERTIES_SCHEMA_REF["$ref"],
    "type": ["object"],
    "default": {"enum": []},
    "required": ["enum"],
    "allOf": [JSON_META_PROPERTIES_SCHEMA_REF],
    "properties": {
        "enum": {
            "type": "array",
            "items": {
                "oneOf": [
                    JSON_BASE_TYPE_NULL_REF,
                    JSON_BASE_TYPE_BOOLEAN_REF,
                    JSON_BASE_TYPE_INTEGER_REF,
                    JSON_BASE_TYPE_NUMBER_REF,
                    JSON_BASE_TYPE_STRING_REF,
                ],
            },
        },
        # "const": {"type": ["boolean", "integer", "null", "number", "string"]},
    },
}


JSON_REF_PROPERTIES_SCHEMA = {
    "$id": JSON_REF_PROPERTIES_SCHEMA_REF["$ref"],
    "type": ["object"],
    "default": {"$ref": None},
    "required": ["$ref"],
    "allOf": [JSON_META_PROPERTIES_SCHEMA_REF],
    "properties": {
        "$ref": {"type": "string", "format": "uri-reference"},
    },
}

JSON_SCHEMA_ROOT_SCHEMA = {
    "$id": JSON_SCHEMA_ROOT_SCHEMA_REF["$ref"],
    "type": ["object"],
    "required": ["$ref"],
    "allOf": [JSON_REF_PROPERTIES_SCHEMA_REF],
    "properties": {
        "$schema": {"const": "http://json-schema.org/draft-07/schema#"},
        "$id": {"type": "string", "format": "uri-reference", "readOnly": True},
        "$ref": {"type": "string", "format": "uri-reference"},
        "definitions": {
            "type": "object",
            "additionalProperties": JSON_SCHEMA_REF,
            "default": {},
        },
    },
    "customType": "typeRoot",
}

BASIC_JSON_SCHEMA_SCHEMAS = [
    JSON_REF_PROPERTIES_SCHEMA_REF,
    JSON_ENUM_PROPERTIES_SCHEMA_REF,
    JSON_BOOLEAN_PROPERTIES_SCHEMA_REF,
    JSON_INTEGER_PROPERTIES_SCHEMA_REF,
    JSON_NUMBER_PROPERTIES_SCHEMA_REF,
    JSON_STRING_PROPERTIES_SCHEMA_REF,
]

RECURSIVE_JSON_SCHEMA_SCHEMAS = [
    JSON_ARRAY_PROPERTIES_SCHEMA_REF,
    JSON_TUPLE_PROPERTIES_SCHEMA_REF,
    JSON_OBJECT_PROPERTIES_SCHEMA_REF,
]

JSON_SCHEMA_SCHEMA = {
    "$id": JSON_SCHEMA_REF["$ref"],
    "type": ["object"],
    "oneOf": [
        *BASIC_JSON_SCHEMA_SCHEMAS,
        *RECURSIVE_JSON_SCHEMA_SCHEMAS,
    ],
    "customType": "typeDefinition",
}

NESTED_JSON_SCHEMA_SCHEMA = {
    "$id": NESTED_JSON_SCHEMA_REF["$ref"],
    "type": ["object"],
    "oneOf": [*BASIC_JSON_SCHEMA_SCHEMAS],
    "customType": "typeDefinition",
}

TYPE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$ref": JSON_SCHEMA_ROOT_SCHEMA_REF["$ref"],
    "definitions": {
        "root": JSON_SCHEMA_ROOT_SCHEMA,
        # oneOf/choice schemas
        "schema": JSON_SCHEMA_SCHEMA,
        "nestedSchema": NESTED_JSON_SCHEMA_SCHEMA,
        # meta
        "meta": JSON_META_PROPERTIES_SCHEMA,
        # type definition schemas
        "object": JSON_OBJECT_PROPERTIES_SCHEMA,
        "arrayBase": JSON_ARRAY_PROPERTIES_BASE_SCHEMA,
        "array": JSON_ARRAY_PROPERTIES_SCHEMA,
        "tuple": JSON_TUPLE_PROPERTIES_SCHEMA,
        "string": JSON_STRING_PROPERTIES_SCHEMA,
        "numericBase": JSON_NUMBER_PROPERTIES_BASE_SCHEMA,
        "number": JSON_NUMBER_PROPERTIES_SCHEMA,
        "integer": JSON_INTEGER_PROPERTIES_SCHEMA,
        "boolean": JSON_BOOLEAN_PROPERTIES_SCHEMA,
        "enum": JSON_ENUM_PROPERTIES_SCHEMA,
        "ref": JSON_REF_PROPERTIES_SCHEMA,
        # value types
        "typeNull": JSON_BASE_TYPE_NULL,
        "typeBoolean": JSON_BASE_TYPE_BOOLEAN,
        "typeInteger": JSON_BASE_TYPE_INTEGER,
        "typeNumber": JSON_BASE_TYPE_NUMBER,
        "typeString": JSON_BASE_TYPE_STRING,
    },
}


__all__.extend(get_all_classes_of_module(__name__, MaBaseSchema))

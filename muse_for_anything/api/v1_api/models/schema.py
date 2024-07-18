"""Module containing all API schemas for the schema API."""

from dataclasses import dataclass
from typing import Any, Dict

import marshmallow as ma
from flask import request

from ....util.import_helpers import get_all_classes_of_module
from ...base_models import (
    ApiObjectSchema,
    ApiResponseSchema,
    BaseApiObject,
    MaBaseSchema,
)

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


class JSONSchemaSchema(MaBaseSchema):
    definitions = ma.fields.Mapping(
        ma.fields.String(), SchemaField(allow_none=False), required=True, allow_none=False
    )
    abstract = ma.fields.Boolean(required=False, load_default=False)


JSON_SCHEMA_ROOT_SCHEMA_REF = {"$ref": "#/definitions/root"}

JSON_SCHEMA_REF = {"$ref": "#/definitions/schema"}

NESTED_JSON_SCHEMA_REF = {"$ref": "#/definitions/nestedSchema"}

JSON_MINIMAL_META_PROPERTIES_SCHEMA_REF = {"$ref": "#/definitions/minMeta"}

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

JSON_RESOURCE_REFERENCE_SCHEMA_REF = {"$ref": "#/definitions/resourceReference"}

JSON_BASE_TYPE_NULL_REF = {"$ref": "#/definitions/typeNull"}

JSON_BASE_TYPE_BOOLEAN_REF = {"$ref": "#/definitions/typeBoolean"}

JSON_BASE_TYPE_INTEGER_REF = {"$ref": "#/definitions/typeInteger"}

JSON_BASE_TYPE_NUMBER_REF = {"$ref": "#/definitions/typeNumber"}

JSON_BASE_TYPE_STRING_REF = {"$ref": "#/definitions/typeString"}


JSON_MINIMAL_META_PROPERTIES_SCHEMA = {
    "$id": JSON_MINIMAL_META_PROPERTIES_SCHEMA_REF["$ref"],
    "type": ["object"],
    "properties": {
        "$id": {"type": "string", "format": "uri-reference"},
        "title": {"type": "string", "maxLength": 300},
        "description": {"type": "string", "format": "markdown"},
        "$comment": {"title": "comment", "type": "string"},
        "deprecated": {"type": "boolean", "default": False},
        "readOnly": {"type": "boolean", "default": False},
        "writeOnly": {"type": "boolean", "default": False},
    },
    "hiddenProperties": [
        "$id",
        "default",
        "readOnly",
        "writeOnly",
        "$comment",
        "abstract",
    ],
    "propertyOrder": {
        "type": 10,
        "deprecated": 20,
        "title": 30,
        "description": 40,
        "$comment": 50,
    },
}

JSON_META_PROPERTIES_SCHEMA = {
    "$id": JSON_META_PROPERTIES_SCHEMA_REF["$ref"],
    "type": ["object"],
    "properties": {
        "$id": {"type": "string", "format": "uri-reference"},
        "title": {"type": "string", "maxLength": 300},
        "description": {"type": "string", "format": "markdown"},
        "$comment": {"title": "comment", "type": "string"},
        "default": NESTED_JSON_SCHEMA_REF,
        "deprecated": {"type": "boolean", "default": False},
        "readOnly": {"type": "boolean", "default": False},
        "writeOnly": {"type": "boolean", "default": False},
        "allOf": {
            "title": "base types",
            "type": "array",
            "minItems": 1,
            "items": NESTED_JSON_SCHEMA_REF,
        },
    },
    "hiddenProperties": [
        "$id",
        "default",
        "readOnly",
        "writeOnly",
        "allOf",
        "$comment",
    ],
    "propertyOrder": {
        "type": 10,
        "deprecated": 20,
        "title": 30,
        "description": 40,
        "$comment": 50,
        "allOf": 90,
    },
}

JSON_OBJECT_PROPERTIES_SCHEMA = {
    "$id": JSON_OBJECT_PROPERTIES_SCHEMA_REF["$ref"],
    "title": "Object",
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
            "customType": "jsonType",
        },
        "customType": {
            "enum": [
                "typeRoot",
                "typeDefinition",
                "enumItem",
            ],
        },
        "maxProperties": {"type": "integer", "minimum": 0},
        "minProperties": {"type": "integer", "minimum": 0, "default": 0},
        "required": {
            "type": "array",
            "items": {"type": "string", "singleLine": True},
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
            "propertyNames": {"type": "string", "format": "regex", "singleLine": True},
            "default": {},
        },
        "propertyNames": JSON_SCHEMA_REF,  # TODO
        "additionalProperties": NESTED_JSON_SCHEMA_REF,
        # custom properties
        "hiddenProperties": {
            "type": "array",
            "items": {"type": "string", "singleLine": True},
            "uniqueItems": True,
            "default": [],
        },
        "propertyOrder": {
            "type": "object",
            "additionalProperties": {"type": "number"},
        },
    },
    "propertyOrder": {
        "customType": 15,
        "properties": 100,
        "required": 110,
        "propertyOrder": 120,
        "hiddenProperties": 130,
        "patternProperties": 140,
        "additionalProperties": 150,
        "propertyNames": 160,
        "minProperties": 170,
        "maxProperties": 180,
    },
    "hiddenProperties": [
        "customType",
        "hiddenProperties",
        "patternProperties",
        "propertyNames",
        "minProperties",
        "maxProperties",
        "abstract",
    ],
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
            "customType": "jsonType",
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
    "hiddenProperties": ["contains", "abstract"],
}

JSON_ARRAY_PROPERTIES_SCHEMA = {
    "$id": JSON_ARRAY_PROPERTIES_SCHEMA_REF["$ref"],
    "title": "Array",
    "type": ["object"],
    "default": {"type": ["array"]},
    "required": ["type", "arrayType"],
    "allOf": [JSON_ARRAY_PROPERTIES_BASE_SCHEMA_REF],
    "properties": {
        "items": NESTED_JSON_SCHEMA_REF,
        "arrayType": {"const": "array"},
        "unorderedItems": {"type": "boolean", "default": False},
    },
    "hiddenProperties": [
        "contains",
        "additionalItems",
    ],
    "propertyOrder": {
        "arrayType": 100,
        "items": 110,
        "minItems": 120,
        "maxItems": 130,
        "uniqueItems": 140,
        "unorderedItems": 150,
    },
}

JSON_TUPLE_PROPERTIES_SCHEMA = {
    "$id": JSON_TUPLE_PROPERTIES_SCHEMA_REF["$ref"],
    "title": "Tuple",
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
    "hiddenProperties": [
        "contains",
    ],
    "propertyOrder": {
        "arrayType": 100,
        "items": 110,
        "additionalItems": 120,
        "minItems": 130,
        "maxItems": 140,
        "uniqueItems": 150,
    },
}

JSON_STRING_PROPERTIES_SCHEMA = {
    "$id": JSON_STRING_PROPERTIES_SCHEMA_REF["$ref"],
    "title": "String",
    "type": ["object"],
    "default": {"type": ["string"]},
    "required": ["type"],
    "allOf": [JSON_META_PROPERTIES_SCHEMA_REF],
    "properties": {
        "type": {
            "type": "array",
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
            "customType": "jsonType",
        },
        "maxLength": {"type": "integer", "minimum": 0},
        "minLength": {"type": "integer", "minimum": 0, "default": 0},
        "singleLine": {
            "title": "Single-Line",
            "description": "Display a single line input instead of a text field.",
            "type": "boolean",
            "default": False,
        },
        "pattern": {"type": "string", "format": "regex", "singleLine": True},
        "format": {"type": "string", "singleLine": True},
        "contentMediaType": {"type": "string", "singleLine": True},
        "contentEncoding": {"type": "string", "singleLine": True},
        "contentSchema": NESTED_JSON_SCHEMA_REF,
    },
    "hiddenProperties": [
        "contentEncoding",
        "contentSchema",
        "contentMediaType",
        "abstract",
    ],
    "propertyOrder": {
        "minLength": 100,
        "maxLength": 110,
        "singleLine": 120,
        "pattern": 130,
        "format": 140,
        "contentMediaType": 150,
        "contentEncoding": 160,
        "contentSchema": 170,
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
    "title": "Number",
    "type": ["object"],
    "default": {"type": ["number"]},
    "required": ["type"],
    "allOf": [JSON_NUMBER_PROPERTIES_BASE_SCHEMA_REF],
    "properties": {
        "type": {
            "type": "array",
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
            "customType": "jsonType",
        },
    },
    "propertyOrder": {
        "minimum": 100,
        "maximum": 110,
        "exclusiveMinimum": 120,
        "exclusiveMaximum": 130,
        "multipleOf": 140,
    },
    "hiddenProperties": ["abstract"],
}

JSON_INTEGER_PROPERTIES_SCHEMA = {
    "$id": JSON_INTEGER_PROPERTIES_SCHEMA_REF["$ref"],
    "title": "Integer",
    "type": ["object"],
    "default": {"type": ["integer"]},
    "required": ["type"],
    "allOf": [JSON_NUMBER_PROPERTIES_BASE_SCHEMA_REF],
    "properties": {
        "type": {
            "type": "array",
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
            "customType": "jsonType",
        },
    },
    "propertyOrder": {
        "minimum": 100,
        "maximum": 110,
        "exclusiveMinimum": 120,
        "exclusiveMaximum": 130,
        "multipleOf": 140,
    },
}

JSON_BOOLEAN_PROPERTIES_SCHEMA = {
    "$id": JSON_BOOLEAN_PROPERTIES_SCHEMA_REF["$ref"],
    "title": "Boolean",
    "type": ["object"],
    "default": {"type": ["boolean"]},
    "required": ["type"],
    "allOf": [JSON_META_PROPERTIES_SCHEMA_REF],
    "properties": {
        "type": {
            "type": "array",
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
            "customType": "jsonType",
        },
    },
    "hiddenProperties": ["abstract"],
}

JSON_BASE_TYPE_NULL = {
    "$id": JSON_BASE_TYPE_NULL_REF["$ref"],
    "type": "null",
    "const": None,
}

JSON_BASE_TYPE_BOOLEAN = {"$id": JSON_BASE_TYPE_BOOLEAN_REF["$ref"], "type": "boolean"}

JSON_BASE_TYPE_INTEGER = {"$id": JSON_BASE_TYPE_INTEGER_REF["$ref"], "type": "integer"}

JSON_BASE_TYPE_NUMBER = {"$id": JSON_BASE_TYPE_NUMBER_REF["$ref"], "type": "number"}

JSON_BASE_TYPE_STRING = {
    "$id": JSON_BASE_TYPE_STRING_REF["$ref"],
    "type": "string",
    "singleLine": True,
}


JSON_ENUM_PROPERTIES_SCHEMA = {
    "$id": JSON_ENUM_PROPERTIES_SCHEMA_REF["$ref"],
    "title": "Enumeration",
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
                "customType": "enumItem",
            },
        },
        # "const": {"type": ["boolean", "integer", "null", "number", "string"]},
    },
    "propertyOrder": {
        "enum": 100,
    },
    "hiddenProperties": ["abstract"],
}


JSON_REF_PROPERTIES_SCHEMA = {
    "$id": JSON_REF_PROPERTIES_SCHEMA_REF["$ref"],
    "title": "Schema Reference",
    "type": ["object"],
    "customType": "jsonRef",
    "default": {"$ref": None},
    "required": ["$ref"],
    "allOf": [JSON_META_PROPERTIES_SCHEMA_REF],
    "properties": {
        "$ref": {"type": "string", "format": "uri-reference", "singleLine": True},
    },
    "propertyOrder": {
        "$ref": 100,
    },
}


JSON_RESOURCE_REFERENCE_SCHEMA = {
    "$id": JSON_RESOURCE_REFERENCE_SCHEMA_REF["$ref"],
    "title": "Resource Reference",
    "type": "object",
    "default": {"type": ["object"], "required": ["referenceKey", "referenceType"]},
    "required": ["type", "customType", "referenceType", "required", "properties"],
    "customType": "resourceReferenceDefinition",
    "allOf": [JSON_MINIMAL_META_PROPERTIES_SCHEMA_REF],
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
            "customType": "jsonType",
        },
        "customType": {"const": "resourceReference"},
        "referenceType": {
            "title": "Reference Type",
            "enum": ["ont-taxonomy", "ont-type"],  # update to include more...
        },
        "referenceKey": {
            "type": "object",
            "additionalProperties": {"type": "string", "singleLine": True},
        },
        "required": {
            "type": "array",
            "items": [
                {"const": "referenceType"},
                {"const": "referenceKey"},
            ],
            "minItems": 2,
            "maxItems": 2,
            "additionalItems": False,
        },
        "properties": {
            "type": "object",
            "required": ["referenceType", "referenceKey"],
            "properties": {
                "referenceType": {
                    "type": "object",
                    "allOf": [JSON_MINIMAL_META_PROPERTIES_SCHEMA_REF],
                    "properties": {
                        "title": {"type": "string", "singleLine": True},
                        "const": {"type": "string", "singleLine": True},
                    },
                    "required": ["const"],
                },
                "referenceKey": {
                    "type": "object",
                    "allOf": [JSON_MINIMAL_META_PROPERTIES_SCHEMA_REF],
                    "properties": {
                        "title": {"type": "string", "singleLine": True},
                        "type": {"const": "object"},
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "type": {"const": "string"},
                                "singleLine": {"const": True},
                            },
                            "required": ["type", "singleLine"],
                        },
                    },
                    "required": ["type", "additionalProperties"],
                },
            },
        },
    },
}

JSON_SCHEMA_ROOT_SCHEMA = {
    "$id": JSON_SCHEMA_ROOT_SCHEMA_REF["$ref"],
    "type": ["object"],
    "required": ["$ref", "title"],
    "allOf": [JSON_REF_PROPERTIES_SCHEMA_REF],
    "customType": "typeRoot",
    "properties": {
        "$schema": {"const": "http://json-schema.org/draft-07/schema#"},
        "$id": {"type": "string", "format": "uri-reference", "readOnly": True},
        "$ref": {"type": "string", "format": "uri-reference"},
        "definitions": {
            "type": "object",
            "additionalProperties": JSON_SCHEMA_REF,
            "default": {},
        },
        "abstract": {"title": "Is Abstract", "type": "boolean", "default": False},
        "title": {
            "title": "Title",
            "type": "string",
            "singleLine": True,
            "maxLength": 150,
        },
        "description": {"title": "Description", "type": "string"},
    },
    "propertyOrder": {
        "title": 10,
        "description": 20,
        "abstract": 30,
        "$schema": 40,
        "$ref": 50,
        "definitions": 60,
    },
}

BASIC_JSON_SCHEMA_SCHEMAS = [
    JSON_REF_PROPERTIES_SCHEMA_REF,
    JSON_ENUM_PROPERTIES_SCHEMA_REF,
    JSON_BOOLEAN_PROPERTIES_SCHEMA_REF,
    JSON_INTEGER_PROPERTIES_SCHEMA_REF,
    JSON_NUMBER_PROPERTIES_SCHEMA_REF,
    JSON_STRING_PROPERTIES_SCHEMA_REF,
    JSON_RESOURCE_REFERENCE_SCHEMA_REF,
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
        "minMeta": JSON_MINIMAL_META_PROPERTIES_SCHEMA,
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
        "resourceReference": JSON_RESOURCE_REFERENCE_SCHEMA,
        # value types
        "typeNull": JSON_BASE_TYPE_NULL,
        "typeBoolean": JSON_BASE_TYPE_BOOLEAN,
        "typeInteger": JSON_BASE_TYPE_INTEGER,
        "typeNumber": JSON_BASE_TYPE_NUMBER,
        "typeString": JSON_BASE_TYPE_STRING,
    },
}


__all__.extend(get_all_classes_of_module(__name__, MaBaseSchema))

"""Module containing the schema API of the v1 API."""

from typing import Any, Callable, Dict, List, Optional, cast
from flask import request, jsonify, Response
from flask.helpers import url_for
from flask.views import MethodView
from flask_babel import gettext
from flask_smorest import abort
from marshmallow.base import SchemaABC
from marshmallow.fields import Field
from http import HTTPStatus

from .root import API_V1
from ..util import JSON_SCHEMA
from ..base_models import ApiLink, ApiResponse, BaseApiObject, DynamicApiResponseSchema
from .models.ontology import (
    NamespaceSchema,
    ObjectTypeSchema,
    TaxonomyItemRelationPostSchema,
    TaxonomyItemRelationSchema,
    TaxonomyItemSchema,
    TaxonomySchema,
)
from .models.schema import SchemaApiObject, SchemaApiObjectSchema, TYPE_SCHEMA


def create_schema_from_model(
    model: SchemaABC, **kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    key: str
    field: Field
    for key, field in model.fields.items():
        if field.data_key:
            field.metadata.setdefault("name", field.data_key)
    schema = cast(Dict[str, Any], JSON_SCHEMA.dump(model))
    defs: Optional[Dict[str, Any]] = schema.get("definitions")
    if defs is None:
        return schema
    for schema_name, extra in kwargs.items():
        sub_schema: Optional[Dict[str, Any]] = defs.get(schema_name)
        if sub_schema is None:
            raise ValueError(
                f"The schema {schema_name} is not defined in the schema of the model {model}!"
            )
        for key, value in extra.items():
            sub_schema[key] = value
    return schema


SCHEMAS: Dict[str, Dict[str, Any]] = {
    "Namespace": create_schema_from_model(
        NamespaceSchema(exclude=("self",)),
        NamespaceSchema={
            "propertyOrder": {"name": 10, "description": 20},
            "hiddenProperties": ["createdOn", "updatedOn", "deletedOn"],
        },
    ),
    "OntologyType": create_schema_from_model(
        ObjectTypeSchema(exclude=("self",)),
        ObjectTypeSchema={
            "propertyOrder": {"name": 10, "description": 20, "version": 30, "schema": 40},
            "hiddenProperties": ["createdOn", "updatedOn", "deletedOn"],
        },
    ),
    "TypeSchema": TYPE_SCHEMA,
    "TaxonomySchema": create_schema_from_model(
        TaxonomySchema(exclude=("self",)),
        TaxonomySchema={
            "propertyOrder": {"name": 10, "description": 20},
            "hiddenProperties": ["createdOn", "updatedOn", "deletedOn", "items"],
        },
    ),
    "TaxonomyItemSchema": create_schema_from_model(
        TaxonomyItemSchema(exclude=("self",)),
        TaxonomyItemSchema={
            "propertyOrder": {
                "name": 10,
                "description": 20,
                "version": 30,
                "sortKey": 40,
            },
            "hiddenProperties": [
                "createdOn",
                "updatedOn",
                "deletedOn",
                "parents",
                "children",
                "isToplevelItem",
            ],
        },
    ),
    "TaxonomyItemRelationSchema": create_schema_from_model(
        TaxonomyItemRelationSchema(exclude=("self",)),
        TaxonomyItemRelationSchema={
            "propertyOrder": {"taxonomyItemSource": 10, "taxonomyItemTarget": 20},
            "hiddenProperties": ["createdOn", "deletedOn"],
        },
    ),
    "TaxonomyItemRelationPostSchema": create_schema_from_model(
        TaxonomyItemRelationPostSchema(),
        TaxonomyItemRelationPostSchema={
            "propertyOrder": {"namespaceId": 10, "taxonomyId": 20, "taxonomyItemId": 30},
        },
    ),
}


def ontology_type_fixer(schema: Dict[str, Any]) -> Dict[str, Any]:
    schema["definitions"]["ObjectTypeSchema"]["properties"]["schema"] = {
        "$ref": f'{url_for("api-v1.ApiSchemaView", schema_id="TypeSchema", _external=True)}#'
    }
    return schema


SCHEMA_FIXERS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "OntologyType": ontology_type_fixer,
}

RELATED_SCHEMA: Dict[str, List[str]] = {"OntologyType": ["TypeSchema"]}


JSON_MIMETYPE = "application/json"
JSON_SCHEMA_MIMETYPE = "application/schema+json"


@API_V1.route("/schemas/")
class SchemaRootView(MethodView):
    """Root endpoint for all schemas."""

    @API_V1.response(DynamicApiResponseSchema())
    def get(self):
        """Get the urls for the schema api."""
        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.ApiSchemaRootView", _external=True),
                    rel=("collection", "schema"),
                    resource_type="schema",
                ),
            ],
            data=BaseApiObject(
                self=ApiLink(
                    href=url_for("api-v1.SchemaRootView", _external=True),
                    rel=("api", "schema"),
                    resource_type="api",
                )
            ),
        )


@API_V1.route("/schemas/api/")
class ApiSchemaRootView(MethodView):
    """Root endpoint for all api schemas."""

    @API_V1.response(DynamicApiResponseSchema())
    def get(self):
        """Get the urls for the schema api."""
        return ApiResponse(
            links=[],
            data=BaseApiObject(
                self=ApiLink(
                    href=url_for("api-v1.ApiSchemaRootView", _external=True),
                    rel=("collection", "schema"),
                    resource_type="schema",
                )
            ),
        )


@API_V1.route("/schemas/api/<string:schema_id>/")
class ApiSchemaView(MethodView):
    """Endpoint for api schemas."""

    @API_V1.response(DynamicApiResponseSchema(SchemaApiObjectSchema()))
    def get(self, schema_id: str):
        """Get the urls for the schema api."""
        schema: Optional[Dict[str, Any]] = SCHEMAS.get(schema_id)
        if schema is None:
            abort(HTTPStatus.NOT_FOUND, gettext("Schema not found."))

        fixer = SCHEMA_FIXERS.get(schema_id)
        if fixer:
            schema = fixer(schema)

        match = request.accept_mimetypes.best_match(
            (JSON_MIMETYPE, JSON_SCHEMA_MIMETYPE), default=JSON_MIMETYPE
        )

        if match == JSON_SCHEMA_MIMETYPE:
            # only return jsonschema if schema mimetype is requested
            response: Response = jsonify(schema)
            response.mimetype = JSON_SCHEMA_MIMETYPE
            return response

        related_schemas = RELATED_SCHEMA.get(schema_id, [])

        related_schema_links = []

        for related_schema_id in related_schemas:
            related_schema_links.append(
                ApiLink(
                    href=url_for(
                        "api-v1.ApiSchemaView",
                        schema_id=related_schema_id,
                        _external=True,
                    ),
                    rel=tuple(),
                    resource_type="schema",
                )
            )

        # return full api response otherwise
        return ApiResponse(
            links=related_schema_links,
            data=SchemaApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.ApiSchemaView", schema_id=schema_id, _external=True
                    ),
                    rel=tuple(),
                    resource_type="schema",
                ),
                schema=schema,
            ),
        )

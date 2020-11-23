"""Module containing the schema API of the v1 API."""

from typing import Any, Dict, Optional, cast
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
from .models.ontology import NamespaceSchema
from .models.schema import (
    SchemaApiObject,
    SchemaApiObjectSchema,
)


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
    )
}


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

        match = request.accept_mimetypes.best_match(
            (JSON_MIMETYPE, JSON_SCHEMA_MIMETYPE), default=JSON_MIMETYPE
        )

        if match == JSON_SCHEMA_MIMETYPE:
            # only return jsonschema if schema mimetype is requested
            response: Response = jsonify(schema)
            response.mimetype = JSON_SCHEMA_MIMETYPE
            return response

        # return full api response otherwise
        return ApiResponse(
            links=[],
            data=SchemaApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.ApiSchemaView", schema_id=schema_id, _external=True
                    ),
                    rel=("schema",),
                    resource_type="schema",
                ),
                schema=schema,
            ),
        )

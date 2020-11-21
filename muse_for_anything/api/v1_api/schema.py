"""Module containing the schema API of the v1 API."""

from muse_for_anything.api.v1_api.models.schema import (
    SchemaApiObject,
    SchemaApiObjectSchema,
)
from typing import Any, Dict, Optional
from flask import request, jsonify, Response
from flask.helpers import url_for
from flask.views import MethodView
from flask_babel import gettext
from flask_smorest import abort
from http import HTTPStatus

from .root import API_V1
from ..util import JSON_SCHEMA
from ..base_models import ApiLink, ApiResponse, BaseApiObject, DynamicApiResponseSchema
from .models.ontology import NamespaceSchema

SCHEMAS: Dict[str, Dict[str, Any]] = {
    "Namespace": JSON_SCHEMA.dump(NamespaceSchema(exclude=("self",)))
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

"""Module containing the schema API of the v1 API."""

from muse_for_anything.api.v1_api.ontology_type_versions_helpers import (
    type_version_to_key,
)
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
from ..util import JSON_SCHEMA, JSON_MIMETYPE, JSON_SCHEMA_MIMETYPE
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

from ...db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectType,
    OntologyObjectTypeVersion,
    OntologyObjectVersion,
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
                    rel=("collection",),
                    resource_type="schema",
                ),
                ApiLink(
                    href=url_for("api-v1.TypeSchemaRootView", _external=True),
                    rel=("collection",),
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
        # TODO add data
        return ApiResponse(
            links=[],
            data=BaseApiObject(
                self=ApiLink(
                    href=url_for("api-v1.ApiSchemaRootView", _external=True),
                    rel=("collection",),
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
            (JSON_MIMETYPE, JSON_SCHEMA_MIMETYPE),
            default=JSON_MIMETYPE,
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


@API_V1.route("/schemas/ontology/")
class TypeSchemaRootView(MethodView):
    """Root endpoint for all ontology type schemas."""

    @API_V1.response(DynamicApiResponseSchema())
    def get(self):
        """TODO"""
        # TODO add data
        return ApiResponse(
            links=[],
            data=BaseApiObject(
                self=ApiLink(
                    href=url_for("api-v1.TypeSchemaRootView", _external=True),
                    rel=("collection",),
                    resource_type="schema",
                )
            ),
        )


@API_V1.route("/schemas/ontology/<string:schema_id>/")
class TypeSchemaView(MethodView):
    """Endpoint for ontology type schemas."""

    def _get_object_type_version(self, schema_id: str) -> OntologyObjectTypeVersion:
        if not schema_id or not schema_id.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested version has the wrong format!"),
            )

        type_version_id = int(schema_id)
        found_object_type_version: Optional[
            OntologyObjectTypeVersion
        ] = OntologyObjectTypeVersion.query.filter(
            OntologyObjectTypeVersion.id == type_version_id
        ).first()

        if found_object_type_version is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Schema id not found."))
        return found_object_type_version  # is not None because abort raises exception

    @API_V1.response(DynamicApiResponseSchema(SchemaApiObjectSchema()))
    def get(self, schema_id: str):
        """TODO"""
        found_type_version = self._get_object_type_version(schema_id=schema_id)

        match = request.accept_mimetypes.best_match(
            (JSON_MIMETYPE, JSON_SCHEMA_MIMETYPE), default=JSON_MIMETYPE
        )

        schema_id_url = url_for(
            "api-v1.TypeSchemaView",
            schema_id=schema_id,
            _external=True,
        )

        type_version_schema_url = url_for(
            "api-v1.TypeVersionView",
            namespace=str(found_type_version.ontology_type.namespace_id),
            object_type=str(found_type_version.object_type_id),
            version=str(found_type_version.version),
            _external=True,
        )

        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$ref": "#/definitions/ObjectSchema",
            "$id": f"{schema_id_url}#",
            "definitions": {
                "ObjectSchema": {
                    "$id": "#/definitions/ObjectSchema",
                    "type": "object",
                    "required": ["name", "data"],
                    "properties": {
                        "createdOn": {
                            "title": "created_on",
                            "type": "string",
                            "format": "date-time",
                            "readonly": True,
                        },
                        "updatedOn": {
                            "title": "updated_on",
                            "type": "string",
                            "format": "date-time",
                            "readonly": True,
                        },
                        "deletedOn": {
                            "title": "deleted_on",
                            "type": "string",
                            "format": "date-time",
                            "readonly": True,
                        },
                        "description": {
                            "title": "description",
                            "type": "string",
                        },
                        "name": {
                            "title": "name",
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 170,
                        },
                        "data": {
                            "title": "Object Data",
                            "$ref": f"{type_version_schema_url}#",
                        },
                    },
                    "additionalProperties": False,
                    "propertyOrder": {
                        "name": 10,
                        "description": 20,
                        "data": 30,
                    },
                    "hiddenProperties": ["createdOn", "updatedOn", "deletedOn"],
                },
            },
        }

        if match == JSON_SCHEMA_MIMETYPE:
            # only return jsonschema if schema mimetype is requested
            response: Response = jsonify(schema)
            response.mimetype = JSON_SCHEMA_MIMETYPE
            return response

        related_schema_links = [
            ApiLink(
                href=type_version_schema_url,
                rel=("schema",),
                resource_type="ont-type-version",
                resource_key=type_version_to_key(found_type_version),
                schema=url_for(
                    "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
                ),
            ),
        ]

        # return full api response otherwise
        return ApiResponse(
            links=related_schema_links,
            data=SchemaApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.TypeSchemaView", schema_id=schema_id, _external=True
                    ),
                    rel=tuple(),
                    resource_type="schema",
                ),
                schema=schema,
            ),
        )

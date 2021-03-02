from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.api.v1_api.models.schema import TYPE_SCHEMA
from muse_for_anything.api.v1_api.namespace_helpers import query_params_to_api_key
from typing import Any, Dict, List, Optional, Union
from flask import url_for
from jsonschema import validate, Draft7Validator

from muse_for_anything.api.base_models import ApiLink, ApiResponse
from muse_for_anything.api.v1_api.models.ontology import (
    NamespaceData,
    NamespaceSchema,
    ObjectTypeSchema,
    ObjectTypeData,
)
from muse_for_anything.db.models.ontology_objects import (
    OntologyObjectType,
    OntologyObjectTypeVersion,
)


def type_page_params_to_key(
    namespace: str, query_params: Optional[Dict[str, Union[str, int]]] = None
) -> Dict[str, str]:
    if query_params is None:
        query_params = {}
    start_key = query_params_to_api_key(query_params)
    start_key["namespaceId"] = namespace
    return start_key


def nav_links_for_type_page(namespace: str) -> List[ApiLink]:
    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.NamespaceView",
                namespace=namespace,
                _external=True,
            ),
            rel=("up",),
            resource_type="ont-namespace",
            resource_key={"namespaceId": namespace},
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
        ),
    ]
    return nav_links


def create_action_link_for_type_page(namespace: str) -> ApiLink:
    return ApiLink(
        href=url_for(
            "api-v1.TypesView",
            namespace=namespace,
            _external=True,
        ),
        rel=("create", "post"),
        resource_type="ont-type",
        resource_key={"namespaceId": namespace},
        schema=url_for("api-v1.ApiSchemaView", schema_id="TypeSchema", _external=True),
    )


def action_links_for_type_page(namespace: Namespace) -> List[ApiLink]:
    actions: List[ApiLink] = []
    if namespace.deleted_on is None:
        # namespace is not deleted
        actions.append(create_action_link_for_type_page(namespace=str(namespace.id)))
    return actions


def type_to_key(object_type: OntologyObjectType) -> Dict[str, str]:
    return {"namespaceId": str(object_type.namespace_id), "typeId": str(object_type.id)}


def nav_links_for_type(object_type: OntologyObjectType) -> List[ApiLink]:
    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.TypesView",
                namespace=str(object_type.namespace_id),
                _external=True,
            ),
            rel=("up", "page", "first", "collection"),
            resource_type="ont-type",
            resource_key={"namespaceId": str(object_type.namespace_id)},
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="ObjectType", _external=True
            ),
        ),
        ApiLink(
            href=url_for(
                "api-v1.TypeVersionsView",
                namespace=str(object_type.namespace_id),
                object_type=str(object_type.id),
                _external=True,
            ),
            rel=("nav", "page", "first", "collection", "schema"),
            resource_type="ont-type-version",
            resource_key=type_to_key(object_type),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
            ),
        ),
        ApiLink(
            href=url_for(
                "api-v1.ObjectsView",
                namespace=str(object_type.namespace_id),
                **{"type-id": str(object_type.id)},
                _external=True,
            ),
            rel=("nav", "collection", "page", "first"),
            resource_type="ont-object",
            resource_key={
                "namespaceId": str(object_type.namespace_id),
                "?type-id": str(object_type.id),
            },
        ),
        ApiLink(
            href=url_for(
                "api-v1.NamespaceView",
                namespace=str(object_type.namespace_id),
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-namespace",
            resource_key={"namespaceId": str(object_type.namespace_id)},
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
        ),
    ]
    return nav_links


def type_to_type_data(object_type: OntologyObjectType) -> ObjectTypeData:
    return ObjectTypeData(
        self=ApiLink(
            href=url_for(
                "api-v1.TypeView",
                namespace=str(object_type.namespace_id),
                object_type=str(object_type.id),
                _external=True,
            ),
            rel=tuple(),
            resource_type="ont-type",
            resource_key=type_to_key(object_type),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
            ),
        ),
        name=object_type.name,
        description=object_type.description,
        created_on=object_type.created_on,
        updated_on=object_type.updated_on,
        deleted_on=object_type.deleted_on,
        version=object_type.version,
        abstract=not object_type.is_toplevel_type,
        schema=object_type.schema,
    )


def action_links_for_type(object_type: OntologyObjectType) -> List[ApiLink]:
    actions: List[ApiLink] = []
    if object_type.namespace.deleted_on is None:
        # namespace is modifyable
        actions.append(
            ApiLink(
                href=url_for(
                    "api-v1.TypesView",
                    namespace=str(object_type.namespace_id),
                    _external=True,
                ),
                rel=("create", "post"),
                resource_type="ont-type",
                resource_key={"namespaceId": str(object_type.namespace_id)},
                schema=url_for(
                    "api-v1.ApiSchemaView", schema_id="TypeSchema", _external=True
                ),
            )
        )

        resource_key = type_to_key(object_type)

        if object_type.deleted_on is None:
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TypeView",
                        namespace=str(object_type.namespace_id),
                        object_type=str(object_type.id),
                        external=True,
                    ),
                    rel=("update", "put"),
                    resource_type="ont-type",
                    resource_key=resource_key,
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="TypeSchema", _external=True
                    ),
                )
            )
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TypeView",
                        namespace=str(object_type.namespace_id),
                        object_type=str(object_type.id),
                        _external=True,
                    ),
                    rel=("delete",),
                    resource_type="ont-type",
                    resource_key=resource_key,
                )
            )
        else:
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TypeView",
                        namespace=str(object_type.namespace_id),
                        object_type=str(object_type.id),
                        _external=True,
                    ),
                    rel=("restore", "post"),
                    resource_type="ont-type",
                    resource_key=resource_key,
                )
            )

    return actions


def type_to_api_response(object_type: OntologyObjectType) -> ApiResponse:
    object_type_data = type_to_type_data(object_type)
    raw_object_type: Dict[str, Any] = ObjectTypeSchema().dump(object_type_data)
    return ApiResponse(
        links=(
            *nav_links_for_type(object_type),
            *action_links_for_type(object_type),
        ),
        data=raw_object_type,
    )


def validate_type_schema(schema: Any):
    # FIXME add proper error reporting for api client
    validator = Draft7Validator(TYPE_SCHEMA)
    for error in sorted(validator.iter_errors(schema), key=str):
        print("VALIDATION ERROR", error.message)
    validate(schema, TYPE_SCHEMA)

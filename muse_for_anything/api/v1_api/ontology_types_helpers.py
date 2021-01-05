from muse_for_anything.api.v1_api.namespace_helpers import query_params_to_api_key
from typing import Any, Dict, List, Union
from flask import url_for

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
    namespace: str, query_params: Dict[str, Union[str, int]]
) -> Dict[str, str]:
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


def action_links_for_type_page(namespace: str) -> List[ApiLink]:
    actions: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.TypesView",
                namespace=namespace,
                _external=True,
            ),
            rel=("create", "post"),
            resource_type="ont-type",
            resource_key={"namespaceId": namespace},
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TypeSchema", _external=True
            ),
        ),
    ]

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
                namespace=str(object_type.id),
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
        schema=object_type.schema,
    )


def action_links_for_type(object_type: OntologyObjectType) -> List[ApiLink]:
    actions: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.TypesView",
                namespace=str(object_type.namespace_id),
                _external=True,
            ),
            rel=("create", "post"),
            resource_type="ont-type",
            resource_key=type_to_key(object_type),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TypeSchema", _external=True
            ),
        ),
    ]

    # TODO resource_key = type_to_key(ontology_type)

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

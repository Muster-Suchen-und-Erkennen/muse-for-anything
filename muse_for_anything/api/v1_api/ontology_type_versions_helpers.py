from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.api.v1_api.models.schema import TYPE_SCHEMA
from muse_for_anything.api.v1_api.namespace_helpers import query_params_to_api_key
from typing import Any, Dict, List, Optional, Union
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

from .ontology_types_helpers import type_to_key


def type_version_page_params_to_key(
    object_type: OntologyObjectType,
    query_params: Optional[Dict[str, Union[str, int]]] = None,
) -> Dict[str, str]:
    if query_params is None:
        query_params = {}
    start_key = query_params_to_api_key(query_params)
    start_key["namespaceId"] = str(object_type.namespace_id)
    start_key["typeId"] = str(object_type.id)
    return start_key


def nav_links_for_type_versions_page(object_type: OntologyObjectType) -> List[ApiLink]:
    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.TypeView",
                namespace=str(object_type.namespace_id),
                object_type=str(object_type.id),
                _external=True,
            ),
            rel=("up",),
            resource_type="ont-type",
            resource_key=type_to_key(object_type),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
            ),
        ),
        ApiLink(
            href=url_for(
                "api-v1.TypesView",
                namespace=str(object_type.namespace_id),
                _external=True,
            ),
            rel=("nav", "page", "first", "collection"),
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


def type_version_to_key(object_type_version: OntologyObjectTypeVersion) -> Dict[str, str]:
    return {
        "namespaceId": str(object_type_version.ontology_type.namespace_id),
        "typeId": str(object_type_version.object_type_id),
        "typeVersion": str(object_type_version.version),
    }


def nav_links_for_type_version(
    object_type_version: OntologyObjectTypeVersion,
) -> List[ApiLink]:
    namespace_id = str(object_type_version.ontology_type.namespace_id)
    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.TypeVersionsView",
                namespace=namespace_id,
                object_type=str(object_type_version.object_type_id),
                _external=True,
            ),
            rel=("up", "page", "first", "collection"),
            resource_type="ont-type-version",
            resource_key=type_to_key(object_type_version.ontology_type),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
            ),
        ),
        ApiLink(
            href=url_for(
                "api-v1.TypeView",
                namespace=namespace_id,
                object_type=str(object_type_version.object_type_id),
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-type",
            resource_key=type_to_key(object_type_version.ontology_type),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
            ),
        ),
        ApiLink(
            href=url_for(
                "api-v1.TypesView",
                namespace=namespace_id,
                _external=True,
            ),
            rel=("page", "first", "collection", "nav"),
            resource_type="ont-type",
            resource_key={"namespaceId": namespace_id},
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="ObjectType", _external=True
            ),
        ),
        ApiLink(
            href=url_for(
                "api-v1.NamespaceView",
                namespace=namespace_id,
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-namespace",
            resource_key={"namespaceId": namespace_id},
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
        ),
    ]
    return nav_links


def type_version_to_type_data(
    object_type_version: OntologyObjectTypeVersion,
) -> ObjectTypeData:
    return ObjectTypeData(
        self=ApiLink(
            href=url_for(
                "api-v1.TypeVersionView",
                namespace=str(object_type_version.ontology_type.namespace_id),
                object_type=str(object_type_version.object_type_id),
                version=str(object_type_version.version),
                _external=True,
            ),
            rel=tuple(),
            resource_type="ont-type-version",
            resource_key=type_version_to_key(object_type_version),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
            ),
        ),
        name=object_type_version.name,
        description=object_type_version.description,
        created_on=object_type_version.created_on,
        updated_on=object_type_version.created_on,
        deleted_on=object_type_version.deleted_on,
        version=object_type_version.version,
        abstract=object_type_version.abstract,
        schema=object_type_version.data,
    )


def type_version_to_api_response(
    object_type_version: OntologyObjectTypeVersion,
) -> ApiResponse:
    object_type_data = type_version_to_type_data(object_type_version)
    raw_object_type: Dict[str, Any] = ObjectTypeSchema().dump(object_type_data)
    return ApiResponse(
        links=(*nav_links_for_type_version(object_type_version),),
        data=raw_object_type,
    )

from typing import Any, Dict, List, Union
from flask import url_for

from muse_for_anything.api.base_models import ApiLink, ApiResponse
from muse_for_anything.api.v1_api.models.ontology import NamespaceData, NamespaceSchema
from muse_for_anything.db.models.namespace import Namespace


def namespace_to_key(namespace: Namespace) -> Dict[str, str]:
    return {"namespaceId": str(namespace.id)}


def namespace_to_namespace_data(namespace: Namespace) -> NamespaceData:
    return NamespaceData(
        self=ApiLink(
            href=url_for(
                "api-v1.NamespaceView", namespace=str(namespace.id), _external=True
            ),
            rel=("ont-namespace",),
            resource_type="ont-namespace",
            resource_key=namespace_to_key(namespace),
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
        ),
        name=namespace.name,
        description=namespace.description,
        created_on=namespace.created_on,
        updated_on=namespace.updated_on,
        deleted_on=namespace.deleted_on,
    )


def nav_links_for_namespace(namespace: Namespace) -> List[ApiLink]:
    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.TypesView",
                namespace=str(namespace.id),
                _external=True,
            ),
            rel=("nav", "collection", "page", "first"),
            resource_type="ont-type",
            resource_key=namespace_to_key(namespace),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
            ),
        ),
        ApiLink(
            href=url_for(
                "api-v1.TaxonomiesView",
                namespace=str(namespace.id),
                _external=True,
            ),
            rel=("nav", "collection", "page", "first"),
            resource_type="ont-taxonomy",
            resource_key=namespace_to_key(namespace),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
        ),
    ]
    return nav_links


def action_links_for_namespace(namespace: Namespace) -> List[ApiLink]:
    actions: List[ApiLink] = [
        ApiLink(
            href=url_for("api-v1.NamespacesView", _external=True),
            rel=("create", "post"),
            resource_type="ont-namespace",
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
        ),
    ]

    resource_key = namespace_to_key(namespace)

    if namespace.deleted_on is None:
        actions.append(
            ApiLink(
                href=url_for(
                    "api-v1.NamespaceView",
                    namespace=str(namespace.id),
                    _external=True,
                ),
                rel=("update", "put"),
                resource_type="ont-namespace",
                resource_key=resource_key,
                schema=url_for(
                    "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                ),
            )
        )
        actions.append(
            ApiLink(
                href=url_for(
                    "api-v1.NamespaceView",
                    namespace=str(namespace.id),
                    _external=True,
                ),
                rel=("delete",),
                resource_type="ont-namespace",
                resource_key=resource_key,
            )
        )
    else:
        actions.append(
            ApiLink(
                href=url_for(
                    "api-v1.NamespaceView",
                    namespace=str(namespace.id),
                    _external=True,
                ),
                rel=("restore", "post"),
                resource_type="ont-namespace",
                resource_key=resource_key,
            )
        )
    return actions


def namespace_to_api_response(namespace: Namespace) -> ApiResponse:
    namespace_data = namespace_to_namespace_data(namespace)
    raw_namespace: Dict[str, Any] = NamespaceSchema().dump(namespace_data)
    return ApiResponse(
        links=(
            ApiLink(
                href=url_for("api-v1.NamespacesView", _external=True),
                rel=("first", "page", "up", "collection", "ont-namespace"),
                resource_type="ont-namespace",
                schema=url_for(
                    "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                ),
            ),
            *nav_links_for_namespace(namespace),
            *action_links_for_namespace(namespace),
        ),
        data=raw_namespace,
    )


def query_params_to_api_key(query_params: Dict[str, Union[str, int]]) -> Dict[str, str]:
    key = {}
    for k, v in query_params.items():
        key[f'?{k.replace("_", "-")}'] = str(v)
    return key

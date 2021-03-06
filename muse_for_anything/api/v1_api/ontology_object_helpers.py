from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.api.v1_api.namespace_helpers import query_params_to_api_key
from typing import Any, Dict, List, Optional, Union
from flask import url_for

from muse_for_anything.api.base_models import ApiLink, ApiResponse
from muse_for_anything.api.v1_api.models.ontology import (
    ObjectSchema,
    ObjectData,
)
from muse_for_anything.db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectType,
    OntologyObjectTypeVersion,
    OntologyObjectVersion,
)

from .ontology_types_helpers import type_to_key
from .ontology_type_versions_helpers import type_version_to_key


def object_page_params_to_key(
    namespace: str, query_params: Optional[Dict[str, Union[str, int]]] = None
) -> Dict[str, str]:
    if query_params is None:
        query_params = {}
    start_key = query_params_to_api_key(query_params)
    start_key["namespaceId"] = namespace
    return start_key


def nav_links_for_object_page(namespace: Namespace) -> List[ApiLink]:
    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.NamespaceView",
                namespace=str(namespace.id),
                _external=True,
            ),
            rel=("up",),
            resource_type="ont-namespace",
            resource_key={"namespaceId": str(namespace.id)},
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
            name=namespace.name,
        ),
    ]
    return nav_links


def action_links_for_object_page(
    namespace: Namespace, type: Optional[OntologyObjectType] = None
) -> List[ApiLink]:
    actions: List[ApiLink] = []
    if (
        type is not None
        and type.is_toplevel_type  # type is not abstract
        and type.deleted_on is None
        and namespace.deleted_on is None
    ):
        actions.append(
            ApiLink(
                href=url_for(
                    "api-v1.ObjectsView",
                    namespace=str(namespace.id),
                    **{"type-id": str(type.id)},
                    _external=True,
                ),
                rel=("create", "post"),
                resource_type="ont-object",
                resource_key={"namespaceId": str(namespace.id), "?type-id": str(type.id)},
                schema=type_version_to_schema_url(type.current_version),
            )
        )
    return actions


def object_to_key(object: OntologyObject) -> Dict[str, str]:
    return {"namespaceId": str(object.namespace_id), "objectId": str(object.id)}


def object_version_to_key(version: OntologyObjectVersion) -> Dict[str, str]:
    start_key = object_to_key(version.ontology_object)
    start_key["objectVersion"] = str(version.version)
    return start_key


def type_version_to_schema_url(version: OntologyObjectTypeVersion) -> str:
    return url_for(
        "api-v1.TypeSchemaView",
        schema_id=str(version.id),
        _external=True,
    )


def nav_links_for_object(object: OntologyObject) -> List[ApiLink]:
    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.ObjectsView",
                namespace=str(object.namespace_id),
                _external=True,
            ),
            rel=("up", "page", "first", "collection"),
            resource_type="ont-object",
            resource_key={"namespaceId": str(object.namespace_id)},
        ),
        ApiLink(
            href=url_for(
                "api-v1.ObjectVersionsView",
                namespace=str(object.namespace_id),
                object_id=str(object.id),
                _external=True,
            ),
            rel=("nav", "page", "first", "collection"),
            resource_type="ont-object-version",
            resource_key=object_to_key(object),
        ),
        ApiLink(
            href=url_for(
                "api-v1.NamespaceView",
                namespace=str(object.namespace_id),
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-namespace",
            resource_key={"namespaceId": str(object.namespace_id)},
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
            name=object.namespace.name,
        ),
    ]

    if isinstance(object, OntologyObject):
        nav_links.append(
            ApiLink(
                href=url_for(
                    "api-v1.TypeView",
                    namespace=str(object.namespace_id),
                    object_type=str(object.object_type_id),
                    _external=True,
                ),
                rel=("nav",),
                resource_type="ont-type",
                resource_key=type_to_key(object.ontology_type),
                schema=url_for(
                    "api-v1.ApiSchemaView", schema_id="TypeSchema", _external=True
                ),
                name=object.ontology_type.name,
            )
        )

    # TODO add more nav links to type and to current version… ?
    return nav_links


def object_to_self_link(object: OntologyObject) -> ApiLink:
    return ApiLink(
        href=url_for(
            "api-v1.ObjectView",
            namespace=str(object.namespace_id),
            object_id=str(object.id),
            _external=True,
        ),
        rel=tuple(),
        resource_type="ont-object",
        resource_key=object_to_key(object),
        schema=type_version_to_schema_url(object.ontology_type_version),
        name=object.name,
    )


def object_version_to_self_link(version: OntologyObjectVersion) -> ApiLink:
    return ApiLink(
        href=url_for(
            "api-v1.ObjectView",
            namespace=str(version.ontology_object.namespace_id),
            object_id=str(version.object_id),
            version=str(version.version),
            _external=True,
        ),
        rel=tuple(),
        resource_type="ont-object-version",
        resource_key=object_version_to_key(version),
        schema=type_version_to_schema_url(version.ontology_type_version),
        name=version.name,
    )


def object_to_object_data(
    object: Union[OntologyObject, OntologyObjectVersion]
) -> ObjectData:
    object_type_version = object.ontology_type_version
    assert (
        object_type_version is not None
    ), "An object should always have a current version!"

    self_link: ApiLink
    if isinstance(object, OntologyObject):
        self_link = object_to_self_link(object)
    else:
        self_link = object_version_to_self_link(object)

    return ObjectData(
        self=self_link,
        name=object.name,
        description=object.description,
        created_on=object.created_on,
        updated_on=object.updated_on,
        deleted_on=object.deleted_on,
        version=object.version,
        data=object.data,
    )


def action_links_for_object(object: OntologyObject) -> List[ApiLink]:
    object_type_version = object.ontology_type_version
    assert (
        object_type_version is not None
    ), "An object should always have a current version!"
    current_type_schema_url = type_version_to_schema_url(
        object.ontology_type.current_version
    )

    actions: List[ApiLink] = []
    if object.namespace.deleted_on is None:
        # namespace is modifyable
        actions.append(
            ApiLink(
                href=url_for(
                    "api-v1.ObjectsView",
                    namespace=str(object.namespace_id),
                    type_id=str(object.object_type_id),
                    _external=True,
                ),
                rel=("create", "post"),
                resource_type="ont-object",
                resource_key={
                    "namespaceId": str(object.namespace_id),
                    "?type-id": str(object.object_type_id),
                },
                schema=current_type_schema_url,
            )
        )

        resource_key = object_to_key(object)

        if object.deleted_on is None:
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.ObjectView",
                        namespace=str(object.namespace_id),
                        object_id=str(object.id),
                        _external=True,
                    ),
                    rel=("update", "put"),
                    resource_type="ont-object",
                    resource_key=resource_key,
                    schema=current_type_schema_url,
                    name=object.name,
                )
            )
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.ObjectView",
                        namespace=str(object.namespace_id),
                        object_id=str(object.id),
                        _external=True,
                    ),
                    rel=("delete",),
                    resource_type="ont-object",
                    resource_key=resource_key,
                    name=object.name,
                )
            )
        else:
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.ObjectView",
                        namespace=str(object.namespace_id),
                        object_id=str(object.id),
                        _external=True,
                    ),
                    rel=("restore", "post"),
                    resource_type="ont-object",
                    resource_key=resource_key,
                    name=object.name,
                )
            )

    return actions


def object_to_api_response(object: OntologyObject) -> ApiResponse:
    object_data = object_to_object_data(object)
    raw_object: Dict[str, Any] = ObjectSchema().dump(object_data)
    return ApiResponse(
        links=(
            *nav_links_for_object(object),
            *action_links_for_object(object),
        ),
        data=raw_object,
    )


def nav_links_for_object_version(version: OntologyObjectVersion) -> List[ApiLink]:
    object = version.ontology_object
    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.ObjectVersionsView",
                namespace=str(object.namespace_id),
                object_id=str(object.id),
                _external=True,
            ),
            rel=("up", "page", "first", "collection"),
            resource_type="ont-object-version",
            resource_key=object_to_key(object),
        ),
        ApiLink(
            href=url_for(
                "api-v1.ObjectView",
                namespace=str(object.namespace_id),
                object_id=str(object.id),
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-object",
            resource_key=object_to_key(object),
            name=object.name,
        ),
        ApiLink(
            href=url_for(
                "api-v1.ObjectsView",
                namespace=str(object.namespace_id),
                _external=True,
            ),
            rel=("nav", "page", "first", "collection"),
            resource_type="ont-object",
            resource_key={"namespaceId": str(object.namespace_id)},
        ),
        ApiLink(
            href=url_for(
                "api-v1.NamespaceView",
                namespace=str(object.namespace_id),
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-namespace",
            resource_key={"namespaceId": str(object.namespace_id)},
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
            name=object.namespace.name,
        ),
    ]

    if isinstance(version, OntologyObjectVersion):
        nav_links.append(
            ApiLink(
                href=url_for(
                    "api-v1.TypeVersionView",
                    namespace=str(object.namespace_id),
                    object_type=str(object.object_type_id),
                    version=str(version.object_type_version_id),
                    _external=True,
                ),
                rel=("nav",),
                resource_type="ont-type-version",
                resource_key=type_version_to_key(version.ontology_type_version),
                schema=url_for(
                    "api-v1.ApiSchemaView", schema_id="TypeSchema", _external=True
                ),
                name=version.ontology_type_version.name,
            )
        )

    # TODO add more nav links to type and to current version… ?
    return nav_links


def object_version_to_api_response(version: OntologyObjectVersion) -> ApiResponse:
    object_data = object_to_object_data(version)
    raw_object: Dict[str, Any] = ObjectSchema().dump(object_data)
    return ApiResponse(
        links=(
            *nav_links_for_object_version(version),
            # TODO *action_links_for_object_version(version),
        ),
        data=raw_object,
    )


def object_version_page_params_to_key(
    object: OntologyObject, query_params: Optional[Dict[str, Union[str, int]]] = None
) -> Dict[str, str]:
    if query_params is None:
        query_params = {}
    start_key = query_params_to_api_key(query_params)
    start_key["namespaceId"] = str(object.namespace_id)
    start_key["objectId"] = str(object.id)
    return start_key


def nav_links_for_object_versions_page(object: OntologyObject) -> List[ApiLink]:
    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.ObjectView",
                namespace=str(object.namespace_id),
                object_id=str(object.id),
                _external=True,
            ),
            rel=("up",),
            resource_type="ont-object",
            resource_key=object_to_key(object),
            name=object.name,
        ),
        ApiLink(
            href=url_for(
                "api-v1.ObjectsView",
                namespace=str(object.namespace_id),
                _external=True,
            ),
            rel=("nav", "page", "first", "collection"),
            resource_type="ont-object",
            resource_key={"namespaceId": str(object.namespace_id)},
        ),
        ApiLink(
            href=url_for(
                "api-v1.NamespaceView",
                namespace=str(object.namespace_id),
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-namespace",
            resource_key={"namespaceId": str(object.namespace_id)},
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
            name=object.namespace.name,
        ),
    ]

    if isinstance(object, OntologyObject):
        nav_links.append(
            ApiLink(
                href=url_for(
                    "api-v1.TypeView",
                    namespace=str(object.namespace_id),
                    object_type=str(object.object_type_id),
                    _external=True,
                ),
                rel=("nav",),
                resource_type="ont-type",
                resource_key=type_to_key(object.ontology_type),
                schema=url_for(
                    "api-v1.ApiSchemaView", schema_id="TypeSchema", _external=True
                ),
                name=object.ontology_type.name,
            )
        )

    # TODO add more nav links to type and to current version…
    return nav_links

"""Module containing resource and link generators for object type versions."""

from typing import Any, Dict, Iterable, List, Optional, Union

from flask import url_for

from muse_for_anything.api.base_models import ApiLink, ApiResponse
from muse_for_anything.api.v1_api.constants import (
    COLLECTION_REL,
    GET,
    ITEM_COUNT_DEFAULT,
    ITEM_COUNT_QUERY_KEY,
    NAMESPACE_REL_TYPE,
    NAV_REL,
    PAGE_REL,
    SCHEMA_RESOURCE,
    TYPE_REL_TYPE,
    TYPE_SCHEMA,
    TYPE_VERSION_EXTRA_LINK_RELATIONS,
    TYPE_VERSION_KEY,
    TYPE_VERSION_PAGE_RESOURCE,
    TYPE_VERSION_REL_TYPE,
    TYPE_VERSION_RESOURCE,
    UP_REL,
)
from muse_for_anything.api.v1_api.models.ontology import ObjectTypeData
from muse_for_anything.api.v1_api.request_helpers import (
    ApiObjectGenerator,
    ApiResponseGenerator,
    KeyGenerator,
    LinkGenerator,
    PageResource,
)
from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectType,
    OntologyObjectTypeVersion,
)
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource


# Type versions page ###########################################################
class ObjectTypeVersionsPageKeyGenerator(
    KeyGenerator, resource_type=OntologyObjectTypeVersion, page=True
):
    def update_key(self, key: Dict[str, str], resource: PageResource) -> Dict[str, str]:
        assert isinstance(resource, PageResource)
        assert resource.resource_type == OntologyObjectTypeVersion
        assert resource.resource is not None
        key.update(KeyGenerator.generate_key(resource.resource))
        return key


class ObjectTypeVersionsPageSelfLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectTypeVersion, page=True
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(
            OsoResource(
                TYPE_VERSION_REL_TYPE,
                is_collection=True,
                parent_resource=resource.resource,
            ),
            action=GET,
        ):
            return
        object_type = resource.resource
        assert object_type is not None
        assert isinstance(object_type, OntologyObjectType)
        if query_params is None:
            query_params = {ITEM_COUNT_QUERY_KEY: ITEM_COUNT_DEFAULT}
        return ApiLink(
            href=url_for(
                TYPE_VERSION_PAGE_RESOURCE,
                namespace=str(object_type.namespace_id),
                object_type=str(object_type.id),
                **query_params,
                _external=True,
            ),
            rel=(COLLECTION_REL, PAGE_REL),
            resource_type=TYPE_VERSION_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for(SCHEMA_RESOURCE, schema_id=TYPE_SCHEMA, _external=True),
        )


class ObjectTypeVersionsPageUpLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectTypeVersion, page=True, relation=UP_REL
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, OntologyObjectType)
        return LinkGenerator.get_link_of(resource.resource, extra_relations=(UP_REL,))


class ObjectTypeVersionsPageNamespaceLinkGenerator(
    LinkGenerator,
    resource_type=OntologyObjectTypeVersion,
    page=True,
    relation=NAMESPACE_REL_TYPE,
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, OntologyObjectType)
        return LinkGenerator.get_link_of(
            resource.resource.namespace, extra_relations=(NAV_REL,)
        )


# Type version #################################################################
class ObjectTypeVersionKeyGenerator(
    KeyGenerator, resource_type=OntologyObjectTypeVersion
):
    def update_key(
        self, key: Dict[str, str], resource: OntologyObjectTypeVersion
    ) -> Dict[str, str]:
        assert isinstance(resource, OntologyObjectTypeVersion)
        key.update(KeyGenerator.generate_key(resource.ontology_type))
        key[TYPE_VERSION_KEY] = str(resource.version)
        return key


class ObjectTypeVersionSelfLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectTypeVersion
):
    def generate_link(
        self,
        resource: OntologyObjectTypeVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                TYPE_VERSION_RESOURCE,
                namespace=str(resource.ontology_type.namespace_id),
                object_type=str(resource.object_type_id),
                version=str(resource.version),
                _external=True,
            ),
            rel=tuple(),
            resource_type=TYPE_VERSION_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(SCHEMA_RESOURCE, schema_id=TYPE_SCHEMA, _external=True),
            name=f"{resource.name} (v{resource.version})",
        )


class ObjectTypeVersionApiObjectGenerator(
    ApiObjectGenerator, resource_type=OntologyObjectTypeVersion
):
    def generate_api_object(
        self,
        resource: OntologyObjectTypeVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[ObjectTypeData]:
        assert isinstance(resource, OntologyObjectTypeVersion)

        if not FLASK_OSO.is_allowed(resource, action=GET):
            return

        return ObjectTypeData(
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
            name=resource.name,
            description=resource.description,
            created_on=resource.created_on,
            updated_on=resource.created_on,
            deleted_on=resource.deleted_on,
            version=resource.version,
            abstract=resource.abstract,
            schema=resource.data,
        )


class ObjectTypeVersionApiResponseGenerator(
    ApiResponseGenerator, resource_type=OntologyObjectTypeVersion
):
    def generate_api_response(
        self, resource, *, link_to_relations: Optional[Iterable[str]], **kwargs
    ) -> Optional[ApiResponse]:
        link_to_relations = (
            TYPE_VERSION_EXTRA_LINK_RELATIONS
            if link_to_relations is None
            else link_to_relations
        )
        return ApiResponseGenerator.default_generate_api_response(
            resource, link_to_relations=link_to_relations, **kwargs
        )


class ObjectTypeVersionUpLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectTypeVersion, relation=UP_REL
):
    def generate_link(
        self,
        resource: OntologyObjectTypeVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectTypeVersion)
        return LinkGenerator.get_link_of(
            PageResource(
                OntologyObjectTypeVersion, resource=resource.ontology_type, page_number=1
            ),
            extra_relations=(UP_REL,),
        )


class ObjectTypeVersionTypeLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectTypeVersion, relation=TYPE_REL_TYPE
):
    def generate_link(
        self,
        resource: OntologyObjectTypeVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectTypeVersion)
        return LinkGenerator.get_link_of(
            resource.ontology_type, extra_relations=(NAV_REL,)
        )


class ObjectTypeVersionNamespaceLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectTypeVersion, relation=NAMESPACE_REL_TYPE
):
    def generate_link(
        self,
        resource: OntologyObjectTypeVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectTypeVersion)
        return LinkGenerator.get_link_of(
            resource.ontology_type.namespace, extra_relations=(NAV_REL,)
        )

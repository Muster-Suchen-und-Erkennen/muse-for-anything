"""Module containing resource and link generators for object versions."""

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
    OBJECT_REL_TYPE,
    OBJECT_VERSION_EXTRA_LINK_RELATIONS,
    OBJECT_VERSION_KEY,
    OBJECT_VERSION_PAGE_RESOURCE,
    OBJECT_VERSION_REL_TYPE,
    PAGE_REL,
    TYPE_REL_TYPE,
    TYPE_VERSION_REL_TYPE,
    TYPE_VERSION_RESOURCE,
    UP_REL,
)
from muse_for_anything.api.v1_api.generators.object import object_type_schema_url
from muse_for_anything.api.v1_api.models.ontology import ObjectData, ObjectTypeData
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
    OntologyObjectVersion,
)
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource


# Object versions page #########################################################
class ObjectVersionsPageKeyGenerator(
    KeyGenerator, resource_type=OntologyObjectVersion, page=True
):
    def update_key(self, key: Dict[str, str], resource: PageResource) -> Dict[str, str]:
        assert isinstance(resource, PageResource)
        assert resource.resource_type == OntologyObjectVersion
        assert resource.resource is not None
        key.update(KeyGenerator.generate_key(resource.resource))
        return key


class ObjectVersionsPageSelfLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectVersion, page=True
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
                OBJECT_VERSION_REL_TYPE,
                is_collection=True,
                parent_resource=resource.resource,
            ),
            action=GET,
        ):
            return
        object_ = resource.resource
        assert object_ is not None
        assert isinstance(object_, OntologyObject)
        if query_params is None:
            query_params = {ITEM_COUNT_QUERY_KEY: ITEM_COUNT_DEFAULT}
        return ApiLink(
            href=url_for(
                OBJECT_VERSION_PAGE_RESOURCE,
                namespace=str(object_.namespace_id),
                object_id=str(object_.id),
                **query_params,
                _external=True,
            ),
            rel=(COLLECTION_REL, PAGE_REL),
            resource_type=OBJECT_VERSION_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
        )


class ObjectVersionsPageUpLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectVersion, page=True, relation=UP_REL
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, OntologyObject)
        return LinkGenerator.get_link_of(resource.resource, extra_relations=(UP_REL,))


class ObjectVersionsPageTypeLinkGenerator(
    LinkGenerator,
    resource_type=OntologyObjectVersion,
    page=True,
    relation=TYPE_REL_TYPE,
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, OntologyObject)
        return LinkGenerator.get_link_of(
            resource.resource.ontology_type, extra_relations=(NAV_REL,)
        )


class ObjectVersionsPageNamespaceLinkGenerator(
    LinkGenerator,
    resource_type=OntologyObjectVersion,
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
        assert isinstance(resource.resource, OntologyObject)
        return LinkGenerator.get_link_of(
            resource.resource.namespace, extra_relations=(NAV_REL,)
        )


# Type version #################################################################
class ObjectVersionKeyGenerator(KeyGenerator, resource_type=OntologyObjectVersion):
    def update_key(
        self, key: Dict[str, str], resource: OntologyObjectVersion
    ) -> Dict[str, str]:
        assert isinstance(resource, OntologyObjectVersion)
        key.update(KeyGenerator.generate_key(resource.ontology_object))
        key[OBJECT_VERSION_KEY] = str(resource.version)
        return key


class TaxonomyItemVersionSelfLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectVersion
):
    def generate_link(
        self,
        resource: OntologyObjectVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                TYPE_VERSION_RESOURCE,
                namespace=str(resource.ontology_object.namespace_id),
                object_type=str(resource.object_id),
                version=str(resource.version),
                _external=True,
            ),
            rel=tuple(),
            resource_type=OBJECT_VERSION_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource),
            schema=object_type_schema_url(resource.ontology_type_version),
            name=f"{resource.name} (v{resource.version})",
        )


class ObjectVersionApiObjectGenerator(
    ApiObjectGenerator, resource_type=OntologyObjectVersion
):
    def generate_api_object(
        self,
        resource: OntologyObjectVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[ObjectData]:
        assert isinstance(resource, OntologyObjectVersion)

        if not FLASK_OSO.is_allowed(resource, action=GET):
            return

        return ObjectData(
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
            name=resource.name,
            description=resource.description,
            created_on=resource.created_on,
            updated_on=resource.updated_on,
            deleted_on=resource.deleted_on,
            version=resource.version,
            data=resource.data,
        )


class ObjectVersionApiResponseGenerator(
    ApiResponseGenerator, resource_type=OntologyObjectVersion
):
    def generate_api_response(
        self, resource, *, link_to_relations: Optional[Iterable[str]], **kwargs
    ) -> Optional[ApiResponse]:
        link_to_relations = (
            OBJECT_VERSION_EXTRA_LINK_RELATIONS
            if link_to_relations is None
            else link_to_relations
        )
        return ApiResponseGenerator.default_generate_api_response(
            resource, link_to_relations=link_to_relations, **kwargs
        )


class ObjectVersionUpLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectVersion, relation=UP_REL
):
    def generate_link(
        self,
        resource: OntologyObjectVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectVersion)
        return LinkGenerator.get_link_of(
            PageResource(
                OntologyObjectVersion, resource=resource.ontology_object, page_number=1
            ),
            extra_relations=(UP_REL,),
        )


class ObjectVersionObjectLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectVersion, relation=OBJECT_REL_TYPE
):
    def generate_link(
        self,
        resource: OntologyObjectVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectVersion)
        return LinkGenerator.get_link_of(
            resource.ontology_object, extra_relations=(NAV_REL,)
        )


class ObjectVersionTypeVersionLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectVersion, relation=TYPE_VERSION_REL_TYPE
):
    def generate_link(
        self,
        resource: OntologyObjectVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectVersion)
        return LinkGenerator.get_link_of(
            resource.ontology_type_version, extra_relations=(NAV_REL,)
        )


class ObjectVersionNamespaceLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectVersion, relation=NAMESPACE_REL_TYPE
):
    def generate_link(
        self,
        resource: OntologyObjectVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectVersion)
        return LinkGenerator.get_link_of(
            resource.ontology_object.namespace, extra_relations=(NAV_REL,)
        )

"""Generators for all Namespace resources."""

from typing import Dict, Iterable, Optional

from flask import url_for

from muse_for_anything.api.base_models import ApiLink, ApiResponse
from muse_for_anything.api.v1_api.constants import (
    COLLECTION_REL,
    CREATE,
    CREATE_REL,
    DELETE,
    DELETE_REL,
    GET,
    ITEM_COUNT_DEFAULT,
    ITEM_COUNT_QUERY_KEY,
    NAMESPACE_EXTRA_LINK_RELATIONS,
    NAMESPACE_ID_KEY,
    NAMESPACE_PAGE_RESOURCE,
    NAMESPACE_REL_TYPE,
    NAMESPACE_RESOURCE,
    NAMESPACE_SCHEMA,
    NAV_REL,
    OBJECT_REL_TYPE,
    PAGE_REL,
    POST_REL,
    PUT_REL,
    RESTORE,
    RESTORE_REL,
    SCHEMA_RESOURCE,
    TAXONOMY_REL_TYPE,
    TYPE_REL_TYPE,
    UP_REL,
    UPDATE,
    UPDATE_REL,
)
from muse_for_anything.api.v1_api.models.ontology import NamespaceData
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
)
from muse_for_anything.db.models.taxonomies import Taxonomy
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource

# Namespace Page ###############################################################


class NamespacePageKeyGenerator(KeyGenerator, resource_type=Namespace, page=True):
    def update_key(self, key: Dict[str, str], resource: PageResource) -> Dict[str, str]:
        assert isinstance(resource, PageResource)
        assert resource.resource_type == Namespace
        return key


class NamespacePageLinkGenerator(LinkGenerator, resource_type=Namespace, page=True):
    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, str]],
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(
            OsoResource(NAMESPACE_REL_TYPE, is_collection=True), action=GET
        ):
            return
        if query_params is None:
            query_params = {ITEM_COUNT_QUERY_KEY: ITEM_COUNT_DEFAULT}
        return ApiLink(
            href=url_for(NAMESPACE_PAGE_RESOURCE, **query_params, _external=True),
            rel=(COLLECTION_REL, PAGE_REL),
            resource_type=NAMESPACE_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for(SCHEMA_RESOURCE, schema_id=NAMESPACE_SCHEMA, _external=True),
        )


class NamespacePageCreateNamespaceLinkGenerator(
    LinkGenerator, resource_type=Namespace, page=True, relation=CREATE_REL
):
    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(OsoResource(NAMESPACE_REL_TYPE), action=CREATE):
            return
        link = LinkGenerator.get_link_of(resource, query_params=query_params)
        link.rel = (CREATE_REL, POST_REL)
        return link


# Namespace ####################################################################


class NamespaceKeyGenerator(KeyGenerator, resource_type=Namespace):
    def update_key(self, key: Dict[str, str], resource: Namespace) -> Dict[str, str]:
        assert isinstance(resource, Namespace)
        key[NAMESPACE_ID_KEY] = str(resource.id)
        return key


class NamespaceSelfLinkGenerator(LinkGenerator, resource_type=Namespace):
    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(NAMESPACE_RESOURCE, namespace=str(resource.id), _external=True),
            rel=tuple(),
            resource_type=NAMESPACE_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(SCHEMA_RESOURCE, schema_id=NAMESPACE_SCHEMA, _external=True),
            name=resource.name,
        )


class NamespaceUpLinkGenerator(LinkGenerator, resource_type=Namespace, relation=UP_REL):
    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            PageResource(Namespace, page_number=1),
            extra_relations=(UP_REL,),
        )


class NamespaceObjectsNavLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation=OBJECT_REL_TYPE
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            PageResource(OntologyObject, resource=resource, page_number=1),
            extra_relations=(NAV_REL,),
        )


class NamespaceTypesNavLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation=TYPE_REL_TYPE
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            PageResource(OntologyObjectType, resource=resource, page_number=1),
            extra_relations=(NAV_REL,),
        )


class NamespaceTaxonomiesNavLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation=TAXONOMY_REL_TYPE
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            PageResource(Taxonomy, resource=resource, page_number=1),
            extra_relations=(NAV_REL,),
        )


class CreateNamespaceLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation=CREATE_REL
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Namespace)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(OsoResource(NAMESPACE_REL_TYPE), action=CREATE):
                return
        link = LinkGenerator.get_link_of(
            PageResource(Namespace, page_number=1),
            query_params={},
            ignore_deleted=ignore_deleted,
        )
        link.rel = (CREATE_REL, POST_REL)
        return link


class UpdateNamespaceLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation=UPDATE_REL
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Namespace)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=UPDATE):
                return  # not allowed
        if not ignore_deleted:
            if resource.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (UPDATE_REL, PUT_REL)
        return link


class DeleteNamespaceLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation=DELETE_REL
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=DELETE):
                return  # not allowed
        if not ignore_deleted:
            if resource.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (DELETE_REL,)
        return link


class RestoreNamespaceLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation=RESTORE_REL
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=RESTORE):
                return  # not allowed
        if not ignore_deleted:
            if not resource.is_deleted:
                return  # not deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (RESTORE_REL, POST_REL)
        return link


class NamespaceApiObjectGenerator(ApiObjectGenerator, resource_type=Namespace):
    def generate_api_object(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[NamespaceData]:
        assert isinstance(resource, Namespace)

        if not FLASK_OSO.is_allowed(resource, action=GET):
            return

        return NamespaceData(
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
            name=resource.name,
            description=resource.description,
            created_on=resource.created_on,
            updated_on=resource.updated_on,
            deleted_on=resource.deleted_on,
        )


class NamespaceApiResponseGenerator(ApiResponseGenerator, resource_type=Namespace):
    def generate_api_response(
        self, resource, *, link_to_relations: Optional[Iterable[str]], **kwargs
    ) -> Optional[ApiResponse]:
        link_to_relations = (
            NAMESPACE_EXTRA_LINK_RELATIONS
            if link_to_relations is None
            else link_to_relations
        )
        return ApiResponseGenerator.default_generate_api_response(
            resource, link_to_relations=link_to_relations, **kwargs
        )

"""Module containing resource and link generators for taxonomies."""

from typing import Any, Dict, Iterable, List, Optional, Union

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
    NAMESPACE_REL_TYPE,
    NAV_REL,
    PAGE_REL,
    POST_REL,
    PUT_REL,
    RESTORE,
    RESTORE_REL,
    SCHEMA_RESOURCE,
    TAXONOMY_EXTRA_LINK_RELATIONS,
    TAXONOMY_ID_KEY,
    TAXONOMY_ITEM_REL_TYPE,
    TAXONOMY_PAGE_RESOURCE,
    TAXONOMY_REL_TYPE,
    TAXONOMY_RESOURCE,
    TAXONOMY_SCHEMA,
    UP_REL,
    UPDATE,
    UPDATE_REL,
)
from muse_for_anything.api.v1_api.models.ontology import TaxonomyData
from muse_for_anything.api.v1_api.request_helpers import (
    ApiObjectGenerator,
    ApiResponseGenerator,
    KeyGenerator,
    LinkGenerator,
    PageResource,
)
from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.db.models.taxonomies import Taxonomy, TaxonomyItem
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource


# Taxonomies page ##############################################################
class TaxonomyPageKeyGenerator(KeyGenerator, resource_type=Taxonomy, page=True):
    def update_key(self, key: Dict[str, str], resource: PageResource) -> Dict[str, str]:
        assert isinstance(resource, PageResource)
        assert resource.resource_type == Taxonomy
        assert resource.resource is not None
        key.update(KeyGenerator.generate_key(resource.resource))
        return key


class TaxonomyPageLinkGenerator(LinkGenerator, resource_type=Taxonomy, page=True):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]],
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(
            OsoResource(
                TAXONOMY_REL_TYPE, is_collection=True, parent_resource=resource.resource
            ),
            action=GET,
        ):
            return
        namespace = resource.resource
        assert namespace is not None
        assert isinstance(namespace, Namespace)
        if query_params is None:
            query_params = {ITEM_COUNT_QUERY_KEY: ITEM_COUNT_DEFAULT}
        return ApiLink(
            href=url_for(
                TAXONOMY_PAGE_RESOURCE,
                namespace=str(namespace.id),
                **query_params,
                _external=True,
            ),
            rel=(COLLECTION_REL, PAGE_REL),
            resource_type=TAXONOMY_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for(SCHEMA_RESOURCE, schema_id=TAXONOMY_SCHEMA, _external=True),
        )


class TaxonomyPageCreateLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, page=True, relation=CREATE_REL
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert resource.resource is not None and isinstance(resource.resource, Namespace)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(
                OsoResource(TAXONOMY_REL_TYPE, parent_resource=resource.resource),
                action=CREATE,
            ):
                return
        if not ignore_deleted:
            if resource.resource.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(resource, query_params=query_params)
        link.rel = (CREATE_REL, POST_REL)
        return link


class TaxonomyPageUpLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, page=True, relation=UP_REL
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            resource.resource,
            extra_relations=(UP_REL,),
        )


class TaxonomyPageNamespacesNavLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, page=True, relation=NAMESPACE_REL_TYPE
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            PageResource(Namespace, page_number=1),
            extra_relations=(NAV_REL,),
        )


# Taxonomies ###################################################################
class TaxonomyKeyGenerator(KeyGenerator, resource_type=Taxonomy):
    def update_key(self, key: Dict[str, str], resource: Taxonomy) -> Dict[str, str]:
        assert isinstance(resource, Taxonomy)
        key.update(KeyGenerator.generate_key(resource.namespace))
        key[TAXONOMY_ID_KEY] = str(resource.id)
        return key


class TaxonomySelfLinkGenerator(LinkGenerator, resource_type=Taxonomy):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                TAXONOMY_RESOURCE,
                namespace=str(resource.namespace_id),
                taxonomy=str(resource.id),
                _external=True,
            ),
            rel=tuple(),
            resource_type=TAXONOMY_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(SCHEMA_RESOURCE, schema_id=TAXONOMY_SCHEMA, _external=True),
            name=resource.name,
        )


class TaxonomyApiObjectGenerator(ApiObjectGenerator, resource_type=Taxonomy):
    def generate_api_object(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[TaxonomyData]:
        assert isinstance(resource, Taxonomy)

        if not FLASK_OSO.is_allowed(resource, action=GET):
            return

        return TaxonomyData(
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
            name=resource.name,
            description=resource.description,
            created_on=resource.created_on,
            updated_on=resource.updated_on,
            deleted_on=resource.deleted_on,
            items=tuple(LinkGenerator.get_link_of(item) for item in resource.items),
        )


class TaxonomyApiResponseGenerator(ApiResponseGenerator, resource_type=Taxonomy):
    def generate_api_response(
        self, resource, *, link_to_relations: Optional[Iterable[str]], **kwargs
    ) -> Optional[ApiResponse]:
        link_to_relations = (
            TAXONOMY_EXTRA_LINK_RELATIONS
            if link_to_relations is None
            else link_to_relations
        )
        return ApiResponseGenerator.default_generate_api_response(
            resource, link_to_relations=link_to_relations, **kwargs
        )


class TaxonomyUpLinkGenerator(LinkGenerator, resource_type=Taxonomy, relation=UP_REL):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        return LinkGenerator.get_link_of(
            PageResource(Taxonomy, resource=resource.namespace, page_number=1),
            extra_relations=(UP_REL,),
        )


class TaxonomyNamespaceNavLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation=NAMESPACE_REL_TYPE
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        return LinkGenerator.get_link_of(
            resource.namespace,
            extra_relations=(NAV_REL,),
        )


class TaxonomyTaxonomyItemsNavLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation=TAXONOMY_ITEM_REL_TYPE
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        return LinkGenerator.get_link_of(
            PageResource(TaxonomyItem, resource=resource, page_number=1),
            extra_relations=(NAV_REL,),
        )


class CreateTaxonomyLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation=CREATE_REL
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        return LinkGenerator.get_link_of(
            PageResource(Taxonomy, resource=resource.namespace, page_number=1),
            query_params={},
            ignore_deleted=ignore_deleted,
            for_relation=CREATE_REL,
        )


class TaxonomyCreateTaxonomyItemLinkGenerator(
    LinkGenerator,
    resource_type=Taxonomy,
    relation=f"{CREATE_REL}_{TAXONOMY_ITEM_REL_TYPE}",
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(
                OsoResource(TAXONOMY_ITEM_REL_TYPE, parent_resource=resource),
                action=CREATE,
            ):
                return  # not allowed
        if not ignore_deleted:
            if resource.is_deleted or resource.namespace.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(
            PageResource(TaxonomyItem, resource=resource, page_number=1),
            query_params={},
            ignore_deleted=ignore_deleted,
        )
        link.rel = (CREATE_REL, POST_REL)
        return link


class UpdateTaxonomyLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation=UPDATE_REL
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=UPDATE):
                return  # not allowed
        if not ignore_deleted:
            if resource.is_deleted or resource.namespace.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (UPDATE_REL, PUT_REL)
        return link


class DeleteTaxonomyLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation=DELETE_REL
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=DELETE):
                return  # not allowed
        if not ignore_deleted:
            if resource.is_deleted or resource.namespace.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (DELETE_REL,)
        return link


class RestoreTaxonomyLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation=RESTORE_REL
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=RESTORE):
                return  # not allowed
        if not ignore_deleted:
            if (not resource.is_deleted) or resource.namespace.is_deleted:
                return  # not deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (RESTORE_REL, POST_REL)
        return link

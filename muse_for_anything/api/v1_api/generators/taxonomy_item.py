"""Module containing resource and link generators for taxonomy items."""

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
    TAXONOMY_ITEM_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_ID_KEY,
    TAXONOMY_ITEM_PAGE_RESOURCE,
    TAXONOMY_ITEM_RELATION_REL_TYPE,
    TAXONOMY_ITEM_REL_TYPE,
    TAXONOMY_ITEM_RESOURCE,
    TAXONOMY_ITEM_SCHEMA,
    TAXONOMY_ITEM_VERSION_REL_TYPE,
    TAXONOMY_REL_TYPE,
    UPDATE_REL,
    UP_REL,
    UPDATE,
)
from muse_for_anything.api.v1_api.models.ontology import (
    TaxonomyItemData,
)
from muse_for_anything.api.v1_api.request_helpers import (
    ApiObjectGenerator,
    ApiResponseGenerator,
    KeyGenerator,
    LinkGenerator,
    PageResource,
)
from muse_for_anything.db.models.taxonomies import (
    Taxonomy,
    TaxonomyItem,
    TaxonomyItemRelation,
    TaxonomyItemVersion,
)
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource


# Taxonomy items page ##########################################################
class TaxonomyItemsPageKeyGenerator(KeyGenerator, resource_type=TaxonomyItem, page=True):
    def update_key(self, key: Dict[str, str], resource: PageResource) -> Dict[str, str]:
        assert isinstance(resource, PageResource)
        assert resource.resource_type == TaxonomyItem
        assert resource.resource is not None
        key.update(KeyGenerator.generate_key(resource.resource))
        return key


class TaxonomyItemsPageLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, page=True
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]],
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(
            OsoResource(
                TAXONOMY_ITEM_REL_TYPE,
                is_collection=True,
                parent_resource=resource.resource,
            ),
            action=GET,
        ):
            return
        taxonomy = resource.resource
        assert taxonomy is not None
        assert isinstance(taxonomy, Taxonomy)
        if query_params is None:
            query_params = {ITEM_COUNT_QUERY_KEY: ITEM_COUNT_DEFAULT}
        return ApiLink(
            href=url_for(
                TAXONOMY_ITEM_PAGE_RESOURCE,
                namespace=str(taxonomy.namespace_id),
                taxonomy=str(taxonomy.id),
                **query_params,
                _external=True,
            ),
            rel=(COLLECTION_REL, PAGE_REL),
            resource_type=TAXONOMY_ITEM_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for(
                SCHEMA_RESOURCE, schema_id=TAXONOMY_ITEM_SCHEMA, _external=True
            ),
        )


class TaxonomyItemPageCreateLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, page=True, relation=CREATE_REL
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, Taxonomy)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(
                OsoResource(TAXONOMY_ITEM_REL_TYPE, parent_resource=resource.resource),
                action=CREATE,
            ):
                return  # not allowed
        if not ignore_deleted:
            if resource.resource.is_deleted or resource.resource.namespace.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(
            resource, query_params=query_params, ignore_deleted=ignore_deleted
        )
        link.rel = (CREATE_REL, POST_REL)
        return link


class TaxonomyItemPageUpLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, page=True, relation=UP_REL
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource.resource, Taxonomy)
        return LinkGenerator.get_link_of(
            resource.resource,
            extra_relations=(UP_REL,),
        )


class TaxonomyItemPageTaxonomiesNavLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, page=True, relation=TAXONOMY_REL_TYPE
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource.resource, Taxonomy)
        return LinkGenerator.get_link_of(
            PageResource(Taxonomy, resource=resource.resource.namespace, page_number=1),
            extra_relations=(NAV_REL,),
        )


class TaxonomyItemPageNamespaceNavLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, page=True, relation=NAMESPACE_REL_TYPE
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource.resource, Taxonomy)
        return LinkGenerator.get_link_of(
            resource.resource.namespace,
            extra_relations=(NAV_REL,),
        )


# taxonomy items ###############################################################
class TaxonomyItemKeyGenerator(KeyGenerator, resource_type=TaxonomyItem):
    def update_key(self, key: Dict[str, str], resource: TaxonomyItem) -> Dict[str, str]:
        assert isinstance(resource, TaxonomyItem)
        key.update(KeyGenerator.generate_key(resource.taxonomy))
        key[TAXONOMY_ITEM_ID_KEY] = str(resource.id)
        return key


class TaxonomyItemSelfLinkGenerator(LinkGenerator, resource_type=TaxonomyItem):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                TAXONOMY_ITEM_RESOURCE,
                namespace=str(resource.taxonomy.namespace_id),
                taxonomy=str(resource.taxonomy_id),
                taxonomy_item=str(resource.id),
                _external=True,
            ),
            rel=tuple(),
            resource_type=TAXONOMY_ITEM_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(
                SCHEMA_RESOURCE, schema_id=TAXONOMY_ITEM_SCHEMA, _external=True
            ),
            name=resource.name,
        )


class TaxonomyItemCreateLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation=CREATE_REL
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            PageResource(TaxonomyItem, resource=resource.taxonomy, page_number=1),
            query_params={},
            ignore_deleted=ignore_deleted,
            for_relation=CREATE_REL,
        )


class UpdateTaxonomyItemLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation=UPDATE_REL
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=UPDATE):
                return  # not allowed
        if not ignore_deleted:
            if (
                resource.is_deleted
                or resource.taxonomy.is_deleted
                or resource.taxonomy.namespace.is_deleted
            ):
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (UPDATE_REL, PUT_REL)
        return link


class DeleteTaxonomyItemLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation=DELETE_REL
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=DELETE):
                return  # not allowed
        if not ignore_deleted:
            if (
                resource.is_deleted
                or resource.taxonomy.is_deleted
                or resource.taxonomy.namespace.is_deleted
            ):
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (DELETE_REL,)
        return link


class RestoreTaxonomyItemLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation=RESTORE_REL
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=RESTORE):
                return  # not allowed
        if not ignore_deleted:
            if (
                (not resource.is_deleted)
                or resource.taxonomy.is_deleted
                or resource.taxonomy.namespace.is_deleted
            ):
                return  # not deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (RESTORE_REL, POST_REL)
        return link


class TaxonomyItemCreateItemRelationLinkGenerator(
    LinkGenerator,
    resource_type=TaxonomyItem,
    relation=f"{CREATE_REL}_{TAXONOMY_ITEM_RELATION_REL_TYPE}",
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            PageResource(TaxonomyItemRelation, resource=resource, page_number=1),
            query_params={},
            ignore_deleted=ignore_deleted,
            for_relation=CREATE_REL,
        )


class TaxonomyItemUpLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation=UP_REL
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            resource.taxonomy,
            extra_relations=(UP_REL,),
        )


class TaxonomyItemNamespaceLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation=NAMESPACE_REL_TYPE
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            resource.taxonomy.namespace,
            extra_relations=(NAV_REL,),
        )


class TaxonomyItemTaxonomiesLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation=TAXONOMY_REL_TYPE
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            PageResource(Taxonomy, resource=resource.taxonomy.namespace, page_number=1),
            extra_relations=(NAV_REL,),
        )


class TaxonomyItemItemRelationsLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation=TAXONOMY_ITEM_RELATION_REL_TYPE
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            PageResource(TaxonomyItemRelation, resource=resource, page_number=1),
            extra_relations=(NAV_REL,),
        )


class TaxonomyItemItemVersionsLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation=TAXONOMY_ITEM_VERSION_REL_TYPE
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            PageResource(TaxonomyItemVersion, resource=resource, page_number=1),
            extra_relations=(NAV_REL,),
        )


class TaxonomyItemApiObjectGenerator(ApiObjectGenerator, resource_type=TaxonomyItem):
    def generate_api_object(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[TaxonomyItemData]:
        assert isinstance(resource, TaxonomyItem)

        if not FLASK_OSO.is_allowed(resource, action=GET):
            return

        parents = [
            LinkGenerator.get_link_of(parent.taxonomy_item_source)
            for parent in resource.current_ancestors
        ]
        children = [
            LinkGenerator.get_link_of(child) for child in resource.current_related
        ]

        return TaxonomyItemData(
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
            name=resource.name,
            description=resource.description,
            sort_key=resource.sort_key,
            version=resource.version,
            parents=parents,
            children=children,
            created_on=resource.created_on,
            updated_on=resource.updated_on,
            deleted_on=resource.deleted_on,
        )


class TaxonomyItemApiResponseGenerator(ApiResponseGenerator, resource_type=TaxonomyItem):
    def generate_api_response(
        self, resource, *, link_to_relations: Optional[Iterable[str]], **kwargs
    ) -> Optional[ApiResponse]:
        link_to_relations = (
            TAXONOMY_ITEM_EXTRA_LINK_RELATIONS
            if link_to_relations is None
            else link_to_relations
        )
        return ApiResponseGenerator.default_generate_api_response(
            resource, link_to_relations=link_to_relations, **kwargs
        )

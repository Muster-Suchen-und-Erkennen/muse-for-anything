"""Module containing resource and link generators for taxonomy item versions."""

from typing import Dict, Iterable, Optional

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
    TAXONOMY_ITEM_RELATION_REL_TYPE,
    TAXONOMY_ITEM_SCHEMA,
    TAXONOMY_ITEM_VERSION_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_VERSION_PAGE_RESOURCE,
    TAXONOMY_ITEM_VERSION_REL_TYPE,
    TAXONOMY_ITEM_VERSION_RESOURCE,
    TAXONOMY_REL_TYPE,
    UP_REL,
    VERSION_KEY,
)
from muse_for_anything.api.v1_api.models.ontology import TaxonomyItemData
from muse_for_anything.api.v1_api.request_helpers import (
    ApiObjectGenerator,
    ApiResponseGenerator,
    KeyGenerator,
    LinkGenerator,
    PageResource,
)
from muse_for_anything.db.models.taxonomies import (
    TaxonomyItem,
    TaxonomyItemRelation,
    TaxonomyItemVersion,
)
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource


# taxonomy item versions page ##################################################
class TaxonomyItemVersionsPageKeyGenerator(
    KeyGenerator, resource_type=TaxonomyItemVersion, page=True
):
    def update_key(self, key: Dict[str, str], resource: PageResource) -> Dict[str, str]:
        assert isinstance(resource, PageResource)
        assert resource.resource_type == TaxonomyItemVersion
        assert resource.resource is not None
        key.update(KeyGenerator.generate_key(resource.resource))
        return key


class TaxonomyItemVersionsPageSelfLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion, page=True
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
                TAXONOMY_ITEM_VERSION_REL_TYPE,
                is_collection=True,
                parent_resource=resource.resource,
            ),
            action=GET,
        ):
            return
        taxonomy_item = resource.resource
        assert taxonomy_item is not None
        assert isinstance(taxonomy_item, TaxonomyItem)
        if query_params is None:
            query_params = {ITEM_COUNT_QUERY_KEY: ITEM_COUNT_DEFAULT}
        return ApiLink(
            href=url_for(
                TAXONOMY_ITEM_VERSION_PAGE_RESOURCE,
                namespace=str(taxonomy_item.taxonomy.namespace_id),
                taxonomy=str(taxonomy_item.taxonomy_id),
                taxonomy_item=str(taxonomy_item.id),
                **query_params,
                _external=True,
            ),
            rel=(COLLECTION_REL, PAGE_REL),
            resource_type=TAXONOMY_ITEM_VERSION_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for(
                SCHEMA_RESOURCE, schema_id=TAXONOMY_ITEM_SCHEMA, _external=True
            ),
        )


class TaxonomyItemVersionsPageUpLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion, page=True, relation=UP_REL
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, TaxonomyItem)
        return LinkGenerator.get_link_of(resource.resource, extra_relations=(UP_REL,))


class TaxonomyItemVersionsPageTaxonomyLinkGenerator(
    LinkGenerator,
    resource_type=TaxonomyItemVersion,
    page=True,
    relation=TAXONOMY_REL_TYPE,
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            resource.resource.taxonomy, extra_relations=(NAV_REL,)
        )


class TaxonomyItemVersionsPageNamespaceLinkGenerator(
    LinkGenerator,
    resource_type=TaxonomyItemVersion,
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
        assert isinstance(resource.resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            resource.resource.taxonomy.namespace, extra_relations=(NAV_REL,)
        )


# taxonomy item versions #######################################################
class TaxonomyItemVersionKeyGenerator(KeyGenerator, resource_type=TaxonomyItemVersion):
    def update_key(
        self, key: Dict[str, str], resource: TaxonomyItemVersion
    ) -> Dict[str, str]:
        assert isinstance(resource, TaxonomyItemVersion)
        key.update(KeyGenerator.generate_key(resource.taxonomy_item))
        key[VERSION_KEY] = str(resource.version)
        return key


class TaxonomyItemVersionSelfLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion
):
    def generate_link(
        self,
        resource: TaxonomyItemVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                TAXONOMY_ITEM_VERSION_RESOURCE,
                namespace=str(resource.taxonomy_item.taxonomy.namespace_id),
                taxonomy=str(resource.taxonomy_item.taxonomy_id),
                taxonomy_item=str(resource.taxonomy_item_id),
                version=str(resource.version),
                _external=True,
            ),
            rel=tuple(),
            resource_type=TAXONOMY_ITEM_VERSION_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(
                SCHEMA_RESOURCE, schema_id=TAXONOMY_ITEM_SCHEMA, _external=True
            ),
            name=f"{resource.name} (v{resource.version})",
        )


class TaxonomyItemVersionUpLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion, relation=UP_REL
):
    def generate_link(
        self,
        resource: TaxonomyItemVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemVersion)
        return LinkGenerator.get_link_of(
            resource.taxonomy_item, extra_relations=(UP_REL,)
        )


class TaxonomyItemVersionTaxonomyItemRelationsLinkGenerator(
    LinkGenerator,
    resource_type=TaxonomyItemVersion,
    relation=TAXONOMY_ITEM_RELATION_REL_TYPE,
):
    def generate_link(
        self,
        resource: TaxonomyItemVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemVersion)
        return LinkGenerator.get_link_of(
            PageResource(
                TaxonomyItemRelation, resource=resource.taxonomy_item, page_number=1
            ),
            extra_relations=(NAV_REL,),
        )


class TaxonomyItemVersionTaxonomyLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion, relation=TAXONOMY_REL_TYPE
):
    def generate_link(
        self,
        resource: TaxonomyItemVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemVersion)
        return LinkGenerator.get_link_of(
            resource.taxonomy_item.taxonomy, extra_relations=(NAV_REL,)
        )


class TaxonomyItemVersionNamespaceLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion, relation=NAMESPACE_REL_TYPE
):
    def generate_link(
        self,
        resource: TaxonomyItemVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemVersion)
        return LinkGenerator.get_link_of(
            resource.taxonomy_item.taxonomy.namespace, extra_relations=(NAV_REL,)
        )


class TaxonomyItemVersionApiObjectGenerator(
    ApiObjectGenerator, resource_type=TaxonomyItemVersion
):
    def generate_api_object(
        self,
        resource: TaxonomyItemVersion,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[TaxonomyItemData]:
        assert isinstance(resource, TaxonomyItemVersion)

        if not FLASK_OSO.is_allowed(resource, action=GET):
            return

        parents = [
            LinkGenerator.get_link_of(parent.taxonomy_item_source)
            for parent in resource.taxonomy_item.current_ancestors
        ]
        children = [
            LinkGenerator.get_link_of(child)
            for child in resource.taxonomy_item.current_related
        ]

        return TaxonomyItemData(
            self=LinkGenerator.get_link_of(resource, query_params=query_params, ignore_deleted=True),
            name=resource.name,
            description=resource.description,
            sort_key=resource.sort_key,
            version=resource.version,
            parents=parents,
            children=children,
            created_on=resource.created_on,
            updated_on=resource.created_on,
            deleted_on=resource.deleted_on,
        )


class TaxonomyItemVersionApiResponseGenerator(
    ApiResponseGenerator, resource_type=TaxonomyItemVersion
):
    def generate_api_response(
        self, resource, *, link_to_relations: Optional[Iterable[str]], **kwargs
    ) -> Optional[ApiResponse]:
        link_to_relations = (
            TAXONOMY_ITEM_VERSION_EXTRA_LINK_RELATIONS
            if link_to_relations is None
            else link_to_relations
        )
        return ApiResponseGenerator.default_generate_api_response(
            resource, link_to_relations=link_to_relations, **kwargs
        )

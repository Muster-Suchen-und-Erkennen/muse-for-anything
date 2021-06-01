"""Module containing resource and link generators for taxonomy item relations."""

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
    NAMESPACE_REL_TYPE,
    NAV_REL,
    PAGE_REL,
    POST_REL,
    SCHEMA_RESOURCE,
    TAXONOMY_ITEM_RELATION_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_RELATION_ID_KEY,
    TAXONOMY_ITEM_RELATION_PAGE_RESOURCE,
    TAXONOMY_ITEM_RELATION_POST_SCHEMA,
    TAXONOMY_ITEM_RELATION_REL_TYPE,
    TAXONOMY_ITEM_RELATION_RESOURCE,
    TAXONOMY_ITEM_RELATION_SCHEMA,
    TAXONOMY_REL_TYPE,
    UP_REL,
)
from muse_for_anything.api.v1_api.models.ontology import TaxonomyItemRelationData
from muse_for_anything.api.v1_api.request_helpers import (
    ApiObjectGenerator,
    ApiResponseGenerator,
    KeyGenerator,
    LinkGenerator,
    PageResource,
)
from muse_for_anything.db.models.taxonomies import TaxonomyItem, TaxonomyItemRelation
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource


# taxonomy item relations page #################################################
class TaxonomyItemRelationsPageKeyGenerator(
    KeyGenerator, resource_type=TaxonomyItemRelation, page=True
):
    def update_key(self, key: Dict[str, str], resource: PageResource) -> Dict[str, str]:
        assert isinstance(resource, PageResource)
        assert resource.resource_type == TaxonomyItemRelation
        assert resource.resource is not None
        key.update(KeyGenerator.generate_key(resource.resource))
        return key


class TaxonomyItemRelationsPageLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, page=True
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
                TAXONOMY_ITEM_RELATION_REL_TYPE,
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
            query_params = {"item-count": "25"}
        return ApiLink(
            href=url_for(
                TAXONOMY_ITEM_RELATION_PAGE_RESOURCE,
                namespace=str(taxonomy_item.taxonomy.namespace_id),
                taxonomy=str(taxonomy_item.taxonomy_id),
                taxonomy_item=str(taxonomy_item.id),
                **query_params,
                _external=True,
            ),
            rel=(COLLECTION_REL, PAGE_REL),
            resource_type=TAXONOMY_ITEM_RELATION_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for(
                SCHEMA_RESOURCE, schema_id=TAXONOMY_ITEM_RELATION_SCHEMA, _external=True
            ),
        )


class TaxonomyItemRelationsPageCreateLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, page=True, relation=CREATE_REL
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
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(
                OsoResource(
                    TAXONOMY_ITEM_RELATION_REL_TYPE, parent_resource=resource.resource
                ),
                action=CREATE,
            ):
                return  # not allowed
        if not ignore_deleted:
            if (
                resource.resource.is_deleted
                or resource.resource.taxonomy.is_deleted
                or resource.resource.taxonomy.namespace.is_deleted
            ):
                return  # deleted
        link = LinkGenerator.get_link_of(
            resource, query_params=query_params, ignore_deleted=ignore_deleted
        )
        link.rel = (CREATE_REL, POST_REL)
        link.schema = url_for(
            SCHEMA_RESOURCE, schema_id=TAXONOMY_ITEM_RELATION_POST_SCHEMA, _external=True
        )
        return link


class TaxonomyItemRelationsPageUpLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, page=True, relation=UP_REL
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


class TaxonomyItemRelationsPageTaxonomyLinkGenerator(
    LinkGenerator,
    resource_type=TaxonomyItemRelation,
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


class TaxonomyItemRelationsPageNamespaceLinkGenerator(
    LinkGenerator,
    resource_type=TaxonomyItemRelation,
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


# taxonomy item relations ######################################################
class TaxonomyItemRelationKeyGenerator(KeyGenerator, resource_type=TaxonomyItemRelation):
    def update_key(
        self, key: Dict[str, str], resource: TaxonomyItemRelation
    ) -> Dict[str, str]:
        assert isinstance(resource, TaxonomyItemRelation)
        key.update(KeyGenerator.generate_key(resource.taxonomy_item_source))
        key[TAXONOMY_ITEM_RELATION_ID_KEY] = str(resource.id)
        return key


class TaxonomyItemRelationSelfLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation
):
    def generate_link(
        self,
        resource: TaxonomyItemRelation,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                TAXONOMY_ITEM_RELATION_RESOURCE,
                namespace=str(resource.taxonomy_item_source.taxonomy.namespace_id),
                taxonomy=str(resource.taxonomy_item_source.taxonomy_id),
                taxonomy_item=str(resource.taxonomy_item_source_id),
                relation=str(resource.id),
                _external=True,
            ),
            rel=tuple(),
            resource_type=TAXONOMY_ITEM_RELATION_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(
                SCHEMA_RESOURCE, schema_id=TAXONOMY_ITEM_RELATION_SCHEMA, _external=True
            ),
        )


class DeleteTaxonomyItemRelationLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, relation=DELETE_REL
):
    def generate_link(
        self,
        resource: TaxonomyItemRelation,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemRelation)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=DELETE):
                return  # not allowed
        if not ignore_deleted:
            if (
                resource.is_deleted
                or resource.taxonomy_item_source.is_deleted
                or resource.taxonomy_item_source.taxonomy.is_deleted
                or resource.taxonomy_item_source.taxonomy.namespace.is_deleted
            ):
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (DELETE_REL,)
        return link


class TaxonomyItemRelationUpLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, relation=UP_REL
):
    def generate_link(
        self,
        resource: TaxonomyItemRelation,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemRelation)
        return LinkGenerator.get_link_of(
            resource.taxonomy_item_source, extra_relations=(UP_REL,)
        )


class TaxonomyItemRelationTaxonomyLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, relation=TAXONOMY_REL_TYPE
):
    def generate_link(
        self,
        resource: TaxonomyItemRelation,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemRelation)
        return LinkGenerator.get_link_of(
            resource.taxonomy_item_source.taxonomy, extra_relations=(NAV_REL,)
        )


class TaxonomyItemRelationNamespaceLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, relation=NAMESPACE_REL_TYPE
):
    def generate_link(
        self,
        resource: TaxonomyItemRelation,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemRelation)
        return LinkGenerator.get_link_of(
            resource.taxonomy_item_source.taxonomy.namespace, extra_relations=(NAV_REL,)
        )


class TaxonomyItemRelationApiObjectGenerator(
    ApiObjectGenerator, resource_type=TaxonomyItemRelation
):
    def generate_api_object(
        self,
        resource: TaxonomyItemRelation,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[TaxonomyItemRelationData]:
        assert isinstance(resource, TaxonomyItemRelation)

        if not FLASK_OSO.is_allowed(resource, action=GET):
            return

        return TaxonomyItemRelationData(
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
            source_item=LinkGenerator.get_link_of(resource.taxonomy_item_source),
            target_item=LinkGenerator.get_link_of(resource.taxonomy_item_target),
            created_on=resource.created_on,
            deleted_on=resource.deleted_on,
        )


class TaxonomyItemRelationApiResponseGenerator(
    ApiResponseGenerator, resource_type=TaxonomyItemRelation
):
    def generate_api_response(
        self, resource, *, link_to_relations: Optional[Iterable[str]], **kwargs
    ) -> Optional[ApiResponse]:
        link_to_relations = (
            TAXONOMY_ITEM_RELATION_EXTRA_LINK_RELATIONS
            if link_to_relations is None
            else link_to_relations
        )
        return ApiResponseGenerator.default_generate_api_response(
            resource, link_to_relations=link_to_relations, **kwargs
        )

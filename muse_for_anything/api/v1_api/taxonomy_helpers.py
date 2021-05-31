"""Module containing resource and link generators for taxonomies and related resources."""

from typing import Any, Dict, Iterable, List, Optional, Union
from flask import url_for

from muse_for_anything.db.models.namespace import Namespace

from muse_for_anything.api.base_models import (
    ApiLink,
    ApiResponse,
)
from muse_for_anything.api.v1_api.models.ontology import (
    TaxonomyData,
    TaxonomyItemData,
    TaxonomyItemRelationData,
)
from muse_for_anything.db.models.taxonomies import (
    Taxonomy,
    TaxonomyItem,
    TaxonomyItemRelation,
    TaxonomyItemVersion,
)


from .request_helpers import (
    ApiObjectGenerator,
    ApiResponseGenerator,
    KeyGenerator,
    LinkGenerator,
    PageResource,
)

from ...oso_helpers import FLASK_OSO, OsoResource


TAXONOMY_PAGE_EXTRA_LINK_RELATIONS = ("ont-namespace",)
TAXONOMY_EXTRA_LINK_RELATIONS = (
    "ont-taxonomy-item",
    "ont-namespace",
    "create_ont-taxonomy-item",
)
TAXONOMY_ITEM_PAGE_EXTRA_LINK_RELATIONS = (
    "ont-namespace",
    "ont-taxonomy",
)
TAXONOMY_ITEM_EXTRA_LINK_RELATIONS = (
    "ont-namespace",
    "ont-taxonomy",
    "ont-taxonomy-item-relation",
    "ont-taxonomy-item-version",
    "create_ont-taxonomy-item-relation",
)
TAXONOMY_ITEM_RELATION_PAGE_EXTRA_LINK_RELATIONS = (
    "ont-namespace",
    "ont-taxonomy",
)
TAXONOMY_ITEM_RELATION_EXTRA_LINK_RELATIONS = (
    "ont-namespace",
    "ont-taxonomy",
)
TAXONOMY_ITEM_VERSION_PAGE_EXTRA_LINK_RELATIONS = (
    "ont-namespace",
    "ont-taxonomy",
)
TAXONOMY_ITEM_VERSION_EXTRA_LINK_RELATIONS = (
    "ont-namespace",
    "ont-taxonomy",
    "ont-taxonomy-item-relation",
)

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
        query_params: Optional[Dict[str, Union[str, int, float]]],
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(
            OsoResource(
                "ont-taxonomy", is_collection=True, parent_resource=resource.resource
            ),
            action="GET",
        ):
            return
        namespace = resource.resource
        assert namespace is not None
        assert isinstance(namespace, Namespace)
        if query_params is None:
            query_params = {"item-count": 25}
        return ApiLink(
            href=url_for(
                "api-v1.TaxonomiesView",
                namespace=str(namespace.id),
                **query_params,
                _external=True,
            ),
            rel=("collection", "page"),
            resource_type="ont-taxonomy",
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
        )


class TaxonomyPageCreateLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, page=True, relation="create"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert resource.resource is not None and isinstance(resource.resource, Namespace)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(
                OsoResource("ont-taxonomy", parent_resource=resource.resource),
                action="CREATE",
            ):
                return
        if not ignore_deleted:
            if resource.resource.is_deleted:
                return  # not deleted
        link = LinkGenerator.get_link_of(resource, query_params=query_params)
        link.rel = ("create", "post")
        return link


class TaxonomyPageUpLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, page=True, relation="up"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            resource.resource,
            extra_relations=("up",),
        )


class TaxonomyPageNamespacesNavLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, page=True, relation="ont-namespace"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            PageResource(Namespace, page_number=1),
            extra_relations=("nav",),
        )


# Taxonomies ###################################################################
class TaxonomyKeyGenerator(KeyGenerator, resource_type=Taxonomy):
    def update_key(self, key: Dict[str, str], resource: Taxonomy) -> Dict[str, str]:
        assert isinstance(resource, Taxonomy)
        key.update(KeyGenerator.generate_key(resource.namespace))
        key["taxonomyId"] = str(resource.id)
        return key


class TaxonomySelfLinkGenerator(LinkGenerator, resource_type=Taxonomy):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                "api-v1.TaxonomyView",
                namespace=str(resource.namespace_id),
                taxonomy=str(resource.id),
                _external=True,
            ),
            rel=tuple(),
            resource_type="ont-taxonomy",
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
            name=resource.name,
        )


class TaxonomyApiObjectGenerator(ApiObjectGenerator, resource_type=Taxonomy):
    def generate_api_object(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
    ) -> Optional[TaxonomyData]:
        assert isinstance(resource, Taxonomy)

        if not FLASK_OSO.is_allowed(resource, action="GET"):
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


class TaxonomyUpLinkGenerator(LinkGenerator, resource_type=Taxonomy, relation="up"):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        return LinkGenerator.get_link_of(
            PageResource(Taxonomy, resource=resource.namespace, page_number=1),
            extra_relations=("up",),
        )


class TaxonomyNamespaceNavLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation="ont-namespace"
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        return LinkGenerator.get_link_of(
            resource.namespace,
            extra_relations=("nav",),
        )


class TaxonomyTaxonomyItemsNavLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation="ont-taxonomy-item"
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        return LinkGenerator.get_link_of(
            PageResource(TaxonomyItem, resource=resource, page_number=1),
            extra_relations=("nav",),
        )


class CreateTaxonomyLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation="create"
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        return LinkGenerator.get_link_of(
            PageResource(Taxonomy, resource=resource.namespace, page_number=1),
            query_params={},
            ignore_deleted=ignore_deleted,
            for_relation="create",
        )


class TaxonomyCreateTaxonomyItemLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation="create_ont-taxonomy-item"
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(
                OsoResource("ont-taxonomy-item", parent_resource=resource),
                action="CREATE",
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
        link.rel = ("create", "post")
        return link


class UpdateTaxonomyLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation="update"
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action="EDIT"):
                return  # not allowed
        if not ignore_deleted:
            if resource.is_deleted or resource.namespace.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = ("update", "put")
        return link


class DeleteTaxonomyLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation="delete"
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action="DELETE"):
                return  # not allowed
        if not ignore_deleted:
            if resource.is_deleted or resource.namespace.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = ("delete",)
        return link


class RestoreTaxonomyLinkGenerator(
    LinkGenerator, resource_type=Taxonomy, relation="restore"
):
    def generate_link(
        self,
        resource: Taxonomy,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Taxonomy)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action="RESTORE"):
                return  # not allowed
        if not ignore_deleted:
            if (not resource.is_deleted) or resource.namespace.is_deleted:
                return  # not deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = ("restore", "post")
        return link


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
        query_params: Optional[Dict[str, Union[str, int, float]]],
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(
            OsoResource(
                "ont-taxonomy-item", is_collection=True, parent_resource=resource.resource
            ),
            action="GET",
        ):
            return
        taxonomy = resource.resource
        assert taxonomy is not None
        assert isinstance(taxonomy, Taxonomy)
        if query_params is None:
            query_params = {"item-count": 25}
        return ApiLink(
            href=url_for(
                "api-v1.TaxonomyItemsView",
                namespace=str(taxonomy.namespace_id),
                taxonomy=str(taxonomy.id),
                **query_params,
                _external=True,
            ),
            rel=("collection", "page"),
            resource_type="ont-taxonomy-item",
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomyItemSchema", _external=True
            ),
        )


class TaxonomyItemPageCreateLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, page=True, relation="create"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, Taxonomy)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(
                OsoResource("ont-taxonomy-item", parent_resource=resource.resource),
                action="CREATE",
            ):
                return  # not allowed
        if not ignore_deleted:
            if resource.resource.is_deleted or resource.resource.namespace.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(
            resource, query_params=query_params, ignore_deleted=ignore_deleted
        )
        link.rel = ("create", "post")
        return link


class TaxonomyItemPageUpLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, page=True, relation="up"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource.resource, Taxonomy)
        return LinkGenerator.get_link_of(
            resource.resource,
            extra_relations=("up",),
        )


class TaxonomyItemPageTaxonomiesNavLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, page=True, relation="ont-taxonomy"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource.resource, Taxonomy)
        return LinkGenerator.get_link_of(
            PageResource(Taxonomy, resource=resource.resource.namespace, page_number=1),
            extra_relations=("nav",),
        )


class TaxonomyItemPageNamespaceNavLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, page=True, relation="ont-namespace"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource.resource, Taxonomy)
        return LinkGenerator.get_link_of(
            resource.resource.namespace,
            extra_relations=("nav",),
        )


# taxonomy items ###############################################################
class TaxonomyItemKeyGenerator(KeyGenerator, resource_type=TaxonomyItem):
    def update_key(self, key: Dict[str, str], resource: TaxonomyItem) -> Dict[str, str]:
        assert isinstance(resource, TaxonomyItem)
        key.update(KeyGenerator.generate_key(resource.taxonomy))
        key["taxonomyItemId"] = str(resource.id)
        return key


class TaxonomyItemSelfLinkGenerator(LinkGenerator, resource_type=TaxonomyItem):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                "api-v1.TaxonomyItemView",
                namespace=str(resource.taxonomy.namespace_id),
                taxonomy=str(resource.taxonomy_id),
                taxonomy_item=str(resource.id),
                _external=True,
            ),
            rel=tuple(),
            resource_type="ont-taxonomy-item",
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomyItemSchema", _external=True
            ),
            name=resource.name,
        )


class TaxonomyItemCreateLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation="create"
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            PageResource(TaxonomyItem, resource=resource.taxonomy, page_number=1),
            query_params={},
            ignore_deleted=ignore_deleted,
            for_relation="create",
        )


class UpdateTaxonomyItemLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation="update"
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action="EDIT"):
                return  # not allowed
        if not ignore_deleted:
            if (
                resource.is_deleted
                or resource.taxonomy.is_deleted
                or resource.taxonomy.namespace.is_deleted
            ):
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = ("update", "put")
        return link


class DeleteTaxonomyItemLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation="delete"
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action="DELETE"):
                return  # not allowed
        if not ignore_deleted:
            if (
                resource.is_deleted
                or resource.taxonomy.is_deleted
                or resource.taxonomy.namespace.is_deleted
            ):
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = ("delete",)
        return link


class RestoreTaxonomyItemLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation="restore"
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action="RESTORE"):
                return  # not allowed
        if not ignore_deleted:
            if (
                (not resource.is_deleted)
                or resource.taxonomy.is_deleted
                or resource.taxonomy.namespace.is_deleted
            ):
                return  # not deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = ("restore", "post")
        return link


class TaxonomyItemCreateItemRelationLinkGenerator(
    LinkGenerator,
    resource_type=TaxonomyItem,
    relation="create_ont-taxonomy-item-relation",
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            PageResource(TaxonomyItemRelation, resource=resource, page_number=1),
            query_params={},
            ignore_deleted=ignore_deleted,
            for_relation="create",
        )


class TaxonomyItemUpLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation="up"
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            resource.taxonomy,
            extra_relations=("up",),
        )


class TaxonomyItemNamespaceLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation="ont-namespace"
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            resource.taxonomy.namespace,
            extra_relations=("nav",),
        )


class TaxonomyItemTaxonomiesLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation="ont-taxonomy"
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            PageResource(Taxonomy, resource=resource.taxonomy.namespace, page_number=1),
            extra_relations=("nav",),
        )


class TaxonomyItemItemRelationsLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation="ont-taxonomy-item-relation"
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            PageResource(TaxonomyItemRelation, resource=resource, page_number=1),
            extra_relations=("nav",),
        )


class TaxonomyItemItemVersionsLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItem, relation="ont-taxonomy-item-version"
):
    def generate_link(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            PageResource(TaxonomyItemVersion, resource=resource, page_number=1),
            extra_relations=("nav",),
        )


class TaxonomyItemApiObjectGenerator(ApiObjectGenerator, resource_type=TaxonomyItem):
    def generate_api_object(
        self,
        resource: TaxonomyItem,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
    ) -> Optional[TaxonomyItemData]:
        assert isinstance(resource, TaxonomyItem)

        if not FLASK_OSO.is_allowed(resource, action="GET"):
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
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(
            OsoResource(
                "ont-taxonomy-item-version",
                is_collection=True,
                parent_resource=resource.resource,
            ),
            action="GET",
        ):
            return
        taxonomy_item = resource.resource
        assert taxonomy_item is not None
        assert isinstance(taxonomy_item, TaxonomyItem)
        if query_params is None:
            query_params = {"item-count": 25}
        return ApiLink(
            href=url_for(
                "api-v1.TaxonomyItemVersionsView",
                namespace=str(taxonomy_item.taxonomy.namespace_id),
                taxonomy=str(taxonomy_item.taxonomy_id),
                taxonomy_item=str(taxonomy_item.id),
                _external=True,
            ),
            rel=("collection", "page"),
            resource_type="ont-taxonomy-item-version",
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomyItemSchema", _external=True
            ),
        )


class TaxonomyItemVersionsPageUpLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion, page=True, relation="up"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, TaxonomyItem)
        return LinkGenerator.get_link_of(resource.resource, extra_relations=("up",))


class TaxonomyItemVersionsPageTaxonomyLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion, page=True, relation="ont-taxonomy"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            resource.resource.taxonomy, extra_relations=("nav",)
        )


class TaxonomyItemVersionsPageNamespaceLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion, page=True, relation="ont-namespace"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            resource.resource.taxonomy.namespace, extra_relations=("nav",)
        )


# taxonomy item versions #######################################################
class TaxonomyItemVersionKeyGenerator(KeyGenerator, resource_type=TaxonomyItemVersion):
    def update_key(
        self, key: Dict[str, str], resource: TaxonomyItemVersion
    ) -> Dict[str, str]:
        assert isinstance(resource, TaxonomyItemVersion)
        key.update(KeyGenerator.generate_key(resource.taxonomy_item))
        key["version"] = str(resource.version)
        return key


class TaxonomyItemVersionSelfLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion
):
    def generate_link(
        self,
        resource: TaxonomyItemVersion,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                "api-v1.TaxonomyItemVersionView",
                namespace=str(resource.taxonomy_item.taxonomy.namespace_id),
                taxonomy=str(resource.taxonomy_item.taxonomy_id),
                taxonomy_item=str(resource.taxonomy_item_id),
                version=str(resource.version),
                _external=True,
            ),
            rel=tuple(),
            resource_type="ont-taxonomy-item-version",
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomyItemSchema", _external=True
            ),
            name=resource.name,
        )


class TaxonomyItemVersionUpLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion, relation="up"
):
    def generate_link(
        self,
        resource: TaxonomyItemVersion,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemVersion)
        return LinkGenerator.get_link_of(resource.taxonomy_item, extra_relations=("up",))


class TaxonomyItemVersionTaxonomyItemRelationsLinkGenerator(
    LinkGenerator,
    resource_type=TaxonomyItemVersion,
    relation="ont-taxonomy-item-relation",
):
    def generate_link(
        self,
        resource: TaxonomyItemVersion,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemVersion)
        return LinkGenerator.get_link_of(
            PageResource(
                TaxonomyItemRelation, resource=resource.taxonomy_item, page_number=1
            ),
            extra_relations=("nav",),
        )


class TaxonomyItemVersionTaxonomyLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion, relation="ont-taxonomy"
):
    def generate_link(
        self,
        resource: TaxonomyItemVersion,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemVersion)
        return LinkGenerator.get_link_of(
            resource.taxonomy_item.taxonomy, extra_relations=("nav",)
        )


class TaxonomyItemVersionNamespaceLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemVersion, relation="ont-namespace"
):
    def generate_link(
        self,
        resource: TaxonomyItemVersion,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemVersion)
        return LinkGenerator.get_link_of(
            resource.taxonomy_item.taxonomy.namespace, extra_relations=("nav",)
        )


class TaxonomyItemVersionApiObjectGenerator(
    ApiObjectGenerator, resource_type=TaxonomyItemVersion
):
    def generate_api_object(
        self,
        resource: TaxonomyItemVersion,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
    ) -> Optional[TaxonomyItemData]:
        assert isinstance(resource, TaxonomyItemVersion)

        if not FLASK_OSO.is_allowed(resource, action="GET"):
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
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
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
        query_params: Optional[Dict[str, Union[str, int, float]]],
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(
            OsoResource(
                "ont-taxonomy-item-relation",
                is_collection=True,
                parent_resource=resource.resource,
            ),
            action="GET",
        ):
            return
        taxonomy_item = resource.resource
        assert taxonomy_item is not None
        assert isinstance(taxonomy_item, TaxonomyItem)
        if query_params is None:
            query_params = {"item-count": 25}
        return ApiLink(
            href=url_for(
                "api-v1.TaxonomyItemRelationsView",
                namespace=str(taxonomy_item.taxonomy.namespace_id),
                taxonomy=str(taxonomy_item.taxonomy_id),
                taxonomy_item=str(taxonomy_item.id),
                **query_params,
                _external=True,
            ),
            rel=("collection", "page"),
            resource_type="ont-taxonomy-item-relation",
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for(
                "api-v1.ApiSchemaView",
                schema_id="TaxonomyItemRelationPostSchema",
                _external=True,
            ),
        )


class TaxonomyItemRelationsPageCreateLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, page=True, relation="create"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, TaxonomyItem)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(
                OsoResource(
                    "ont-taxonomy-item-relation", parent_resource=resource.resource
                ),
                action="CREATE",
            ):
                print("NOT ALLOWED CREATE_RELATION after checks", resource.resource)
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
        link.rel = ("create", "post")
        return link


class TaxonomyItemRelationsPageUpLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, page=True, relation="up"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, TaxonomyItem)
        return LinkGenerator.get_link_of(resource.resource, extra_relations=("up",))


class TaxonomyItemRelationsPageTaxonomyLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, page=True, relation="ont-taxonomy"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            resource.resource.taxonomy, extra_relations=("nav",)
        )


class TaxonomyItemRelationsPageNamespaceLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, page=True, relation="ont-namespace"
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert isinstance(resource.resource, TaxonomyItem)
        return LinkGenerator.get_link_of(
            resource.resource.taxonomy.namespace, extra_relations=("nav",)
        )


# taxonomy item relations ######################################################
class TaxonomyItemRelationKeyGenerator(KeyGenerator, resource_type=TaxonomyItemRelation):
    def update_key(
        self, key: Dict[str, str], resource: TaxonomyItemRelation
    ) -> Dict[str, str]:
        assert isinstance(resource, TaxonomyItemRelation)
        key.update(KeyGenerator.generate_key(resource.taxonomy_item_source))
        key["relationId"] = str(resource.id)
        return key


class TaxonomyItemRelationSelfLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation
):
    def generate_link(
        self,
        resource: TaxonomyItemRelation,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                "api-v1.TaxonomyItemRelationView",
                namespace=str(resource.taxonomy_item_source.taxonomy.namespace_id),
                taxonomy=str(resource.taxonomy_item_source.taxonomy_id),
                taxonomy_item=str(resource.taxonomy_item_source_id),
                relation=str(resource.id),
                _external=True,
            ),
            rel=tuple(),
            resource_type="ont-taxonomy-item-relation",
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomyRelationSchema", _external=True
            ),
        )


class DeleteTaxonomyItemRelationLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, relation="delete"
):
    def generate_link(
        self,
        resource: TaxonomyItemRelation,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemRelation)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action="DELETE"):
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
        link.rel = ("delete",)
        return link


class TaxonomyItemRelationUpLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, relation="up"
):
    def generate_link(
        self,
        resource: TaxonomyItemRelation,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemRelation)
        return LinkGenerator.get_link_of(
            resource.taxonomy_item_source, extra_relations=("up",)
        )


class TaxonomyItemRelationTaxonomyLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, relation="ont-taxonomy"
):
    def generate_link(
        self,
        resource: TaxonomyItemRelation,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemRelation)
        return LinkGenerator.get_link_of(
            resource.taxonomy_item_source.taxonomy, extra_relations=("nav",)
        )


class TaxonomyItemRelationNamespaceLinkGenerator(
    LinkGenerator, resource_type=TaxonomyItemRelation, relation="ont-namespace"
):
    def generate_link(
        self,
        resource: TaxonomyItemRelation,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, TaxonomyItemRelation)
        return LinkGenerator.get_link_of(
            resource.taxonomy_item_source.taxonomy.namespace, extra_relations=("nav",)
        )


class TaxonomyItemRelationApiObjectGenerator(
    ApiObjectGenerator, resource_type=TaxonomyItemRelation
):
    def generate_api_object(
        self,
        resource: TaxonomyItemRelation,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
    ) -> Optional[TaxonomyItemRelationData]:
        assert isinstance(resource, TaxonomyItemRelation)

        if not FLASK_OSO.is_allowed(resource, action="GET"):
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

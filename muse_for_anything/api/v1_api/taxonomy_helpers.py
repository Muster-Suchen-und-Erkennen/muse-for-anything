from typing import Any, Dict, List, Optional, Union
from flask import url_for

from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.api.v1_api.namespace_helpers import query_params_to_api_key

from muse_for_anything.api.base_models import (
    ApiLink,
    ApiResponse,
)
from muse_for_anything.api.v1_api.models.ontology import (
    TaxonomyData,
    TaxonomyItemData,
    TaxonomyItemRelationData,
    TaxonomyItemRelationSchema,
    TaxonomyItemSchema,
    TaxonomySchema,
)
from muse_for_anything.db.models.taxonomies import (
    Taxonomy,
    TaxonomyItem,
    TaxonomyItemRelation,
    TaxonomyItemVersion,
)


from .request_helpers import KeyGenerator, LinkGenerator, PageResource

from ...oso_helpers import FLASK_OSO, OsoResource


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
        query_params: Optional[Dict[str, Union[str, int, float]]]
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(OsoResource("ont-taxonomy"), action="GET"):
            return
        namespace = resource.resource
        assert namespace is not None
        assert isinstance(namespace, Namespace)
        if query_params is None:
            query_params = {"item-count": 50}
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


def taxonomy_page_params_to_key(
    namespace: str, query_params: Optional[Dict[str, Union[str, int]]] = None
) -> Dict[str, str]:
    if query_params is None:
        query_params = {}
    start_key = query_params_to_api_key(query_params)
    start_key["namespaceId"] = namespace
    return start_key


def nav_links_for_taxonomy_page(namespace: Namespace) -> List[ApiLink]:
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


def create_action_link_for_taxonomy_page(namespace: Namespace) -> ApiLink:
    return ApiLink(
        href=url_for(
            "api-v1.TaxonomiesView",
            namespace=str(namespace.id),
            _external=True,
        ),
        rel=("create", "post"),
        resource_type="ont-taxonomy",
        resource_key={"namespaceId": str(namespace.id)},
        schema=url_for(
            "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
        ),
    )


def action_links_for_taxonomy_page(namespace: Namespace) -> List[ApiLink]:
    actions: List[ApiLink] = []
    if namespace.deleted_on is None:
        # namespace is not deleted
        actions.append(create_action_link_for_taxonomy_page(namespace=namespace))
    return actions


def taxonomy_to_key(taxonomy: Taxonomy) -> Dict[str, str]:
    return {"namespaceId": str(taxonomy.namespace_id), "taxonomyId": str(taxonomy.id)}


def nav_links_for_taxonomy(taxonomy: Taxonomy) -> List[ApiLink]:
    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.TaxonomiesView",
                namespace=str(taxonomy.namespace_id),
                _external=True,
            ),
            rel=("up", "page", "first", "collection"),
            resource_type="ont-taxonomy",
            resource_key={"namespaceId": str(taxonomy.namespace_id)},
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
        ),
        ApiLink(
            href=url_for(
                "api-v1.TaxonomyItemsView",
                namespace=str(taxonomy.namespace_id),
                taxonomy=str(taxonomy.id),
                _external=True,
            ),
            rel=("nav", "page", "first", "collection"),
            resource_type="ont-taxonomy-item",
            resource_key={
                "namespaceId": str(taxonomy.namespace_id),
                "taxonomyId": str(taxonomy.id),
            },
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomyItemSchema", _external=True
            ),
        ),
        ApiLink(
            href=url_for(
                "api-v1.NamespaceView",
                namespace=str(taxonomy.namespace_id),
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-namespace",
            resource_key={"namespaceId": str(taxonomy.namespace_id)},
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
            name=taxonomy.namespace.name,
        ),
    ]
    return nav_links


def taxonomy_item_to_key(item: TaxonomyItem) -> Dict[str, str]:
    return {
        "namespaceId": str(item.taxonomy.namespace_id),
        "taxonomyId": str(item.taxonomy_id),
        "taxonomyItemId": str(item.id),
    }


def taxonomy_item_to_api_link(item: TaxonomyItem) -> ApiLink:
    return ApiLink(
        href=url_for(
            "api-v1.TaxonomyItemView",
            namespace=str(item.taxonomy.namespace_id),
            taxonomy=str(item.taxonomy_id),
            taxonomy_item=str(item.id),
            _external=True,
        ),
        rel=tuple(),
        resource_type="ont-taxonomy-item",
        resource_key=taxonomy_item_to_key(item),
        schema=url_for(
            "api-v1.ApiSchemaView", schema_id="TaxonomyItemSchema", _external=True
        ),
        name=item.name,
    )


def taxonomy_to_items_links(taxonomy: Taxonomy) -> List[ApiLink]:
    return [taxonomy_item_to_api_link(item) for item in taxonomy.current_items]


def taxonomy_to_taxonomy_data(taxonomy: Taxonomy) -> TaxonomyData:
    return TaxonomyData(
        self=ApiLink(
            href=url_for(
                "api-v1.TaxonomyView",
                namespace=str(taxonomy.namespace_id),
                taxonomy=str(taxonomy.id),
                _external=True,
            ),
            rel=tuple(),
            resource_type="ont-taxonomy",
            resource_key=taxonomy_to_key(taxonomy),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
            name=taxonomy.name,
        ),
        name=taxonomy.name,
        description=taxonomy.description,
        created_on=taxonomy.created_on,
        updated_on=taxonomy.updated_on,
        deleted_on=taxonomy.deleted_on,
        items=taxonomy_to_items_links(taxonomy),
    )


def action_links_for_taxonomy(taxonomy: Taxonomy) -> List[ApiLink]:
    actions: List[ApiLink] = []
    if taxonomy.namespace.deleted_on is None:
        # namespace is modifyable
        actions.append(
            ApiLink(
                href=url_for(
                    "api-v1.TaxonomiesView",
                    namespace=str(taxonomy.namespace_id),
                    _external=True,
                ),
                rel=("create", "post"),
                resource_type="ont-taxonomy",
                resource_key={"namespaceId": str(taxonomy.namespace_id)},
                schema=url_for(
                    "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
                ),
            )
        )

        resource_key = taxonomy_to_key(taxonomy)

        if taxonomy.deleted_on is None:
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyView",
                        namespace=str(taxonomy.namespace_id),
                        taxonomy=str(taxonomy.id),
                        _external=True,
                    ),
                    rel=("update", "put"),
                    resource_type="ont-taxonomy",
                    resource_key=resource_key,
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
                    ),
                    name=taxonomy.name,
                )
            )
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyView",
                        namespace=str(taxonomy.namespace_id),
                        taxonomy=str(taxonomy.id),
                        _external=True,
                    ),
                    rel=("delete",),
                    resource_type="ont-taxonomy",
                    resource_key=resource_key,
                    name=taxonomy.name,
                )
            )
            actions.append(create_action_link_for_taxonomy_item_page(taxonomy))
        else:
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyView",
                        namespace=str(taxonomy.namespace_id),
                        taxonomy=str(taxonomy.id),
                        _external=True,
                    ),
                    rel=("restore", "post"),
                    resource_type="ont-taxonomy",
                    resource_key=resource_key,
                    name=taxonomy.name,
                )
            )

    return actions


def taxonomy_to_api_response(taxonomy: Taxonomy) -> ApiResponse:
    taxonomy_data = taxonomy_to_taxonomy_data(taxonomy)
    raw_taxonomy: Dict[str, Any] = TaxonomySchema().dump(taxonomy_data)
    return ApiResponse(
        links=(
            *nav_links_for_taxonomy(taxonomy),
            *action_links_for_taxonomy(taxonomy),
        ),
        data=raw_taxonomy,
    )


def taxonomy_item_page_params_to_key(
    namespace: str,
    taxonomy: str,
    query_params: Optional[Dict[str, Union[str, int]]] = None,
) -> Dict[str, str]:
    if query_params is None:
        query_params = {}
    start_key = query_params_to_api_key(query_params)
    start_key["namespaceId"] = namespace
    start_key["taxonomyId"] = taxonomy
    return start_key


def nav_links_for_taxonomy_item_page(taxonomy: Taxonomy) -> List[ApiLink]:
    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.TaxonomyView",
                namespace=str(taxonomy.namespace_id),
                taxonomy=str(taxonomy.id),
                _external=True,
            ),
            rel=("up",),
            resource_type="ont-taxonomy",
            resource_key=taxonomy_to_key(taxonomy),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
            name=taxonomy.name,
        ),
        ApiLink(
            href=url_for(
                "api-v1.NamespaceView",
                namespace=str(taxonomy.namespace_id),
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-namespace",
            resource_key={"namespaceId": str(taxonomy.namespace_id)},
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
            name=taxonomy.namespace.name,
        ),
    ]
    return nav_links


def create_action_link_for_taxonomy_item_page(taxonomy: Taxonomy) -> ApiLink:
    return ApiLink(
        href=url_for(
            "api-v1.TaxonomyItemsView",
            namespace=str(taxonomy.namespace_id),
            taxonomy=str(taxonomy.id),
            _external=True,
        ),
        rel=("create", "post"),
        resource_type="ont-taxonomy-item",
        resource_key=taxonomy_to_key(taxonomy),
        schema=url_for(
            "api-v1.ApiSchemaView", schema_id="TaxonomyItemSchema", _external=True
        ),
    )


def action_links_for_taxonomy_item_page(taxonomy: Taxonomy) -> List[ApiLink]:
    actions: List[ApiLink] = []
    if taxonomy.deleted_on is None and taxonomy.namespace.deleted_on is None:
        # taxonomy and namespace are not deleted
        actions.append(create_action_link_for_taxonomy_item_page(taxonomy=taxonomy))
    return actions


def taxonomy_item_version_to_key(item: TaxonomyItemVersion) -> Dict[str, str]:
    return {
        "namespaceId": str(item.taxonomy_item.taxonomy.namespace_id),
        "taxonomyId": str(item.taxonomy_item.taxonomy_id),
        "taxonomyItemId": str(item.taxonomy_item.id),
        "version": str(item.version),
    }


def taxonomy_item_version_to_api_link(item: TaxonomyItemVersion) -> ApiLink:
    return ApiLink(
        href=url_for(
            "api-v1.TaxonomyItemVersionView",
            namespace=str(item.taxonomy_item.taxonomy.namespace_id),
            taxonomy=str(item.taxonomy_item.taxonomy_id),
            taxonomy_item=str(item.taxonomy_item_id),
            version=str(item.version),
            _external=True,
        ),
        rel=tuple(),
        resource_type="ont-taxonomy-item-version",
        resource_key=taxonomy_item_version_to_key(item),
        schema=url_for(
            "api-v1.ApiSchemaView", schema_id="TaxonomyItemSchema", _external=True
        ),
        name=item.name,
    )


def taxonomy_item_relation_to_api_link(relation: TaxonomyItemRelation) -> ApiLink:
    resource_key = taxonomy_item_to_key(relation.taxonomy_item_source)
    resource_key["relationId"] = str(relation.id)
    return ApiLink(
        href=url_for(
            "api-v1.TaxonomyItemRelationView",
            namespace=str(relation.taxonomy_item_source.taxonomy.namespace_id),
            taxonomy=str(relation.taxonomy_item_source.taxonomy_id),
            taxonomy_item=str(relation.taxonomy_item_source_id),
            relation=str(relation.id),
            _external=True,
        ),
        rel=tuple(),
        resource_type="ont-taxonomy-item-relation",
        resource_key=resource_key,
    )


def taxonomy_item_to_taxonomy_item_data(
    item: Union[TaxonomyItem, TaxonomyItemVersion]
) -> TaxonomyItemData:

    is_taxonomy_item = isinstance(item, TaxonomyItem)

    self_link: ApiLink
    if is_taxonomy_item:
        self_link = taxonomy_item_to_api_link(item)
    else:
        self_link = taxonomy_item_version_to_api_link(item)

    updated_on = item.updated_on if is_taxonomy_item else item.created_on

    tax_item: TaxonomyItem = item if is_taxonomy_item else item.taxonomy_item
    parents = [
        taxonomy_item_to_api_link(parent.taxonomy_item_source)
        for parent in tax_item.current_ancestors
    ]
    children = [
        taxonomy_item_relation_to_api_link(child) for child in tax_item.current_related
    ]

    return TaxonomyItemData(
        self=self_link,
        name=item.name,
        description=item.description,
        sort_key=item.sort_key,
        version=item.version,
        parents=parents,
        children=children,
        created_on=item.created_on,
        updated_on=updated_on,
        deleted_on=item.deleted_on,
    )


def nav_links_for_taxonomy_item(item: TaxonomyItem) -> List[ApiLink]:
    namespace_id = str(item.taxonomy.namespace_id)

    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.TaxonomyView",
                namespace=namespace_id,
                taxonomy=str(item.taxonomy_id),
                _external=True,
            ),
            rel=("up",),
            resource_type="ont-taxonomy",
            resource_key=taxonomy_to_key(item.taxonomy),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
            name=item.taxonomy.name,
        ),
        ApiLink(
            href=url_for(
                "api-v1.TaxonomiesView",
                namespace=namespace_id,
                _external=True,
            ),
            rel=("nav", "page", "first", "collection"),
            resource_type="ont-taxonomy",
            resource_key={"namespaceId": namespace_id},
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
        ),
        ApiLink(
            href=url_for(
                "api-v1.NamespaceView",
                namespace=namespace_id,
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-namespace",
            resource_key={"namespaceId": namespace_id},
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
            name=item.taxonomy.namespace.name,
        ),
    ]
    return nav_links


def action_links_for_taxonomy_item(item: TaxonomyItem) -> List[ApiLink]:
    actions: List[ApiLink] = []
    if item.taxonomy.namespace.deleted_on is None and item.taxonomy.deleted_on is None:
        # namespace and taxonomy are modifyable

        namespace_id = str(item.taxonomy.namespace_id)

        actions.append(
            ApiLink(
                href=url_for(
                    "api-v1.TaxonomyItemsView",
                    namespace=namespace_id,
                    taxonomy=str(item.taxonomy_id),
                    _external=True,
                ),
                rel=("create", "post"),
                resource_type="ont-taxonomy-item",
                resource_key=taxonomy_to_key(item.taxonomy),
                schema=url_for(
                    "api-v1.ApiSchemaView", schema_id="TaxonomyItemSchema", _external=True
                ),
            )
        )

        resource_key = taxonomy_item_to_key(item)

        if item.deleted_on is None:
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyItemView",
                        namespace=namespace_id,
                        taxonomy=str(item.taxonomy_id),
                        taxonomy_item=str(item.id),
                        _external=True,
                    ),
                    rel=("update", "put"),
                    resource_type="ont-taxonomy-item",
                    resource_key=resource_key,
                    schema=url_for(
                        "api-v1.ApiSchemaView",
                        schema_id="TaxonomyItemSchema",
                        _external=True,
                    ),
                    name=item.name,
                )
            )
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyItemView",
                        namespace=namespace_id,
                        taxonomy=str(item.taxonomy_id),
                        taxonomy_item=str(item.id),
                        _external=True,
                    ),
                    rel=("delete",),
                    resource_type="ont-taxonomy-item",
                    resource_key=resource_key,
                    name=item.name,
                )
            )
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyItemRelationsView",
                        namespace=namespace_id,
                        taxonomy=str(item.taxonomy_id),
                        taxonomy_item=str(item.id),
                        _external=True,
                    ),
                    rel=("create", "post"),
                    resource_type="ont-taxonomy-item-relation",
                    resource_key=taxonomy_item_to_key(item),
                    schema=url_for(
                        "api-v1.ApiSchemaView",
                        schema_id="TaxonomyItemRelationPostSchema",
                        _external=True,
                    ),
                )
            )
        else:
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyItemView",
                        namespace=namespace_id,
                        taxonomy=str(item.taxonomy_id),
                        taxonomy_item=str(item.id),
                        _external=True,
                    ),
                    rel=("restore", "post"),
                    resource_type="ont-taxonomy-item",
                    resource_key=resource_key,
                    name=item.name,
                )
            )

    return actions


def nav_links_for_taxonomy_item_version(
    item_version: TaxonomyItemVersion,
) -> List[ApiLink]:
    item = item_version.taxonomy_item
    namespace_id = str(item.taxonomy.namespace_id)

    nav_links: List[ApiLink] = [
        # TODO up navigation link to versions page
        ApiLink(
            href=url_for(
                "api-v1.TaxonomyItemView",
                namespace=namespace_id,
                taxonomy=str(item.taxonomy_id),
                taxonomy_item=str(item.id),
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-taxonomy-item",
            resource_key=taxonomy_to_key(item.taxonomy),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomyItemSchema", _external=True
            ),
            name=item.name,
        ),
        ApiLink(
            href=url_for(
                "api-v1.TaxonomyView",
                namespace=namespace_id,
                taxonomy=str(item.taxonomy_id),
                _external=True,
            ),
            rel=("up",),
            resource_type="ont-taxonomy",
            resource_key=taxonomy_to_key(item.taxonomy),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
            name=item.taxonomy.name,
        ),
        ApiLink(
            href=url_for(
                "api-v1.TaxonomiesView",
                namespace=namespace_id,
                _external=True,
            ),
            rel=("nav", "page", "first", "collection"),
            resource_type="ont-taxonomy",
            resource_key={"namespaceId": namespace_id},
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
        ),
        ApiLink(
            href=url_for(
                "api-v1.NamespaceView",
                namespace=namespace_id,
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-namespace",
            resource_key={"namespaceId": namespace_id},
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
            name=item.taxonomy.namespace.name,
        ),
    ]
    return nav_links


def action_links_for_taxonomy_item_version(
    item_version: TaxonomyItemVersion,
) -> List[ApiLink]:
    actions: List[ApiLink] = []
    # TODO
    return actions


def taxonomy_item_to_api_response(item: TaxonomyItem) -> ApiResponse:
    taxonomy_item_data = taxonomy_item_to_taxonomy_item_data(item)
    raw_taxonomy_item: Dict[str, Any] = TaxonomyItemSchema().dump(taxonomy_item_data)
    return ApiResponse(
        links=(
            *nav_links_for_taxonomy_item(item),
            *action_links_for_taxonomy_item(item),
        ),
        data=raw_taxonomy_item,
    )


def create_action_link_for_taxonomy_item_relation_page(
    namespace: str, taxonomy: str, taxonomy_item: str
) -> ApiLink:
    return ApiLink(
        href=url_for(
            "api-v1.TaxonomyItemRelationsView",
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            _external=True,
        ),
        rel=("create", "post"),
        resource_type="ont-taxonomy-item-relation",
        resource_key={
            "namespaceId": namespace,
            "taxonomyId": taxonomy,
            "taxonomyItemId": taxonomy_item,
        },
        schema=url_for(
            "api-v1.ApiSchemaView",
            schema_id="TaxonomyItemRelationPostSchema",
            _external=True,
        ),
    )


def nav_links_for_taxonomy_item_relation(
    relation: TaxonomyItemRelation,
) -> List[ApiLink]:
    taxonomy = relation.taxonomy_item_source.taxonomy
    namespace_id = str(taxonomy.namespace_id)

    nav_links: List[ApiLink] = [
        ApiLink(
            href=url_for(
                "api-v1.TaxonomyView",
                namespace=namespace_id,
                taxonomy=str(taxonomy.id),
                _external=True,
            ),
            rel=("up",),
            resource_type="ont-taxonomy",
            resource_key=taxonomy_to_key(taxonomy),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
            name=taxonomy.name,
        ),
        ApiLink(
            href=url_for(
                "api-v1.TaxonomiesView",
                namespace=namespace_id,
                _external=True,
            ),
            rel=("nav", "page", "first", "collection"),
            resource_type="ont-taxonomy",
            resource_key={"namespaceId": namespace_id},
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
        ),
        ApiLink(
            href=url_for(
                "api-v1.NamespaceView",
                namespace=namespace_id,
                _external=True,
            ),
            rel=("nav",),
            resource_type="ont-namespace",
            resource_key={"namespaceId": namespace_id},
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
            name=taxonomy.namespace.name,
        ),
    ]
    return nav_links


def action_links_for_taxonomy_item_relation(
    relation: TaxonomyItemRelation,
) -> List[ApiLink]:
    actions: List[ApiLink] = []
    item: TaxonomyItem = relation.taxonomy_item_source
    if (
        item.taxonomy.namespace.deleted_on is None
        and item.taxonomy.deleted_on is None
        and item.deleted_on is None
    ):
        # namespace and taxonomy and item are modifyable

        namespace_id = str(item.taxonomy.namespace_id)

        resource_key = taxonomy_item_to_key(item)
        resource_key["relationId"] = str(relation.id)

        if item.deleted_on is None:
            actions.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyItemRelationView",
                        namespace=namespace_id,
                        taxonomy=str(item.taxonomy_id),
                        taxonomy_item=str(item.id),
                        relation=str(relation.id),
                        _external=True,
                    ),
                    rel=("delete",),
                    resource_type="ont-taxonomy-item-relation",
                    resource_key=resource_key,
                )
            )

    return actions


def taxonomy_item_relation_to_taxonomy_item_relation_data(
    relation: TaxonomyItemRelation,
) -> TaxonomyItemRelationData:
    return TaxonomyItemRelationData(
        self=taxonomy_item_relation_to_api_link(relation),
        source_item=taxonomy_item_to_api_link(relation.taxonomy_item_source),
        target_item=taxonomy_item_to_api_link(relation.taxonomy_item_target),
        created_on=relation.created_on,
        deleted_on=relation.deleted_on,
    )


def taxonomy_item_relation_to_api_response(relation: TaxonomyItemRelation) -> ApiResponse:
    relation_data = taxonomy_item_relation_to_taxonomy_item_relation_data(relation)
    raw_relation: Dict[str, Any] = TaxonomyItemRelationSchema().dump(relation_data)
    return ApiResponse(
        links=(
            *nav_links_for_taxonomy_item_relation(relation),
            *action_links_for_taxonomy_item_relation(relation),
        ),
        data=raw_relation,
    )

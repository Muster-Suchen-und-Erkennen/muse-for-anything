"""Module containing the taxonomy items API endpoints of the v1 API."""

from datetime import datetime
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Sequence, Tuple, cast

from flask.views import MethodView
from flask_babel import gettext
from flask_smorest import abort
from marshmallow.utils import INCLUDE
from sqlalchemy.orm import selectinload

from muse_for_anything.api.pagination_util import (
    PaginationOptions,
    default_get_page_info,
    dump_embedded_page_items,
    generate_page_links,
    prepare_pagination_query_args,
)
from muse_for_anything.api.v1_api.request_helpers import (
    ApiResponseGenerator,
    LinkGenerator,
    PageResource,
    skip_slow_policy_checks_for_links_in_embedded_responses,
)
from muse_for_anything.db.models.taxonomies import (
    Taxonomy,
    TaxonomyItem,
    TaxonomyItemRelation,
    TaxonomyItemVersion,
)
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource

from .models.ontology import (
    TaxonomyItemRelationPostSchema,
    TaxonomyItemRelationSchema,
    TaxonomyItemSchema,
    TaxonomySchema,
)
from .root import API_V1
from .taxonomy_helpers import (
    TAXONOMY_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_RELATION_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_RELATION_PAGE_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_VERSION_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_VERSION_PAGE_EXTRA_LINK_RELATIONS,
)
from ..base_models import (
    ApiLink,
    ApiResponse,
    ChangedApiObject,
    ChangedApiObjectSchema,
    CursorPageArgumentsSchema,
    CursorPageSchema,
    DynamicApiResponseSchema,
    NewApiObject,
    NewApiObjectSchema,
)
from ...db.db import DB


@API_V1.route(
    "/namespaces/<string:namespace>/taxonomies/<string:taxonomy>/items/<string:taxonomy_item>/"
)
class TaxonomyItemView(MethodView):
    """Endpoint for a single taxonomy item."""

    def _check_path_params(self, namespace: str, taxonomy: str, taxonomy_item: str):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not taxonomy or not taxonomy.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy id has the wrong format!"),
            )
        if not taxonomy_item or not taxonomy_item.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy item id has the wrong format!"),
            )

    def _get_taxonomy_item(
        self, namespace: str, taxonomy: str, taxonomy_item: str
    ) -> TaxonomyItem:
        namespace_id = int(namespace)
        taxonomy_id = int(taxonomy)
        taxonomy_item_id = int(taxonomy_item)
        found_taxonomy_item: Optional[TaxonomyItem] = (
            TaxonomyItem.query.options(selectinload(TaxonomyItem.current_ancestors))
            .filter(
                TaxonomyItem.id == taxonomy_item_id,
                TaxonomyItem.taxonomy_id == taxonomy_id,
            )
            .first()
        )

        if (
            found_taxonomy_item is None
            or found_taxonomy_item.taxonomy.namespace_id != namespace_id
        ):
            abort(HTTPStatus.NOT_FOUND, message=gettext("Taxonomy item not found."))
        return found_taxonomy_item  # is not None because abort raises exception

    def _check_if_taxonomy_modifiable(self, taxonomy: Taxonomy):
        if taxonomy.namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )
        if taxonomy.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy is marked as deleted and cannot be modified further."
                ),
            )

    def _check_if_modifiable(self, taxonomy_item: TaxonomyItem):
        self._check_if_taxonomy_modifiable(taxonomy=taxonomy_item.taxonomy)
        if taxonomy_item.deleted_on is not None:
            # cannot modify deleted taxonomy!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy item is marked as deleted and cannot be modified further."
                ),
            )

    @API_V1.response(DynamicApiResponseSchema(TaxonomyItemSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, taxonomy: str, taxonomy_item: str, **kwargs: Any):
        """Get a single taxonomy item."""
        self._check_path_params(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        found_taxonomy_item: TaxonomyItem = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )

        FLASK_OSO.authorize_and_set_resource(found_taxonomy_item)

        embedded: List[ApiResponse] = []
        extra_links: List[ApiLink] = []

        with skip_slow_policy_checks_for_links_in_embedded_responses():
            item_dump = TaxonomyItemSchema().dump
            relation_dump = TaxonomyItemRelationSchema().dump
            for relation in found_taxonomy_item.current_ancestors:
                parent_response = ApiResponseGenerator.get_api_response(
                    relation.taxonomy_item_source
                )
                if parent_response:
                    link: ApiLink = parent_response.data.self
                    extra_links.append(link.copy_with(rel=("parent", *link.rel)))
                    parent_response.data = item_dump(parent_response.data)
                    embedded.append(parent_response)
            for relation in found_taxonomy_item.current_related:
                child_relation_response = ApiResponseGenerator.get_api_response(relation)
                if child_relation_response:
                    extra_links.append(child_relation_response.data.self)
                    child_relation_response.data = relation_dump(
                        child_relation_response.data
                    )
                    embedded.append(child_relation_response)
                child_response = ApiResponseGenerator.get_api_response(
                    relation.taxonomy_item_target
                )
                if child_response:
                    link: ApiLink = child_response.data.self
                    extra_links.append(link.copy_with(rel=("child", *link.rel)))
                    child_response.data = item_dump(child_response.data)
                    embedded.append(child_response)

        return ApiResponseGenerator.get_api_response(
            found_taxonomy_item,
            link_to_relations=TAXONOMY_ITEM_EXTRA_LINK_RELATIONS,
            extra_links=extra_links,
            extra_embedded=embedded,
        )

    @API_V1.arguments(TaxonomyItemSchema())
    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def put(self, data, namespace: str, taxonomy: str, taxonomy_item: str):
        """Update a taxonomy item."""
        self._check_path_params(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        found_taxonomy_item: TaxonomyItem = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        self._check_if_modifiable(found_taxonomy_item)

        FLASK_OSO.authorize_and_set_resource(found_taxonomy_item, action="EDIT")

        taxonomy_item_version = TaxonomyItemVersion(
            taxonomy_item=found_taxonomy_item,
            version=found_taxonomy_item.current_version.version + 1,
            name=data["name"],
            description=data.get("description", ""),
            sort_key=data.get("sort_key", 10),
        )
        found_taxonomy_item.current_version = taxonomy_item_version
        DB.session.add(found_taxonomy_item)
        DB.session.add(taxonomy_item_version)
        DB.session.commit()

        taxonomy_item_response = ApiResponseGenerator.get_api_response(
            found_taxonomy_item, link_to_relations=TAXONOMY_ITEM_EXTRA_LINK_RELATIONS
        )
        taxonomy_item_link = taxonomy_item_response.data.self
        taxonomy_item_response.data = TaxonomyItemSchema().dump(
            taxonomy_item_response.data
        )

        self_link = LinkGenerator.get_link_of(
            found_taxonomy_item,
            for_relation="update",
            extra_relations=("ont-taxonomy-item",),
            ignore_deleted=True,
        )
        self_link.resource_type = "changed"

        return ApiResponse(
            links=[taxonomy_item_link],
            embedded=[taxonomy_item_response],
            data=ChangedApiObject(
                self=self_link,
                changed=taxonomy_item_link,
            ),
        )

    def _get_embedded_changed_related_resources(
        self,
        ancestors: Sequence[TaxonomyItemRelation],
        related: Sequence[TaxonomyItemRelation],
    ) -> Tuple[List[ApiResponse], List[ApiLink]]:
        embedded = []
        links = []
        with skip_slow_policy_checks_for_links_in_embedded_responses():
            item_dump = TaxonomyItemSchema().dump
            relation_dump = TaxonomyItemRelationSchema().dump
            for relation in ancestors:
                parent_relation_response = ApiResponseGenerator.get_api_response(relation)
                if parent_relation_response:
                    links.append(parent_relation_response.data.self)
                    parent_relation_response.data = relation_dump(
                        parent_relation_response.data
                    )
                    embedded.append(parent_relation_response)
                parent_response = ApiResponseGenerator.get_api_response(
                    relation.taxonomy_item_target
                )
                if parent_response:
                    link: ApiLink = parent_response.data.self
                    links.append(link.copy_with(rel=("child", *link.rel)))
                    parent_response.data = item_dump(parent_response.data)
                    embedded.append(parent_response)
            for relation in related:
                child_relation_response = ApiResponseGenerator.get_api_response(relation)
                if child_relation_response:
                    links.append(child_relation_response.data.self)
                    child_relation_response.data = relation_dump(
                        child_relation_response.data
                    )
                    embedded.append(child_relation_response)
                child_response = ApiResponseGenerator.get_api_response(
                    relation.taxonomy_item_target
                )
                if child_response:
                    link: ApiLink = child_response.data.self
                    links.append(link.copy_with(rel=("child", *link.rel)))
                    child_response.data = item_dump(child_response.data)
                    embedded.append(child_response)
        return embedded, links

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def post(self, namespace: str, taxonomy: str, taxonomy_item: str):  # restore action
        """Restore a deleted taxonomy item."""
        self._check_path_params(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        found_taxonomy_item: TaxonomyItem = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        self._check_if_taxonomy_modifiable(found_taxonomy_item.taxonomy)

        FLASK_OSO.authorize_and_set_resource(found_taxonomy_item, action="RESTORE")

        changed_links: List[ApiLink] = []
        embedded: List[ApiResponse] = []

        # only actually restore when not already restored
        if found_taxonomy_item.deleted_on is not None:
            # restore taxonomy item
            deleted_timestamp = found_taxonomy_item.deleted_on
            found_taxonomy_item.deleted_on = None
            # also restore relations
            ancestors: Sequence[TaxonomyItemRelation] = TaxonomyItemRelation.query.filter(
                TaxonomyItemRelation.taxonomy_item_target_id == found_taxonomy_item.id,
                TaxonomyItemRelation.deleted_on == deleted_timestamp,
            ).all()
            ancestor_ids = set()
            relation: TaxonomyItemRelation
            for relation in ancestors:
                if relation.taxonomy_item_source.deleted_on is not None:
                    continue  # do not restore relations to deleted items
                ancestor_ids.add(relation.taxonomy_item_source_id)
                relation.deleted_on = None
                DB.session.add(relation)

            def produces_circle(relation: TaxonomyItemRelation) -> bool:
                if relation.taxonomy_item_target_id in ancestor_ids:
                    return True
                for rel in relation.taxonomy_item_target.current_related:
                    if produces_circle(rel):
                        return True
                return False

            children: Sequence[TaxonomyItemRelation] = TaxonomyItemRelation.query.filter(
                TaxonomyItemRelation.taxonomy_item_source_id == found_taxonomy_item.id,
                TaxonomyItemRelation.deleted_on == deleted_timestamp,
            ).all()
            for relation in children:
                if relation.taxonomy_item_target.deleted_on is not None:
                    continue  # do not restore relations to deleted items
                if produces_circle(relation):
                    continue
                relation.deleted_on = None
                DB.session.add(relation)
            DB.session.add(found_taxonomy_item)
            DB.session.commit()

            # add changed items to be embedded into the response
            embedded, changed_links = self._get_embedded_changed_related_resources(
                ancestors=found_taxonomy_item.current_ancestors,
                related=found_taxonomy_item.current_related,
            )

        taxonomy_item_response = ApiResponseGenerator.get_api_response(
            found_taxonomy_item, link_to_relations=TAXONOMY_ITEM_EXTRA_LINK_RELATIONS
        )
        taxonomy_item_link = taxonomy_item_response.data.self
        taxonomy_item_response.data = TaxonomyItemSchema().dump(
            taxonomy_item_response.data
        )

        taxonomy_response = ApiResponseGenerator.get_api_response(
            found_taxonomy_item.taxonomy, link_to_relations=TAXONOMY_EXTRA_LINK_RELATIONS
        )
        taxonomy_link = taxonomy_response.data.self
        taxonomy_response.data = TaxonomySchema().dump(taxonomy_response.data)

        self_link = LinkGenerator.get_link_of(
            found_taxonomy_item,
            for_relation="restore",
            extra_relations=("ont-taxonomy-item",),
            ignore_deleted=True,
        )
        self_link.resource_type = "changed"

        return ApiResponse(
            links=[taxonomy_item_link, taxonomy_link, *changed_links],
            embedded=[taxonomy_item_response, taxonomy_response, *embedded],
            data=ChangedApiObject(
                self=self_link,
                changed=taxonomy_item_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def delete(self, namespace: str, taxonomy: str, taxonomy_item: str):  # restore action
        """Delete a taxonomy item."""
        self._check_path_params(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        found_taxonomy_item: TaxonomyItem = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        self._check_if_taxonomy_modifiable(found_taxonomy_item.taxonomy)

        FLASK_OSO.authorize_and_set_resource(found_taxonomy_item)

        changed_links: List[ApiLink] = []
        embedded: List[ApiResponse] = []

        # only actually delete when not already deleted
        if found_taxonomy_item.deleted_on is None:
            # delete taxonomy item
            deleted_timestamp = datetime.utcnow()
            found_taxonomy_item.deleted_on = deleted_timestamp
            # also delete incoming and outgoing relations to remove them
            # from relations of existing items
            ancestors = found_taxonomy_item.current_ancestors
            for relation in found_taxonomy_item.current_ancestors:
                relation.deleted_on = deleted_timestamp
                DB.session.add(relation)
            related = found_taxonomy_item.current_related
            for relation in found_taxonomy_item.current_related:
                relation.deleted_on = deleted_timestamp
                DB.session.add(relation)
            DB.session.add(found_taxonomy_item)
            DB.session.commit()

            # add changed items to be embedded into the response
            embedded, changed_links = self._get_embedded_changed_related_resources(
                ancestors=ancestors, related=related
            )

        taxonomy_item_response = ApiResponseGenerator.get_api_response(
            found_taxonomy_item, link_to_relations=TAXONOMY_ITEM_EXTRA_LINK_RELATIONS
        )
        taxonomy_item_link = taxonomy_item_response.data.self
        taxonomy_item_response.data = TaxonomyItemSchema().dump(
            taxonomy_item_response.data
        )

        taxonomy_response = ApiResponseGenerator.get_api_response(
            found_taxonomy_item.taxonomy, link_to_relations=TAXONOMY_EXTRA_LINK_RELATIONS
        )
        taxonomy_link = taxonomy_response.data.self
        taxonomy_response.data = TaxonomySchema().dump(taxonomy_response.data)

        self_link = LinkGenerator.get_link_of(
            found_taxonomy_item,
            for_relation="restore",
            extra_relations=("ont-taxonomy-item",),
            ignore_deleted=True,
        )
        self_link.resource_type = "changed"

        return ApiResponse(
            links=[taxonomy_item_link, taxonomy_link, *changed_links],
            embedded=[taxonomy_item_response, taxonomy_response, *embedded],
            data=ChangedApiObject(
                self=self_link,
                changed=taxonomy_item_link,
            ),
        )


@API_V1.route(
    "/namespaces/<string:namespace>/taxonomies/<string:taxonomy>/items/<string:taxonomy_item>/relations/"
)
class TaxonomyItemRelationsView(MethodView):
    """Endpoint for manipulating taxonomy item relations."""

    def _check_path_params(self, namespace: str, taxonomy: str, taxonomy_item: str):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not taxonomy or not taxonomy.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy id has the wrong format!"),
            )
        if not taxonomy_item or not taxonomy_item.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy item id has the wrong format!"),
            )

    def _get_taxonomy_item(
        self, namespace: str, taxonomy: str, taxonomy_item: str
    ) -> TaxonomyItem:
        namespace_id = int(namespace)
        taxonomy_id = int(taxonomy)
        taxonomy_item_id = int(taxonomy_item)
        found_taxonomy_item: Optional[TaxonomyItem] = TaxonomyItem.query.filter(
            TaxonomyItem.id == taxonomy_item_id,
            TaxonomyItem.taxonomy_id == taxonomy_id,
        ).first()

        if (
            found_taxonomy_item is None
            or found_taxonomy_item.taxonomy.namespace_id != namespace_id
        ):
            abort(HTTPStatus.NOT_FOUND, message=gettext("Taxonomy item not found."))
        return found_taxonomy_item  # is not None because abort raises exception

    def _check_if_modifiable(self, taxonomy_item: TaxonomyItem):
        taxonomy = taxonomy_item.taxonomy
        if taxonomy.namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )
        if taxonomy.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy is marked as deleted and cannot be modified further."
                ),
            )
        if taxonomy_item.deleted_on is not None:
            # cannot modify deleted taxonomy!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy item is marked as deleted and cannot be modified further."
                ),
            )

    def _check_item_circle(
        self,
        item_target: TaxonomyItem,
        item_source: TaxonomyItem,
        original_target: Optional[TaxonomyItem] = None,
    ):
        """Check for a path from target to source which would form a circular dependency. Abort if such a path is found!"""
        if original_target is None:
            original_target = item_target
        relation: TaxonomyItemRelation
        for relation in item_target.current_related:
            if relation.taxonomy_item_target.deleted_on is not None:
                continue  # exclude deleted items as targets
            if relation.taxonomy_item_target_id == item_source.id:
                abort(
                    HTTPStatus.CONFLICT,
                    message=gettext(
                        "Cannot add a relation from %(target)s to %(source)s as it would create a circle!",
                        target=original_target.name,
                        source=item_source.name,
                    ),
                )
            else:
                self._check_item_circle(
                    item_target=relation.taxonomy_item_target,
                    item_source=item_source,
                    original_target=original_target,
                )

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt")
    def get(
        self,
        namespace: str,
        taxonomy: str,
        taxonomy_item: str,
        **kwargs,
    ):
        """Get all relations of a taxonomy item."""
        self._check_path_params(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        found_taxonomy_item = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                "ont-taxonomy-item-relation",
                is_collection=True,
                parent_resource=found_taxonomy_item,
            )
        )

        pagination_options: PaginationOptions = prepare_pagination_query_args(
            **kwargs, _sort_default="-created_on"
        )

        taxonomy_item_relation_filter = (
            TaxonomyItemRelation.deleted_on == None,
            TaxonomyItemRelation.taxonomy_item_source_id == int(taxonomy_item),
        )

        pagination_info = default_get_page_info(
            TaxonomyItemRelation,
            taxonomy_item_relation_filter,
            pagination_options,
            [TaxonomyItemRelation.created_on],
        )

        taxonomy_item_relations: List[
            TaxonomyItemRelation
        ] = pagination_info.page_items_query.all()

        embedded_items, items = dump_embedded_page_items(
            taxonomy_item_relations,
            TaxonomyItemRelationSchema(),
            TAXONOMY_ITEM_RELATION_EXTRA_LINK_RELATIONS,
        )

        page_resource = PageResource(
            TaxonomyItemRelation,
            resource=found_taxonomy_item,
            page_number=pagination_info.cursor_page,
            active_page=pagination_info.cursor_page,
            last_page=pagination_info.last_page.page,
            collection_size=pagination_info.collection_size,
            item_links=items,
        )
        self_link = LinkGenerator.get_link_of(
            page_resource, query_params=pagination_options.to_query_params()
        )

        extra_links = generate_page_links(
            page_resource, pagination_info, pagination_options
        )

        return ApiResponseGenerator.get_api_response(
            page_resource,
            query_params=pagination_options.to_query_params(),
            extra_links=[
                LinkGenerator.get_link_of(
                    page_resource.get_page(1),
                    query_params=pagination_options.to_query_params(cursor=None),
                ),
                self_link,
                *extra_links,
            ],
            extra_embedded=embedded_items,
            link_to_relations=TAXONOMY_ITEM_RELATION_PAGE_EXTRA_LINK_RELATIONS,
        )

    @API_V1.arguments(TaxonomyItemRelationPostSchema())
    @API_V1.response(DynamicApiResponseSchema(NewApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def post(
        self,
        data: Dict[str, str],
        namespace: str,
        taxonomy: str,
        taxonomy_item: str,
    ):
        """Create a new relation to a taxonomy item."""
        self._check_path_params(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        if namespace != data["namespace_id"] or taxonomy != data["taxonomy_id"]:
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext(
                    "Cannot create a relation to a taxonomy item of a different taxonomy!"
                ),
            )

        found_taxonomy_item = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        self._check_if_modifiable(found_taxonomy_item)

        found_taxonomy_item_target = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=data["taxonomy_item_id"]
        )
        self._check_if_modifiable(found_taxonomy_item_target)

        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                "ont-taxonomy-item-relation", parent_resource=found_taxonomy_item
            ),
            action="CREATE",
        )

        self._check_item_circle(found_taxonomy_item_target, found_taxonomy_item)

        relation = TaxonomyItemRelation(
            taxonomy_item_source=found_taxonomy_item,
            taxonomy_item_target=found_taxonomy_item_target,
        )
        DB.session.add(relation)
        DB.session.commit()

        embedded: List[ApiResponse] = []
        extra_links: List[ApiLink] = []

        with skip_slow_policy_checks_for_links_in_embedded_responses():
            dump = TaxonomyItemSchema().dump
            for extra_rel, resource in (
                ("source", found_taxonomy_item),
                ("target", found_taxonomy_item_target),
            ):
                response = ApiResponseGenerator.get_api_response(resource=resource)
                if response:
                    link: ApiLink = response.data.self
                    extra_links.append(link.copy_with(rel=(extra_rel, *link.rel)))
                    response.data = dump(response.data)
                    embedded.append(response)

        relation_response = ApiResponseGenerator.get_api_response(resource=relation)
        if relation_response is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Could not create a response.")
        taxonomy_item_relation_link: ApiLink = relation_response.data.self
        relation_response.data = TaxonomyItemRelationSchema().dump(relation_response.data)
        embedded.append(relation_response)

        self_link = LinkGenerator.get_link_of(
            PageResource(TaxonomyItemRelation, resource=found_taxonomy_item),
            for_relation="create",
            extra_relations=("ont-taxonomy-item-relation",),
            ignore_deleted=True,
        )
        self_link.resource_type = "new"

        return ApiResponse(
            links=extra_links,
            embedded=embedded,
            data=NewApiObject(
                self=self_link,
                new=taxonomy_item_relation_link,
            ),
        )


@API_V1.route(
    "/namespaces/<string:namespace>/taxonomies/<string:taxonomy>/items/<string:taxonomy_item>/relations/<string:relation>/"
)
class TaxonomyItemRelationView(MethodView):
    """Endpoint for removing taxonomy item relations."""

    def _check_path_params(
        self, namespace: str, taxonomy: str, taxonomy_item: str, relation: str
    ):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not taxonomy or not taxonomy.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy id has the wrong format!"),
            )
        if not taxonomy_item or not taxonomy_item.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy item id has the wrong format!"),
            )
        if not relation or not relation.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext(
                    "The requested taxonomy item relation id has the wrong format!"
                ),
            )

    def _get_taxonomy_item_relation(
        self, namespace: str, taxonomy: str, taxonomy_item: str, relation: str
    ) -> TaxonomyItemRelation:
        namespace_id = int(namespace)
        taxonomy_id = int(taxonomy)
        taxonomy_item_id = int(taxonomy_item)
        relation_id = int(relation)
        found_taxonomy_item_relation: Optional[
            TaxonomyItemRelation
        ] = TaxonomyItemRelation.query.filter(
            TaxonomyItemRelation.id == relation_id,
            TaxonomyItemRelation.taxonomy_item_source_id == taxonomy_item_id,
        ).first()

        if (
            found_taxonomy_item_relation is None
            or found_taxonomy_item_relation.taxonomy_item_source.taxonomy_id
            != taxonomy_id
            or found_taxonomy_item_relation.taxonomy_item_source.taxonomy.namespace_id
            != namespace_id
        ):
            abort(
                HTTPStatus.NOT_FOUND, message=gettext("Taxonomy item relation not found.")
            )
        return found_taxonomy_item_relation  # is not None because abort raises exception

    def _check_if_modifiable(self, relation: TaxonomyItemRelation):
        taxonomy_item = relation.taxonomy_item_source
        taxonomy = taxonomy_item.taxonomy
        if taxonomy.namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )
        if taxonomy.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy is marked as deleted and cannot be modified further."
                ),
            )
        if taxonomy_item.deleted_on is not None:
            # cannot modify deleted taxonomy item!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy item is marked as deleted and cannot be modified further."
                ),
            )

    def _get_embedded_resources_for_relation(
        self, relation: TaxonomyItemRelation
    ) -> Tuple[List[ApiResponse], List[ApiLink]]:
        embedded: List[ApiResponse] = []
        extra_links: List[ApiLink] = []

        with skip_slow_policy_checks_for_links_in_embedded_responses():
            dump = TaxonomyItemSchema().dump
            for extra_rel, resource in (
                ("source", relation.taxonomy_item_source),
                ("target", relation.taxonomy_item_target),
            ):
                response = ApiResponseGenerator.get_api_response(resource=resource)
                if response:
                    link: ApiLink = response.data.self
                    extra_links.append(link.copy_with(rel=(extra_rel, *link.rel)))
                    response.data = dump(response.data)
                    embedded.append(response)

        return embedded, extra_links

    @API_V1.response(DynamicApiResponseSchema(TaxonomyItemRelationSchema()))
    @API_V1.require_jwt("jwt")
    def get(
        self,
        namespace: str,
        taxonomy: str,
        taxonomy_item: str,
        relation: str,
        **kwargs: Any,
    ):
        """Get a single relation."""
        self._check_path_params(
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            relation=relation,
        )
        found_relation = self._get_taxonomy_item_relation(
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            relation=relation,
        )
        FLASK_OSO.authorize_and_set_resource(found_relation)
        embedded, extra_links = self._get_embedded_resources_for_relation(found_relation)
        return ApiResponseGenerator.get_api_response(
            found_relation,
            link_to_relations=TAXONOMY_ITEM_RELATION_EXTRA_LINK_RELATIONS,
            extra_links=extra_links,
            extra_embedded=embedded,
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def delete(
        self,
        namespace: str,
        taxonomy: str,
        taxonomy_item: str,
        relation: str,
        **kwargs: Any,
    ):
        """Delete an existing relation."""
        self._check_path_params(
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            relation=relation,
        )
        found_relation = self._get_taxonomy_item_relation(
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            relation=relation,
        )
        self._check_if_modifiable(found_relation)

        FLASK_OSO.authorize_and_set_resource(found_relation)

        # only actually delete when not already deleted
        if found_relation.deleted_on is None:
            # delete taxonomy item relation
            found_relation.deleted_on = datetime.utcnow()
            DB.session.add(found_relation)
            DB.session.commit()

        embedded, extra_links = self._get_embedded_resources_for_relation(found_relation)

        relation_response = ApiResponseGenerator.get_api_response(resource=found_relation)
        if relation_response is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR, "Could not create a response.")
        taxonomy_item_relation_link: ApiLink = relation_response.data.self
        relation_response.data = TaxonomyItemRelationSchema().dump(relation_response.data)
        embedded.append(relation_response)

        self_link = LinkGenerator.get_link_of(
            found_relation,
            for_relation="delete",
            extra_relations=("ont-taxonomy-item-relation",),
            ignore_deleted=True,
        )
        self_link.resource_type = "changed"

        return ApiResponse(
            links=extra_links,
            embedded=embedded,
            data=ChangedApiObject(
                self=self_link,
                changed=taxonomy_item_relation_link,
            ),
        )


@API_V1.route(
    "/namespaces/<string:namespace>/taxonomies/<string:taxonomy>/items/<string:taxonomy_item>/versions/"
)
class TaxonomyItemVersionsView(MethodView):
    """Endpoint for all versions of a taxonomy item."""

    def _check_path_params(self, namespace: str, taxonomy: str, taxonomy_item: str):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not taxonomy or not taxonomy.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy id has the wrong format!"),
            )
        if not taxonomy_item or not taxonomy_item.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy item id has the wrong format!"),
            )

    def _get_taxonomy_item(
        self, namespace: str, taxonomy: str, taxonomy_item: str
    ) -> TaxonomyItem:
        namespace_id = int(namespace)
        taxonomy_id = int(taxonomy)
        taxonomy_item_id = int(taxonomy_item)
        found_taxonomy_item: Optional[TaxonomyItem] = TaxonomyItem.query.filter(
            TaxonomyItem.id == taxonomy_item_id,
            TaxonomyItem.taxonomy_id == taxonomy_id,
        ).first()

        if (
            found_taxonomy_item is None
            or found_taxonomy_item.taxonomy.namespace_id != namespace_id
        ):
            abort(HTTPStatus.NOT_FOUND, message=gettext("Taxonomy item not found."))
        return found_taxonomy_item  # is not None because abort raises exception

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, taxonomy: str, taxonomy_item: str, **kwargs: Any):
        """Get all versions of a taxonomy item."""
        self._check_path_params(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        found_taxonomy_item: TaxonomyItem = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                "ont-taxonomy-item-version",
                is_collection=True,
                parent_resource=found_taxonomy_item,
            )
        )

        pagination_options: PaginationOptions = prepare_pagination_query_args(
            **kwargs, _sort_default="-created_on"
        )

        taxonomy_item_version_filter = (
            TaxonomyItemVersion.deleted_on == None,
            TaxonomyItemVersion.taxonomy_item == found_taxonomy_item,
        )

        pagination_info = default_get_page_info(
            TaxonomyItemVersion,
            taxonomy_item_version_filter,
            pagination_options,
            [TaxonomyItemVersion.created_on],
        )

        taxonomy_item_versions: List[
            TaxonomyItemVersion
        ] = pagination_info.page_items_query.all()

        embedded_items, items = dump_embedded_page_items(
            taxonomy_item_versions,
            TaxonomyItemSchema(),
            TAXONOMY_ITEM_VERSION_EXTRA_LINK_RELATIONS,
        )

        page_resource = PageResource(
            TaxonomyItemVersion,
            resource=found_taxonomy_item,
            page_number=pagination_info.cursor_page,
            active_page=pagination_info.cursor_page,
            last_page=pagination_info.last_page.page,
            collection_size=pagination_info.collection_size,
            item_links=items,
        )
        self_link = LinkGenerator.get_link_of(
            page_resource, query_params=pagination_options.to_query_params()
        )

        extra_links = generate_page_links(
            page_resource, pagination_info, pagination_options
        )

        return ApiResponseGenerator.get_api_response(
            page_resource,
            query_params=pagination_options.to_query_params(),
            extra_links=[
                LinkGenerator.get_link_of(
                    page_resource.get_page(1),
                    query_params=pagination_options.to_query_params(cursor=None),
                ),
                self_link,
                *extra_links,
            ],
            extra_embedded=embedded_items,
            link_to_relations=TAXONOMY_ITEM_VERSION_PAGE_EXTRA_LINK_RELATIONS,
        )


@API_V1.route(
    "/namespaces/<string:namespace>/taxonomies/<string:taxonomy>/items/<string:taxonomy_item>/versions/<string:version>/"
)
class TaxonomyItemVersionView(MethodView):
    """Endpoint for a single version of a taxonomy item."""

    def _check_path_params(
        self, namespace: str, taxonomy: str, taxonomy_item: str, version: str
    ):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not taxonomy or not taxonomy.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy id has the wrong format!"),
            )
        if not taxonomy_item or not taxonomy_item.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy item id has the wrong format!"),
            )
        if not version or not version.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext(
                    "The requested taxonomy item version has the wrong format!"
                ),
            )

    def _get_taxonomy_item_version(
        self, namespace: str, taxonomy: str, taxonomy_item: str, version: str
    ) -> TaxonomyItemVersion:
        namespace_id = int(namespace)
        taxonomy_id = int(taxonomy)
        taxonomy_item_id = int(taxonomy_item)
        version_nr = int(version)
        found_taxonomy_item_version: Optional[
            TaxonomyItemVersion
        ] = TaxonomyItemVersion.query.filter(
            TaxonomyItemVersion.version == version_nr,
            TaxonomyItemVersion.taxonomy_item_id == taxonomy_item_id,
        ).first()

        if (
            found_taxonomy_item_version is None
            or found_taxonomy_item_version.taxonomy_item.taxonomy_id != taxonomy_id
            or found_taxonomy_item_version.taxonomy_item.taxonomy.namespace_id
            != namespace_id
        ):
            abort(
                HTTPStatus.NOT_FOUND, message=gettext("Taxonomy item version not found.")
            )
        return found_taxonomy_item_version  # is not None because abort raises exception

    @API_V1.response(DynamicApiResponseSchema(TaxonomyItemSchema()))
    @API_V1.require_jwt("jwt")
    def get(
        self,
        namespace: str,
        taxonomy: str,
        taxonomy_item: str,
        version: str,
        **kwargs: Any,
    ):
        """Get a single taxonomy item version."""
        self._check_path_params(
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            version=version,
        )
        found_taxonomy_item_version = self._get_taxonomy_item_version(
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            version=version,
        )
        FLASK_OSO.authorize_and_set_resource(found_taxonomy_item_version)

        return ApiResponseGenerator.get_api_response(
            found_taxonomy_item_version,
            link_to_relations=TAXONOMY_ITEM_VERSION_EXTRA_LINK_RELATIONS,
        )

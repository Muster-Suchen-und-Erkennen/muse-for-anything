"""Module containing the taxonomy API endpoints of the v1 API."""

from datetime import datetime
from http import HTTPStatus
from typing import Any, List, Optional

from flask.globals import g
from flask.views import MethodView
from flask_babel import gettext
from flask_smorest import abort
from marshmallow.utils import INCLUDE
from sqlalchemy.sql.expression import exists, literal, or_, select

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
from muse_for_anything.db.models.users import User
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource

from ...db.db import DB
from ...db.models.namespace import Namespace
from ...db.models.taxonomies import Taxonomy, TaxonomyItem, TaxonomyItemVersion
from ..base_models import (
    ApiResponse,
    ChangedApiObject,
    ChangedApiObjectSchema,
    CollectionFilter,
    CollectionFilterOption,
    CursorPageSchema,
    DynamicApiResponseSchema,
    NewApiObject,
    NewApiObjectSchema,
)
from .constants import (
    CHANGED_REL,
    CREATE,
    CREATE_REL,
    DELETE_REL,
    NEW_REL,
    RESTORE,
    RESTORE_REL,
    TAXONOMY_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_PAGE_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_REL_TYPE,
    TAXONOMY_PAGE_EXTRA_LINK_RELATIONS,
    TAXONOMY_REL_TYPE,
    UPDATE,
    UPDATE_REL,
)

# import taxonomy specific generators to load them
from .generators import taxonomy, taxonomy_item  # noqa
from .models.ontology import (
    TaxonomyItemPageParamsSchema,
    TaxonomyItemRelationSchema,
    TaxonomyItemSchema,
    TaxonomyPageParamsSchema,
    TaxonomySchema,
)
from .root import API_V1


@API_V1.route("/namespaces/<string:namespace>/taxonomies/")
class TaxonomiesView(MethodView):
    """Endpoint for all namespace taxonomies."""

    def _check_path_params(self, namespace: str):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )

    def _get_namespace(self, namespace: str) -> Namespace:
        namespace_id = int(namespace)
        namespace_id = int(namespace)
        found_namespace: Optional[Namespace] = Namespace.query.filter(
            Namespace.id == namespace_id
        ).first()

        if found_namespace is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Namespace not found."))
        return found_namespace  # is not None because abort raises exception

    @API_V1.arguments(TaxonomyPageParamsSchema, location="query", as_kwargs=True)
    @API_V1.response(200, DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, search: Optional[str] = None, **kwargs: Any):
        """Get the page of taxonomies."""
        self._check_path_params(namespace=namespace)
        found_namespace = self._get_namespace(namespace=namespace)
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                TAXONOMY_REL_TYPE, is_collection=True, parent_resource=found_namespace
            )
        )

        pagination_options: PaginationOptions = prepare_pagination_query_args(
            **kwargs, _sort_default="name"
        )

        taxonomy_filter = (
            Taxonomy.deleted_on == None,
            Taxonomy.namespace_id == int(namespace),
        )

        if search:
            taxonomy_filter = (
                *taxonomy_filter,
                or_(
                    # TODO switch from contains to match depending on DB...
                    Taxonomy.name.contains(search),
                    Taxonomy.description.contains(search),
                ),
            )

        pagination_info = default_get_page_info(
            Taxonomy,
            taxonomy_filter,
            pagination_options,
            [Taxonomy.name, Taxonomy.created_on, Taxonomy.updated_on],
        )

        taxonomies: List[Taxonomy] = pagination_info.page_items_query.all()

        embedded_items, items = dump_embedded_page_items(
            taxonomies, TaxonomySchema(), TAXONOMY_EXTRA_LINK_RELATIONS
        )

        page_resource = PageResource(
            Taxonomy,
            resource=found_namespace,
            page_number=pagination_info.cursor_page,
            active_page=pagination_info.cursor_page,
            last_page=pagination_info.last_page.page,
            collection_size=pagination_info.collection_size,
            item_links=items,
        )

        filter_query_params = {}
        if search:
            filter_query_params["search"] = search

        page_resource.filters = [
            CollectionFilter(key="?search", type="search"),
            CollectionFilter(
                key="?sort",
                type="sort",
                options=[
                    CollectionFilterOption("name"),
                    CollectionFilterOption("created_on"),
                    CollectionFilterOption("updated_on"),
                ],
            ),
        ]

        self_link = LinkGenerator.get_link_of(
            page_resource,
            query_params=pagination_options.to_query_params(
                extra_params=filter_query_params
            ),
        )

        extra_links = generate_page_links(
            page_resource,
            pagination_info,
            pagination_options,
            extra_params=filter_query_params,
        )

        return ApiResponseGenerator.get_api_response(
            page_resource,
            query_params=pagination_options.to_query_params(
                extra_params=filter_query_params
            ),
            extra_links=[
                LinkGenerator.get_link_of(
                    page_resource.get_page(1),
                    query_params=pagination_options.to_query_params(
                        cursor=None, extra_params=filter_query_params
                    ),
                ),
                self_link,
                *extra_links,
            ],
            extra_embedded=embedded_items,
            link_to_relations=TAXONOMY_PAGE_EXTRA_LINK_RELATIONS,
        )

    @API_V1.arguments(TaxonomySchema())
    @API_V1.response(200, DynamicApiResponseSchema(NewApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def post(self, data, namespace: str):
        """Create a new taxonomy."""
        self._check_path_params(namespace=namespace)

        found_namespace = self._get_namespace(namespace=namespace)
        if found_namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )

        FLASK_OSO.authorize_and_set_resource(
            OsoResource(TAXONOMY_REL_TYPE, parent_resource=found_namespace), action=CREATE
        )

        existing: bool = (
            DB.session.query(literal(True))
            .filter(
                Taxonomy.query.filter(
                    Taxonomy.namespace_id == found_namespace.id,
                    Taxonomy.name == data["name"],
                ).exists()
            )
            .scalar()
        )
        if existing:
            abort(
                400,
                f"Name {data['name']} is already used for another Taxonomy in this Namespace!",
            )

        taxonomy = Taxonomy(
            namespace=found_namespace,
            name=data.get("name"),
            description=data.get("description", ""),
        )
        DB.session.add(taxonomy)
        DB.session.flush()
        user: User = g.current_user
        user.set_role_for_resource("owner", taxonomy)
        DB.session.commit()

        taxonomy_response = ApiResponseGenerator.get_api_response(
            taxonomy, link_to_relations=TAXONOMY_EXTRA_LINK_RELATIONS
        )
        taxonomy_link = taxonomy_response.data.self
        taxonomy_response.data = TaxonomySchema().dump(taxonomy_response.data)

        self_link = LinkGenerator.get_link_of(
            PageResource(Taxonomy, resource=found_namespace),
            for_relation=CREATE_REL,
            extra_relations=(TAXONOMY_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = NEW_REL

        return ApiResponse(
            links=[taxonomy_link],
            embedded=[taxonomy_response],
            data=NewApiObject(
                self=self_link,
                new=taxonomy_link,
            ),
        )


@API_V1.route("/namespaces/<string:namespace>/taxonomies/<string:taxonomy>/")
class TaxonomyView(MethodView):
    """Endpoint for a single taxonomy."""

    def _check_path_params(self, namespace: str, taxonomy: str):
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

    def _get_taxonomy(self, namespace: str, taxonomy: str) -> Taxonomy:
        namespace_id = int(namespace)
        taxonomy_id = int(taxonomy)
        found_taxonomy: Optional[Taxonomy] = (
            Taxonomy.get_eager_query()
            .filter(
                Taxonomy.id == taxonomy_id,
                Taxonomy.namespace_id == namespace_id,
            )
            .first()
        )

        if found_taxonomy is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Taxonomy not found."))
        return found_taxonomy  # is not None because abort raises exception

    def _check_if_namespace_modifiable(self, namespace: Namespace):
        if namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )

    def _check_if_modifiable(self, taxonomy: Taxonomy):
        self._check_if_namespace_modifiable(namespace=taxonomy.namespace)
        if taxonomy.deleted_on is not None:
            # cannot modify deleted taxonomy!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy is marked as deleted and cannot be modified further."
                ),
            )

    @API_V1.response(200, DynamicApiResponseSchema(TaxonomySchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, taxonomy: str):
        """Get a single taxonomy."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )
        FLASK_OSO.authorize_and_set_resource(found_taxonomy)

        embedded_items: List[ApiResponse] = []

        item_schema = TaxonomyItemSchema()
        relation_schema = TaxonomyItemRelationSchema()

        with skip_slow_policy_checks_for_links_in_embedded_responses():
            for item in found_taxonomy.current_items:
                item_response = ApiResponseGenerator.get_api_response(item)
                if item_response:
                    item_response.data = item_schema.dump(item_response.data)
                    embedded_items.append(item_response)
                for relation in item.current_related:
                    relation_response = ApiResponseGenerator.get_api_response(relation)
                    if relation_response:
                        relation_response.data = relation_schema.dump(
                            relation_response.data
                        )
                        embedded_items.append(relation_response)

        return ApiResponseGenerator.get_api_response(
            found_taxonomy,
            link_to_relations=TAXONOMY_EXTRA_LINK_RELATIONS,
            extra_embedded=embedded_items,
        )

    @API_V1.arguments(TaxonomySchema())
    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def put(self, data, namespace: str, taxonomy: str):
        """Update taxonomy in place."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )

        self._check_if_modifiable(found_taxonomy)

        FLASK_OSO.authorize_and_set_resource(found_taxonomy, action=UPDATE)

        if found_taxonomy.name != data.get("name"):
            existing: bool = (
                DB.session.query(literal(True))
                .filter(
                    Taxonomy.query.filter(
                        Taxonomy.namespace_id == found_taxonomy.namespace_id,
                        Taxonomy.name == data["name"],
                    ).exists()
                )
                .scalar()
            )
            if existing:
                abort(
                    400,
                    f"Name {data['name']} is already used for another Taxonomy in this namespace!",
                )

        found_taxonomy.update(
            name=data.get("name"),
            description=data.get("description", ""),
        )
        DB.session.add(found_taxonomy)
        DB.session.commit()

        taxonomy_response = ApiResponseGenerator.get_api_response(
            found_taxonomy, link_to_relations=TAXONOMY_EXTRA_LINK_RELATIONS
        )
        taxonomy_link = taxonomy_response.data.self
        taxonomy_response.data = TaxonomySchema().dump(taxonomy_response.data)

        self_link = LinkGenerator.get_link_of(
            found_taxonomy,
            for_relation=UPDATE_REL,
            extra_relations=(TAXONOMY_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[taxonomy_link],
            embedded=[taxonomy_response],
            data=ChangedApiObject(
                self=self_link,
                changed=taxonomy_link,
            ),
        )

    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def post(self, namespace: str, taxonomy: str):  # restore action
        """Restore a deleted taxonomy."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )
        self._check_if_namespace_modifiable(found_taxonomy.namespace)

        FLASK_OSO.authorize_and_set_resource(found_taxonomy, action=RESTORE)

        # only actually restore when not already restored
        if found_taxonomy.deleted_on is not None:
            # restore object type
            found_taxonomy.deleted_on = None
            DB.session.add(found_taxonomy)
            DB.session.commit()

        taxonomy_response = ApiResponseGenerator.get_api_response(
            found_taxonomy, link_to_relations=TAXONOMY_EXTRA_LINK_RELATIONS
        )
        taxonomy_link = taxonomy_response.data.self
        taxonomy_response.data = TaxonomySchema().dump(taxonomy_response.data)

        self_link = LinkGenerator.get_link_of(
            found_taxonomy,
            for_relation=RESTORE_REL,
            extra_relations=(TAXONOMY_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[taxonomy_link],
            embedded=[taxonomy_response],
            data=ChangedApiObject(
                self=self_link,
                changed=taxonomy_link,
            ),
        )

    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def delete(self, namespace: str, taxonomy: str):
        """Delete a taxonomy."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )
        self._check_if_namespace_modifiable(found_taxonomy.namespace)

        FLASK_OSO.authorize_and_set_resource(found_taxonomy)

        # only actually delete when not already deleted
        if found_taxonomy.deleted_on is None:
            # soft delete namespace
            found_taxonomy.deleted_on = datetime.utcnow()
            DB.session.add(found_taxonomy)
            DB.session.commit()

        taxonomy_response = ApiResponseGenerator.get_api_response(
            found_taxonomy, link_to_relations=TAXONOMY_EXTRA_LINK_RELATIONS
        )
        taxonomy_link = taxonomy_response.data.self
        taxonomy_response.data = TaxonomySchema().dump(taxonomy_response.data)

        self_link = LinkGenerator.get_link_of(
            found_taxonomy,
            for_relation=DELETE_REL,
            extra_relations=(TAXONOMY_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[taxonomy_link],
            embedded=[taxonomy_response],
            data=ChangedApiObject(
                self=self_link,
                changed=taxonomy_link,
            ),
        )


@API_V1.route("/namespaces/<string:namespace>/taxonomies/<string:taxonomy>/items/")
class TaxonomyItemsView(MethodView):
    """Endpoint for all taxonomy items."""

    def _check_path_params(self, namespace: str, taxonomy: str):
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

    def _get_lazy_loaded_taxonomy(self, namespace: str, taxonomy: str) -> Taxonomy:
        namespace_id = int(namespace)
        taxonomy_id = int(taxonomy)
        found_taxonomy: Optional[Taxonomy] = Taxonomy.query.filter(
            Taxonomy.id == taxonomy_id,
            Taxonomy.namespace_id == namespace_id,
        ).first()

        if found_taxonomy is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Taxonomy not found."))
        return found_taxonomy  # is not None because abort raises exception

    def _check_if_namespace_modifiable(self, namespace: Namespace):
        if namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )

    def _check_if_modifiable(self, taxonomy: Taxonomy):
        self._check_if_namespace_modifiable(namespace=taxonomy.namespace)
        if taxonomy.deleted_on is not None:
            # cannot modify deleted taxonomy!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy is marked as deleted and cannot be modified further."
                ),
            )

    @API_V1.arguments(TaxonomyItemPageParamsSchema, location="query", as_kwargs=True)
    @API_V1.response(200, DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, taxonomy: str, search: Optional[str] = None, **kwargs):
        """Get all items of a taxonomy."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_lazy_loaded_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                TAXONOMY_ITEM_REL_TYPE, is_collection=True, parent_resource=found_taxonomy
            )
        )

        pagination_options: PaginationOptions = prepare_pagination_query_args(
            **kwargs, _sort_default="-created_on"
        )

        taxonomy_item_filter = (
            TaxonomyItem.deleted_on == None,
            TaxonomyItem.taxonomy_id == int(taxonomy),
        )

        if search:
            taxonomy_item_filter = (
                *taxonomy_item_filter,
                exists(
                    select(TaxonomyItemVersion)
                    .where(TaxonomyItem.current_version_id == TaxonomyItemVersion.id)
                    .where(
                        or_(
                            TaxonomyItemVersion.name.contains(search),
                            TaxonomyItemVersion.description.contains(search),
                        ),
                    )
                ),
            )

        pagination_info = default_get_page_info(
            TaxonomyItem,
            taxonomy_item_filter,
            pagination_options,
            [TaxonomyItem.created_on, TaxonomyItem.updated_on],
        )

        taxonomy_items: List[TaxonomyItem] = pagination_info.page_items_query.all()

        embedded_items, items = dump_embedded_page_items(
            taxonomy_items, TaxonomyItemSchema(), TAXONOMY_ITEM_EXTRA_LINK_RELATIONS
        )

        page_resource = PageResource(
            TaxonomyItem,
            resource=found_taxonomy,
            page_number=pagination_info.cursor_page,
            active_page=pagination_info.cursor_page,
            last_page=pagination_info.last_page.page,
            collection_size=pagination_info.collection_size,
            item_links=items,
        )

        filter_query_params = {}
        if search:
            filter_query_params["search"] = search

        page_resource.filters = [
            CollectionFilter(key="?search", type="search"),
            CollectionFilter(
                key="?sort",
                type="sort",
                options=[
                    CollectionFilterOption("created_on"),
                    CollectionFilterOption("updated_on"),
                ],
            ),
        ]

        self_link = LinkGenerator.get_link_of(
            page_resource,
            query_params=pagination_options.to_query_params(
                extra_params=filter_query_params
            ),
        )

        extra_links = generate_page_links(
            page_resource,
            pagination_info,
            pagination_options,
            extra_params=filter_query_params,
        )

        return ApiResponseGenerator.get_api_response(
            page_resource,
            query_params=pagination_options.to_query_params(
                extra_params=filter_query_params
            ),
            extra_links=[
                LinkGenerator.get_link_of(
                    page_resource.get_page(1),
                    query_params=pagination_options.to_query_params(
                        cursor=None, extra_params=filter_query_params
                    ),
                ),
                self_link,
                *extra_links,
            ],
            extra_embedded=embedded_items,
            link_to_relations=TAXONOMY_ITEM_PAGE_EXTRA_LINK_RELATIONS,
        )

    @API_V1.arguments(TaxonomyItemSchema())
    @API_V1.response(200, DynamicApiResponseSchema(NewApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def post(self, data, namespace: str, taxonomy: str):
        """Create a new taxonomy item."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy = self._get_lazy_loaded_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )
        if found_taxonomy.namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )
        if found_taxonomy.deleted_on is not None:
            # cannot modify deleted taxonomy!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy is marked as deleted and cannot be modified further."
                ),
            )

        FLASK_OSO.authorize_and_set_resource(
            OsoResource(TAXONOMY_ITEM_REL_TYPE, parent_resource=found_taxonomy),
            action=CREATE,
        )

        taxonomy_item = TaxonomyItem(
            taxonomy=found_taxonomy,
        )
        DB.session.add(taxonomy_item)
        DB.session.flush()
        taxonomy_item_version = TaxonomyItemVersion(
            taxonomy_item=taxonomy_item,
            version=1,
            name=data["name"],
            description=data.get("description", ""),
            sort_key=data.get("sort_key", 10),
        )
        taxonomy_item.current_version = taxonomy_item_version
        DB.session.add(taxonomy_item)
        DB.session.add(taxonomy_item_version)
        DB.session.commit()

        taxonomy_item_response = ApiResponseGenerator.get_api_response(
            taxonomy_item, link_to_relations=TAXONOMY_ITEM_EXTRA_LINK_RELATIONS
        )
        taxonomy_item_link = taxonomy_item_response.data.self
        taxonomy_item_response.data = TaxonomyItemSchema().dump(
            taxonomy_item_response.data
        )

        taxonomy_response = ApiResponseGenerator.get_api_response(
            taxonomy_item.taxonomy, link_to_relations=TAXONOMY_EXTRA_LINK_RELATIONS
        )
        taxonomy_link = taxonomy_response.data.self
        taxonomy_response.data = TaxonomySchema().dump(taxonomy_response.data)

        self_link = LinkGenerator.get_link_of(
            PageResource(TaxonomyItem, resource=found_taxonomy),
            for_relation=CREATE_REL,
            extra_relations=(TAXONOMY_ITEM_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = NEW_REL

        return ApiResponse(
            links=[taxonomy_item_link, taxonomy_link],
            embedded=[taxonomy_item_response, taxonomy_response],
            data=NewApiObject(
                self=self_link,
                new=taxonomy_item_link,
            ),
        )

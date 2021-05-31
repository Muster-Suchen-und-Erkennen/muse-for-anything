"""Module containing the taxonomy API endpoints of the v1 API."""

from datetime import datetime
from muse_for_anything.db.models.users import User
from muse_for_anything.api.v1_api.request_helpers import (
    ApiResponseGenerator,
    LinkGenerator,
    PageResource,
    skip_slow_policy_checks_for_links_in_embedded_responses,
)
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource

from marshmallow.utils import INCLUDE
from flask_babel import gettext
from typing import Any, List, Optional, Union, cast
from flask.globals import g
from flask.views import MethodView
from sqlalchemy.sql.expression import literal
from flask_smorest import abort
from http import HTTPStatus

from .root import API_V1
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
from ...db.pagination import get_page_info
from ...db.models.namespace import Namespace
from ...db.models.taxonomies import Taxonomy, TaxonomyItem, TaxonomyItemVersion

from .models.ontology import (
    TaxonomyItemRelationSchema,
    TaxonomyItemSchema,
    TaxonomySchema,
)

from .taxonomy_helpers import (
    TAXONOMY_EXTRA_LINK_RELATIONS,
    TAXONOMY_PAGE_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_PAGE_EXTRA_LINK_RELATIONS,
    TAXONOMY_ITEM_EXTRA_LINK_RELATIONS,
)


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

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, **kwargs: Any):
        """Get the page of taxonomies."""
        self._check_path_params(namespace=namespace)
        found_namespace = self._get_namespace(namespace=namespace)
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                "ont-taxonomy", is_collection=True, parent_resource=found_namespace
            )
        )

        cursor: Optional[str] = kwargs.get("cursor", None)
        item_count: int = cast(int, kwargs.get("item_count", 25))
        sort: str = cast(str, kwargs.get("sort", "name").lstrip("+"))

        taxonomy_filter = (
            Taxonomy.deleted_on == None,
            Taxonomy.namespace_id == int(namespace),
        )

        pagination_info = get_page_info(
            Taxonomy,
            Taxonomy.id,
            [Taxonomy.name],
            cursor,
            sort,
            item_count,
            filter_criteria=taxonomy_filter,
        )

        taxonomies: List[Taxonomy] = pagination_info.page_items_query.all()

        embedded_items: List[ApiResponse] = []
        items: List[ApiLink] = []

        dump = TaxonomySchema().dump
        with skip_slow_policy_checks_for_links_in_embedded_responses():
            for taxonomy in taxonomies:
                response = ApiResponseGenerator.get_api_response(
                    taxonomy, link_to_relations=TAXONOMY_EXTRA_LINK_RELATIONS
                )
                if response:
                    items.append(response.data.self)
                    response.data = dump(response.data)
                    embedded_items.append(response)

        query_params = {
            "item-count": item_count,
            "sort": sort,
        }

        self_query_params = dict(query_params)

        if cursor:
            self_query_params["cursor"] = cursor

        page_resource = PageResource(
            Taxonomy,
            resource=found_namespace,
            active_page=pagination_info.cursor_page,
            last_page=pagination_info.last_page.page,
            collection_size=pagination_info.collection_size,
            item_links=items,
        )
        self_link = LinkGenerator.get_link_of(
            page_resource.get_page(pagination_info.cursor_page),
            query_params=self_query_params,
        )

        extra_links: List[ApiLink] = [self_link]

        if pagination_info.last_page is not None:
            if pagination_info.cursor_page != pagination_info.last_page.page:
                # only if current page is not last page
                last_query_params = dict(query_params)
                last_query_params["cursor"] = str(pagination_info.last_page.cursor)

                extra_links.append(
                    LinkGenerator.get_link_of(
                        page_resource.get_page(pagination_info.last_page.page),
                        query_params=last_query_params,
                    )
                )

        for page in pagination_info.surrounding_pages:
            if page == pagination_info.last_page:
                continue  # link already included
            page_query_params = dict(query_params)
            page_query_params["cursor"] = str(page.cursor)

            extra_links.append(
                LinkGenerator.get_link_of(
                    page_resource.get_page(page.page),
                    query_params=page_query_params,
                )
            )

        return ApiResponseGenerator.get_api_response(
            page_resource,
            query_params=self_query_params,
            extra_links=[
                LinkGenerator.get_link_of(
                    page_resource.get_page(1),
                    query_params=query_params,
                ),
                *extra_links,
            ],
            extra_embedded=embedded_items,
            link_to_relations=TAXONOMY_PAGE_EXTRA_LINK_RELATIONS,
        )

    @API_V1.arguments(TaxonomySchema())
    @API_V1.response(DynamicApiResponseSchema(NewApiObjectSchema()))
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
            OsoResource("ont-taxonomy", parent_resource=found_namespace), action="CREATE"
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
            for_relation="create",
            extra_relations=("ont-taxonomy",),
            ignore_deleted=True,
        )
        self_link.resource_type = "new"

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

    @API_V1.response(DynamicApiResponseSchema(TaxonomySchema()))
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
    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def put(self, data, namespace: str, taxonomy: str):
        """Update taxonomy in place."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )

        self._check_if_modifiable(found_taxonomy)

        FLASK_OSO.authorize_and_set_resource(found_taxonomy, action="EDIT")

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
            for_relation="update",
            extra_relations=("ont-taxonomy",),
            ignore_deleted=True,
        )
        self_link.resource_type = "changed"

        return ApiResponse(
            links=[taxonomy_link],
            embedded=[taxonomy_response],
            data=ChangedApiObject(
                self=self_link,
                changed=taxonomy_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def post(self, namespace: str, taxonomy: str):  # restore action
        """Restore a deleted taxonomy."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )
        self._check_if_namespace_modifiable(found_taxonomy.namespace)

        FLASK_OSO.authorize_and_set_resource(found_taxonomy, action="RESTORE")

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
            for_relation="restore",
            extra_relations=("ont-taxonomy",),
            ignore_deleted=True,
        )
        self_link.resource_type = "changed"

        return ApiResponse(
            links=[taxonomy_link],
            embedded=[taxonomy_response],
            data=ChangedApiObject(
                self=self_link,
                changed=taxonomy_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
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
            for_relation="delete",
            extra_relations=("ont-taxonomy",),
            ignore_deleted=True,
        )
        self_link.resource_type = "changed"

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

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, taxonomy: str, **kwargs):
        """Get all items of a taxonomy."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_lazy_loaded_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                "ont-taxonomy-item", is_collection=True, parent_resource=found_taxonomy
            )
        )

        cursor: Optional[str] = kwargs.get("cursor", None)
        item_count: int = cast(int, kwargs.get("item_count", 25))
        sort: str = cast(str, kwargs.get("sort", "-updated_on").lstrip("+"))

        taxonomy_item_filter = (
            TaxonomyItem.deleted_on == None,
            TaxonomyItem.taxonomy_id == int(taxonomy),
        )

        pagination_info = get_page_info(
            TaxonomyItem,
            TaxonomyItem.id,
            [TaxonomyItem.updated_on],
            cursor,
            sort,
            item_count,
            filter_criteria=taxonomy_item_filter,
        )

        taxonomy_items: List[TaxonomyItem] = pagination_info.page_items_query.all()

        embedded_items: List[ApiResponse] = []
        items: List[ApiLink] = []

        dump = TaxonomyItemSchema().dump
        with skip_slow_policy_checks_for_links_in_embedded_responses():
            for taxonomy_item in taxonomy_items:
                response = ApiResponseGenerator.get_api_response(
                    taxonomy_item, link_to_relations=TAXONOMY_ITEM_EXTRA_LINK_RELATIONS
                )
                if response:
                    items.append(response.data.self)
                    response.data = dump(response.data)
                    embedded_items.append(response)

        query_params = {
            "item-count": item_count,
            "sort": sort,
        }

        self_query_params = dict(query_params)

        if cursor:
            self_query_params["cursor"] = cursor

        page_resource = PageResource(
            TaxonomyItem,
            resource=found_taxonomy,
            active_page=pagination_info.cursor_page,
            last_page=pagination_info.last_page.page,
            collection_size=pagination_info.collection_size,
            item_links=items,
        )
        self_link = LinkGenerator.get_link_of(
            page_resource.get_page(pagination_info.cursor_page),
            query_params=self_query_params,
        )

        extra_links: List[ApiLink] = [self_link]

        if pagination_info.last_page is not None:
            if pagination_info.cursor_page != pagination_info.last_page.page:
                # only if current page is not last page
                last_query_params = dict(query_params)
                last_query_params["cursor"] = str(pagination_info.last_page.cursor)

                extra_links.append(
                    LinkGenerator.get_link_of(
                        page_resource.get_page(pagination_info.last_page.page),
                        query_params=last_query_params,
                    )
                )

        for page in pagination_info.surrounding_pages:
            if page == pagination_info.last_page:
                continue  # link already included
            page_query_params = dict(query_params)
            page_query_params["cursor"] = str(page.cursor)

            extra_links.append(
                LinkGenerator.get_link_of(
                    page_resource.get_page(page.page),
                    query_params=page_query_params,
                )
            )

        return ApiResponseGenerator.get_api_response(
            page_resource,
            query_params=self_query_params,
            extra_links=[
                LinkGenerator.get_link_of(
                    page_resource.get_page(1),
                    query_params=query_params,
                ),
                *extra_links,
            ],
            extra_embedded=embedded_items,
            link_to_relations=TAXONOMY_ITEM_PAGE_EXTRA_LINK_RELATIONS,
        )

    @API_V1.arguments(TaxonomyItemSchema())
    @API_V1.response(DynamicApiResponseSchema(NewApiObjectSchema()))
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
            OsoResource("ont-taxonomy-item", parent_resource=found_taxonomy),
            action="CREATE",
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
            for_relation="create",
            extra_relations=("ont-taxonomy-item",),
            ignore_deleted=True,
        )
        self_link.resource_type = "new"

        return ApiResponse(
            links=[taxonomy_item_link, taxonomy_link],
            embedded=[taxonomy_item_response, taxonomy_response],
            data=NewApiObject(
                self=self_link,
                new=taxonomy_item_link,
            ),
        )

"""Module containing the taxonomy API endpoints of the v1 API."""

from datetime import datetime

from marshmallow.utils import INCLUDE
from flask_babel import gettext
from muse_for_anything.api.util import template_url_for
from typing import Any, Callable, Dict, List, Optional, Union, cast
from flask.helpers import url_for
from flask.views import MethodView
from sqlalchemy.sql.expression import asc, desc, literal
from sqlalchemy.orm.query import Query
from flask_smorest import abort
from http import HTTPStatus

from .root import API_V1
from ..base_models import (
    ApiLink,
    ApiResponse,
    ChangedApiObject,
    ChangedApiObjectSchema,
    CursorPage,
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

from .models.ontology import TaxonomyItemSchema, TaxonomySchema

from .namespace_helpers import (
    query_params_to_api_key,
)

from .taxonomy_helpers import (
    action_links_for_taxonomy,
    action_links_for_taxonomy_item_page,
    action_links_for_taxonomy_page,
    create_action_link_for_taxonomy_item_page,
    create_action_link_for_taxonomy_page,
    nav_links_for_taxonomy,
    nav_links_for_taxonomy_item_page,
    nav_links_for_taxonomy_page,
    taxonomy_item_page_params_to_key,
    taxonomy_item_relation_to_api_response,
    taxonomy_item_to_api_response,
    taxonomy_item_to_taxonomy_item_data,
    taxonomy_page_params_to_key,
    taxonomy_to_api_response,
    taxonomy_to_taxonomy_data,
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
    def get(self, namespace: str, **kwargs: Any):
        """Get the page of taxonomies."""
        self._check_path_params(namespace=namespace)
        found_namespace = self._get_namespace(namespace=namespace)

        cursor: Optional[str] = kwargs.get("cursor", None)
        item_count: int = cast(int, kwargs.get("item_count", 50))
        sort: str = cast(str, kwargs.get("sort", "name").lstrip("+"))
        sort_function: Callable[..., Any] = (
            desc if sort is not None and sort.startswith("-") else asc
        )
        sort_key: str = sort.lstrip("+-") if sort is not None else "name"

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

        query: Query = Taxonomy.get_eager_query().filter(*taxonomy_filter)

        query = query.order_by(asc(Taxonomy.id))

        if sort_key == "name":
            query = query.order_by(sort_function(Taxonomy.name.collate("NOCASE")))

        if cursor is not None and cursor.isdigit():
            # hope that cursor row has not jumped compared to last query in get_page_info
            query = query.offset(pagination_info.cursor_row)

        query = query.limit(item_count)

        taxonomies: List[Taxonomy] = query.all()

        embedded_items: List[ApiResponse] = [
            taxonomy_to_api_response(taxonomy) for taxonomy in taxonomies
        ]
        items: List[ApiLink] = [item.data.get("self") for item in embedded_items]

        query_params = {
            "item_count": item_count,
            "sort": sort,
        }

        self_query_params = dict(query_params)

        if cursor:
            self_query_params["cursor"] = cursor

        self_rels = []
        if pagination_info.cursor_page == 1:
            self_rels.append("first")
        if (
            pagination_info.last_page
            and pagination_info.cursor_page == pagination_info.last_page.page
        ):
            self_rels.append("last")

        self_link = ApiLink(
            href=url_for(
                "api-v1.TaxonomiesView",
                namespace=namespace,
                _external=True,
                **self_query_params,
            ),
            rel=(
                *self_rels,
                "page",
                f"page-{pagination_info.cursor_page}",
                "collection",
            ),
            resource_type="ont-taxonomy",
            resource_key=taxonomy_page_params_to_key(namespace, self_query_params),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
            ),
        )

        extra_links: List[ApiLink] = [self_link]

        if pagination_info.last_page is not None:
            if pagination_info.cursor_page != pagination_info.last_page.page:
                # only if current page is not last page
                last_query_params = dict(query_params)
                last_query_params["cursor"] = str(pagination_info.last_page.cursor)

                extra_links.append(
                    ApiLink(
                        href=url_for(
                            "api-v1.TaxonomiesView",
                            namespace=namespace,
                            _external=True,
                            **last_query_params,
                        ),
                        rel=(
                            "last",
                            "page",
                            f"page-{pagination_info.last_page.page}",
                            "collection",
                        ),
                        resource_type="ont-taxonomy",
                        resource_key=taxonomy_page_params_to_key(
                            namespace, last_query_params
                        ),
                        schema=url_for(
                            "api-v1.ApiSchemaView",
                            schema_id="TaxonomySchema",
                            _external=True,
                        ),
                    )
                )

        for page in pagination_info.surrounding_pages:
            if page == pagination_info.last_page:
                continue  # link already included
            page_query_params = dict(query_params)
            page_query_params["cursor"] = str(page.cursor)

            extra_rels = []
            if page.page + 1 == pagination_info.cursor_page:
                extra_rels.append("prev")
            if page.page - 1 == pagination_info.cursor_page:
                extra_rels.append("next")

            extra_links.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TaxonomiesView",
                        namespace=namespace,
                        _external=True,
                        **page_query_params,
                    ),
                    rel=(
                        *extra_rels,
                        "page",
                        f"page-{page.page}",
                        "collection",
                    ),
                    resource_type="ont-taxonomy",
                    resource_key=taxonomy_page_params_to_key(
                        namespace, page_query_params
                    ),
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
                    ),
                )
            )

        extra_links.extend(nav_links_for_taxonomy_page(namespace))

        extra_links.extend(action_links_for_taxonomy_page(found_namespace))

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True, **query_params),
                    rel=("first", "page", "page-1", "collection", "nav"),
                    resource_type="ont-namespace",
                    resource_key=query_params_to_api_key({"item-count": item_count}),
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                ApiLink(
                    href=url_for(
                        "api-v1.TaxonomiesView",
                        namespace=namespace,
                        _external=True,
                        **query_params,
                    ),
                    rel=("first", "page", "page-1", "collection"),
                    resource_type="ont-taxonomy",
                    resource_key=taxonomy_page_params_to_key(namespace, query_params),
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="TaxonomySchema", _external=True
                    ),
                ),
                *extra_links,
            ],
            embedded=embedded_items,
            data=CursorPage(
                self=self_link,
                collection_size=pagination_info.collection_size,
                page=pagination_info.cursor_page,
                first_row=pagination_info.cursor_row + 1,
                items=items,
            ),
        )

    @API_V1.arguments(TaxonomySchema())
    @API_V1.response(DynamicApiResponseSchema(NewApiObjectSchema()))
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
        DB.session.commit()

        taxonomy_link = taxonomy_to_taxonomy_data(taxonomy).self
        taxonomy_data = taxonomy_to_api_response(taxonomy)

        self_link = create_action_link_for_taxonomy_page(namespace=namespace)
        self_link.rel = (*self_link.rel, "ont-taxonomy")
        self_link.resource_type = "new"

        return ApiResponse(
            links=[taxonomy_link],
            embedded=[taxonomy_data],
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
    def get(self, namespace: str, taxonomy: str):
        """Get a single taxonomy."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )

        embedded_items: List[ApiResponse] = []

        for item in found_taxonomy.current_items:
            embedded_items.append(taxonomy_item_to_api_response(item))
            for relation in item.current_related:
                embedded_items.append(taxonomy_item_relation_to_api_response(relation))

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for(
                        "api-v1.NamespacesView",
                        _external=True,
                        item_count=50,
                        sort="name",
                    ),
                    rel=("first", "page", "collection", "nav"),
                    resource_type="ont-namespace",
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                *nav_links_for_taxonomy(found_taxonomy),
                *action_links_for_taxonomy(found_taxonomy),
            ],
            embedded=embedded_items,
            data=taxonomy_to_taxonomy_data(found_taxonomy),
        )

    @API_V1.arguments(TaxonomySchema())
    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def put(self, data, namespace: str, taxonomy: str):
        """Update taxonomy in place."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )
        self._check_if_modifiable(found_taxonomy)

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

        taxonomy_link = taxonomy_to_taxonomy_data(found_taxonomy).self
        taxonomy_data = taxonomy_to_api_response(found_taxonomy)

        return ApiResponse(
            links=[taxonomy_link],
            embedded=[taxonomy_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyView",
                        namespace=namespace,
                        taxonomy=taxonomy,
                        _external=True,
                    ),
                    rel=(
                        "update",
                        "put",
                        "ont-taxonomy",
                    ),
                    resource_type="changed",
                ),
                changed=taxonomy_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def post(self, namespace: str, taxonomy: str):  # restore action
        """Restore a deleted taxonomy."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )
        self._check_if_namespace_modifiable(found_taxonomy.namespace)

        # only actually restore when not already restored
        if found_taxonomy.deleted_on is not None:
            # restore object type
            found_taxonomy.deleted_on = None
            DB.session.add(found_taxonomy)
            DB.session.commit()

        taxonomy_link = taxonomy_to_taxonomy_data(found_taxonomy).self
        taxonomy_data = taxonomy_to_api_response(found_taxonomy)

        return ApiResponse(
            links=[taxonomy_link],
            embedded=[taxonomy_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyView",
                        namespace=namespace,
                        taxonomy=taxonomy,
                        _external=True,
                    ),
                    rel=(
                        "restore",
                        "post",
                        "ont-taxonomy",
                    ),
                    resource_type="changed",
                ),
                changed=taxonomy_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def delete(self, namespace: str, taxonomy: str):
        """Delete a taxonomy."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )
        self._check_if_namespace_modifiable(found_taxonomy.namespace)

        # only actually delete when not already deleted
        if found_taxonomy.deleted_on is None:
            # soft delete namespace
            found_taxonomy.deleted_on = datetime.utcnow()
            DB.session.add(found_taxonomy)
            DB.session.commit()

        taxonomy_link = taxonomy_to_taxonomy_data(found_taxonomy).self
        taxonomy_data = taxonomy_to_api_response(found_taxonomy)

        return ApiResponse(
            links=[taxonomy_link],
            embedded=[taxonomy_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyView",
                        namespace=namespace,
                        taxonomy=taxonomy,
                        _external=True,
                    ),
                    rel=(
                        "delete",
                        "ont-taxonomy",
                    ),
                    resource_type="changed",
                ),
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
    def get(self, namespace: str, taxonomy: str, **kwargs):
        """Get all items of a taxonomy."""
        self._check_path_params(namespace=namespace, taxonomy=taxonomy)
        found_taxonomy: Taxonomy = self._get_lazy_loaded_taxonomy(
            namespace=namespace, taxonomy=taxonomy
        )

        cursor: Optional[str] = kwargs.get("cursor", None)
        item_count: int = cast(int, kwargs.get("item_count", 50))
        sort: str = cast(str, kwargs.get("sort", "-updated_on").lstrip("+"))
        sort_function: Callable[..., Any] = (
            desc if sort is not None and sort.startswith("-") else asc
        )
        sort_key: str = sort.lstrip("+-") if sort is not None else "updated_on"

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

        query: Query = TaxonomyItem.query.filter(*taxonomy_item_filter)

        query = query.order_by(asc(TaxonomyItem.id))

        if sort_key == "updated_on":
            query = query.order_by(sort_function(TaxonomyItem.updated_on))

        if cursor is not None and cursor.isdigit():
            # hope that cursor row has not jumped compared to last query in get_page_info
            query = query.offset(pagination_info.cursor_row)

        query = query.limit(item_count)

        taxonomy_items: List[TaxonomyItem] = query.all()

        embedded_items: List[ApiResponse] = [
            taxonomy_item_to_api_response(item) for item in taxonomy_items
        ]
        items: List[ApiLink] = [item.data.get("self") for item in embedded_items]

        query_params = {
            "item_count": item_count,
            "sort": sort,
        }

        self_query_params = dict(query_params)

        if cursor:
            self_query_params["cursor"] = cursor

        self_rels = []
        if pagination_info.cursor_page == 1:
            self_rels.append("first")
        if (
            pagination_info.last_page
            and pagination_info.cursor_page == pagination_info.last_page.page
        ):
            self_rels.append("last")

        self_link = ApiLink(
            href=url_for(
                "api-v1.TaxonomyItemsView",
                namespace=namespace,
                taxonomy=taxonomy,
                _external=True,
                **self_query_params,
            ),
            rel=(
                *self_rels,
                "page",
                f"page-{pagination_info.cursor_page}",
                "collection",
            ),
            resource_type="ont-taxonomy-item",
            resource_key=taxonomy_item_page_params_to_key(
                namespace, taxonomy, self_query_params
            ),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="TaxonomyItemSchema", _external=True
            ),
        )

        extra_links: List[ApiLink] = [self_link]

        if pagination_info.last_page is not None:
            if pagination_info.cursor_page != pagination_info.last_page.page:
                # only if current page is not last page
                last_query_params = dict(query_params)
                last_query_params["cursor"] = str(pagination_info.last_page.cursor)

                extra_links.append(
                    ApiLink(
                        href=url_for(
                            "api-v1.TaxonomyItemsView",
                            namespace=namespace,
                            taxonomy=taxonomy,
                            _external=True,
                            **last_query_params,
                        ),
                        rel=(
                            "last",
                            "page",
                            f"page-{pagination_info.last_page.page}",
                            "collection",
                        ),
                        resource_type="ont-taxonomy-item",
                        resource_key=taxonomy_item_page_params_to_key(
                            namespace, taxonomy, last_query_params
                        ),
                        schema=url_for(
                            "api-v1.ApiSchemaView",
                            schema_id="TaxonomyItemSchema",
                            _external=True,
                        ),
                    )
                )

        for page in pagination_info.surrounding_pages:
            if page == pagination_info.last_page:
                continue  # link already included
            page_query_params = dict(query_params)
            page_query_params["cursor"] = str(page.cursor)

            extra_rels = []
            if page.page + 1 == pagination_info.cursor_page:
                extra_rels.append("prev")
            if page.page - 1 == pagination_info.cursor_page:
                extra_rels.append("next")

            extra_links.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyItemsView",
                        namespace=namespace,
                        taxonomy=taxonomy,
                        _external=True,
                        **page_query_params,
                    ),
                    rel=(
                        *extra_rels,
                        "page",
                        f"page-{page.page}",
                        "collection",
                    ),
                    resource_type="ont-taxonomy-item",
                    resource_key=taxonomy_item_page_params_to_key(
                        namespace, taxonomy, page_query_params
                    ),
                    schema=url_for(
                        "api-v1.ApiSchemaView",
                        schema_id="TaxonomyItemSchema",
                        _external=True,
                    ),
                )
            )

        extra_links.extend(nav_links_for_taxonomy_item_page(namespace, taxonomy))

        extra_links.extend(action_links_for_taxonomy_item_page(found_taxonomy))

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True, **query_params),
                    rel=("first", "page", "page-1", "collection", "nav"),
                    resource_type="ont-namespace",
                    resource_key=query_params_to_api_key({"item-count": item_count}),
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                ApiLink(
                    href=url_for(  # hardcoded first page link
                        "api-v1.TaxonomyItemsView",
                        namespace=namespace,
                        taxonomy=taxonomy,
                        _external=True,
                        **query_params,
                    ),
                    rel=("first", "page", "page-1", "collection"),
                    resource_type="ont-taxonomy-item",
                    resource_key=taxonomy_item_page_params_to_key(
                        namespace, taxonomy, query_params
                    ),
                    schema=url_for(
                        "api-v1.ApiSchemaView",
                        schema_id="TaxonomyItemSchema",
                        _external=True,
                    ),
                ),
                *extra_links,
            ],
            embedded=embedded_items,
            data=CursorPage(
                self=self_link,
                collection_size=pagination_info.collection_size,
                page=pagination_info.cursor_page,
                first_row=pagination_info.cursor_row + 1,
                items=items,
            ),
        )

    @API_V1.arguments(TaxonomyItemSchema())
    @API_V1.response(DynamicApiResponseSchema(NewApiObjectSchema()))
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

        taxonomy_item_link = taxonomy_item_to_taxonomy_item_data(taxonomy_item).self
        taxonomy_item_data = taxonomy_item_to_api_response(taxonomy_item)

        taxonomy_link = taxonomy_to_taxonomy_data(taxonomy_item.taxonomy).self
        taxonomy_data = taxonomy_to_api_response(taxonomy_item.taxonomy)

        self_link = create_action_link_for_taxonomy_item_page(
            namespace=namespace, taxonomy=taxonomy
        )
        self_link.rel = (*self_link.rel, "ont-taxonomy-item")
        self_link.resource_type = "new"

        return ApiResponse(
            links=[taxonomy_item_link, taxonomy_link],
            embedded=[taxonomy_item_data, taxonomy_data],
            data=NewApiObject(
                self=self_link,
                new=taxonomy_item_link,
            ),
        )

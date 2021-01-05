"""Module containing the namespace API endpoints of the v1 API."""

from datetime import datetime
from muse_for_anything.api.v1_api.ontology_types_helpers import (
    action_links_for_type,
    action_links_for_type_page,
    nav_links_for_type,
    nav_links_for_type_page,
    type_page_params_to_key,
    type_to_api_response,
    type_to_type_data,
)
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
    KeyedApiLink,
    NewApiObject,
    NewApiObjectSchema,
)
from .models.ontology import NamespaceSchema, ObjectTypeSchema
from ...db.db import DB
from ...db.pagination import get_page_info
from ...db.models.namespace import Namespace
from ...db.models.ontology_objects import OntologyObjectType, OntologyObjectTypeVersion

from .namespace_helpers import (
    query_params_to_api_key,
)


@API_V1.route("/namespaces/<string:namespace>/types/")
class TypesView(MethodView):
    """Endpoint for all namespace types."""

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    def get(self, namespace: str, **kwargs: Any):
        """Get the page of types."""
        if namespace is None or not namespace.isdigit():
            abort(400, f"Illegal namespace identifier {namespace}!")

        cursor: Optional[str] = kwargs.get("cursor", None)
        item_count: int = cast(int, kwargs.get("item_count", 50))
        sort: str = cast(str, kwargs.get("sort", "name").lstrip("+"))
        sort_function: Callable[..., Any] = (
            desc if sort is not None and sort.startswith("-") else asc
        )
        sort_key: str = sort.lstrip("+-") if sort is not None else "name"

        ontology_type_filter = (
            OntologyObjectType.deleted_on == None,
            OntologyObjectType.namespace_id == int(namespace),
        )

        pagination_info = get_page_info(
            OntologyObjectType,
            OntologyObjectType.id,
            [OntologyObjectType.name],
            cursor,
            sort,
            item_count,
            filter_criteria=ontology_type_filter,
        )

        query: Query = OntologyObjectType.query.filter(*ontology_type_filter)

        query = query.order_by(asc(OntologyObjectType.id))

        if sort_key == "name":
            query = query.order_by(
                sort_function(OntologyObjectType.name.collate("NOCASE"))
            )

        if cursor is not None and cursor.isdigit():
            # hope that cursor row has not jumped compared to last query in get_page_info
            query = query.offset(pagination_info.cursor_row)

        query = query.limit(item_count)

        object_types: List[OntologyObjectType] = query.all()

        embedded_items: List[ApiResponse] = [
            type_to_api_response(object_type) for object_type in object_types
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
                "api-v1.TypesView",
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
            resource_type="ont-type",
            resource_key=type_page_params_to_key(namespace, self_query_params),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
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
                            "api-v1.NamespacesView",
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
                        resource_type="ont-type",
                        resource_key=type_page_params_to_key(
                            namespace, last_query_params
                        ),
                        schema=url_for(
                            "api-v1.ApiSchemaView",
                            schema_id="OntologyType",
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
                        "api-v1.NamespacesView",
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
                    resource_type="ont-type",
                    resource_key=type_page_params_to_key(namespace, page_query_params),
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
                    ),
                )
            )

        extra_links.extend(nav_links_for_type_page(namespace))

        extra_links.extend(action_links_for_type_page(namespace))

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
                        "api-v1.TypesView",
                        namespace=namespace,
                        _external=True,
                        **query_params,
                    ),
                    rel=("first", "page", "page-1", "collection"),
                    resource_type="ont-type",
                    resource_key=type_page_params_to_key(namespace, query_params),
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
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

    @API_V1.arguments(NamespaceSchema(only=("name", "description")))
    @API_V1.response(DynamicApiResponseSchema(NewApiObjectSchema()))
    def post(self, namespace_data):
        abort(
            500,
            f"Not Implemented yet",
        )


@API_V1.route("/namespaces/<string:namespace>/types/<string:object_type>/")
class TypeView(MethodView):
    """Endpoint a single object type resource."""

    @API_V1.response(DynamicApiResponseSchema(ObjectTypeSchema()))
    def get(self, namespace: str, object_type: str, **kwargs: Any):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not object_type or not object_type.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested type id has the wrong format!"),
            )
        namespace_id = int(namespace)
        object_type_id = int(object_type)
        found_object_type: Optional[OntologyObjectType] = OntologyObjectType.query.filter(
            OntologyObjectType.id == object_type_id,
            OntologyObjectType.namespace_id == namespace_id,
        ).first()

        if found_object_type is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Object Type not found."))

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for(
                        "api-v1.NamespacesView",
                        _external=True,
                        item_count=50,
                        sort="name",
                    ),
                    rel=("first", "page", "collection", "ont-namespace"),
                    resource_type="ont-namespace",
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                *nav_links_for_type(found_object_type),
                *action_links_for_type(found_object_type),
            ],
            data=type_to_type_data(found_object_type),
        )

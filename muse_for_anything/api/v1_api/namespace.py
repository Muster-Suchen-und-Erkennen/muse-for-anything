"""Module containing the namespace API endpoints of the v1 API."""

from datetime import datetime
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
    ApiResponseSchema,
    DynamicApiResponseSchema,
    KeyedApiLink,
    NewApiObject,
    NewApiObjectSchema,
)
from .models.ontology import NamespaceData, NamespaceSchema
from ...db.db import DB
from ...db.pagination import get_page_info
from ...db.models.namespace import Namespace


def namespace_to_key(namespace: Namespace) -> Dict[str, str]:
    return {"namespaceId": str(namespace.id)}


def namespace_to_namespace_data(namespace: Namespace) -> NamespaceData:
    return NamespaceData(
        self=ApiLink(
            href=url_for(
                "api-v1.NamespaceView", namespace=str(namespace.id), _external=True
            ),
            rel=("ont-namespace",),
            resource_type="ont-namespace",
            resource_key=namespace_to_key(namespace),
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
        ),
        name=namespace.name,
        description=namespace.description,
        created_on=namespace.created_on,
        updated_on=namespace.updated_on,
        deleted_on=namespace.deleted_on,
    )


def action_links_for_namespace(namespace: Namespace) -> List[ApiLink]:
    actions: List[ApiLink] = [
        ApiLink(
            href=url_for("api-v1.NamespacesView", _external=True),
            rel=("create", "post", "ont-namespace"),
            resource_type="ont-namespace",
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
        ),
    ]

    resource_key = namespace_to_key(namespace)

    if namespace.deleted_on is None:
        actions.append(
            ApiLink(
                href=url_for(
                    "api-v1.NamespaceView",
                    namespace=str(namespace.id),
                    _external=True,
                ),
                rel=("update", "put", "ont-namespace"),
                resource_type="ont-namespace",
                resource_key=resource_key,
                schema=url_for(
                    "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                ),
            )
        )
        actions.append(
            ApiLink(
                href=url_for(
                    "api-v1.NamespaceView",
                    namespace=str(namespace.id),
                    _external=True,
                ),
                rel=("delete", "ont-namespace"),
                resource_type="ont-namespace",
                resource_key=resource_key,
            )
        )
    else:
        actions.append(
            ApiLink(
                href=url_for(
                    "api-v1.NamespaceView",
                    namespace=str(namespace.id),
                    _external=True,
                ),
                rel=("restore", "post", "ont-namespace"),
                resource_type="ont-namespace",
                resource_key=resource_key,
            )
        )
    return actions


def namespace_to_api_response(namespace: Namespace) -> ApiResponse:
    namespace_data = namespace_to_namespace_data(namespace)
    raw_namespace: Dict[str, Any] = NamespaceSchema().dump(namespace_data)
    return ApiResponse(
        links=(
            ApiLink(
                href=url_for("api-v1.NamespacesView", _external=True),
                rel=("first", "page", "up", "collection", "ont-namespace"),
                resource_type="ont-namespace",
                schema=url_for(
                    "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                ),
            ),
            *action_links_for_namespace(namespace),
        ),
        data=raw_namespace,
    )


def query_params_to_api_key(query_params: Dict[str, Union[str, int]]) -> Dict[str, str]:
    key = {}
    for k, v in query_params.items():
        key[k.replace("_", "-")] = str(v)
    return key


@API_V1.route("/namespaces/")
class NamespacesView(MethodView):
    """Endpoint for all namespaces collection resource."""

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    def get(self, **kwargs: Any):
        """Get the page of namespaces."""
        cursor: Optional[str] = kwargs.get("cursor", None)
        item_count: int = cast(int, kwargs.get("item_count", 50))
        sort: str = cast(str, kwargs.get("sort", "name").lstrip("+"))
        sort_function: Callable[..., Any] = (
            desc if sort is not None and sort.startswith("-") else asc
        )
        sort_key: str = sort.lstrip("+-") if sort is not None else "name"

        namespace_filter = (Namespace.deleted_on == None,)

        pagination_info = get_page_info(
            Namespace,
            Namespace.id,
            [Namespace.name],
            cursor,
            sort,
            item_count,
            filter_criteria=namespace_filter,
        )

        query: Query = Namespace.query.filter(*namespace_filter)

        if sort_key == "name":
            query = query.order_by(sort_function(Namespace.name.collate("NOCASE")))

        if cursor is not None and cursor.isdigit():
            # hope that cursor row has not jumped compared to last query in get_page_info
            query = query.offset(pagination_info.cursor_row)

        query = query.limit(item_count)

        namespaces: List[Namespace] = query.all()

        embedded_items: List[ApiResponse] = [
            namespace_to_api_response(namespace) for namespace in namespaces
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
            href=url_for("api-v1.NamespacesView", _external=True, **self_query_params),
            rel=(
                *self_rels,
                "page",
                f"page-{pagination_info.cursor_page}",
                "collection",
                "ont-namespace",
            ),
            resource_type="ont-namespace",
            resource_key=query_params_to_api_key(self_query_params),
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
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
                            "api-v1.NamespacesView", _external=True, **last_query_params
                        ),
                        rel=(
                            "last",
                            "page",
                            f"page-{pagination_info.last_page.page}",
                            "collection",
                            "ont-namespace",
                        ),
                        resource_type="ont-namespace",
                        resource_key=query_params_to_api_key(last_query_params),
                        schema=url_for(
                            "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
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
                        "api-v1.NamespacesView", _external=True, **page_query_params
                    ),
                    rel=(
                        *extra_rels,
                        "page",
                        f"page-{page.page}",
                        "collection",
                        "ont-namespace",
                    ),
                    resource_type="ont-namespace",
                    resource_key=query_params_to_api_key(page_query_params),
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                )
            )

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True, **query_params),
                    rel=("first", "page", "page-1", "collection", "ont-namespace"),
                    resource_type="ont-namespace",
                    resource_key=query_params_to_api_key(query_params),
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True),
                    rel=("create", "post", "ont-namespace"),
                    resource_type="ont-namespace",
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                *extra_links,
            ],
            embedded=embedded_items,
            keyed_links=[
                KeyedApiLink(
                    href=template_url_for(
                        "api-v1.NamespaceView",
                        {"namespace": "namespaceId"},
                        _external=True,
                    ),
                    rel=("ont-namespace",),
                    resource_type="ont-namespace",
                    key=("namespaceId",),
                ),
                KeyedApiLink(
                    href=template_url_for(
                        "api-v1.NamespacesView",
                        {"item_count": "item_count", "sort": "sort", "cursor": "cursor"},
                        _external=True,
                    ),
                    rel=("collection", "ont-namespace"),
                    resource_type="ont-namespace",
                    key=("item_count", "cursor", "sort"),
                ),
            ],
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
        existing: bool = (
            DB.session.query(literal(True))
            .filter(
                Namespace.query.filter(Namespace.name == namespace_data["name"]).exists()
            )
            .scalar()
        )
        if existing:
            abort(
                400,
                f"Name {namespace_data['name']} is already used for another Namespace!",
            )
        namespace = Namespace(**namespace_data)
        DB.session.add(namespace)
        DB.session.commit()

        namespace_link = namespace_to_namespace_data(namespace).self
        namespace_data = namespace_to_api_response(namespace)

        return ApiResponse(
            links=[namespace_link],
            embedded=[namespace_data],
            data=NewApiObject(
                self=ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True),
                    rel=(
                        "new",
                        "create",
                        "post",
                        "ont-namespace",
                    ),
                    resource_type="new",
                ),
                new=namespace_link,
            ),
        )


@API_V1.route("/namespaces/<string:namespace>/")
class NamespaceView(MethodView):
    """Endpoint a single namespace resource."""

    @API_V1.response(DynamicApiResponseSchema(NamespaceSchema()))
    def get(self, namespace: str, **kwargs: Any):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        namespace_id = int(namespace)
        found_namespace: Optional[Namespace] = Namespace.query.filter(
            Namespace.id == namespace_id
        ).first()

        if found_namespace is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Namespace not found."))

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for(
                        "api-v1.NamespacesView",
                        _external=True,
                        item_count=50,
                        sort="name",
                    ),
                    rel=("first", "page", "up", "collection", "ont-namespace"),
                    resource_type="ont-namespace",
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                *action_links_for_namespace(found_namespace),
            ],
            data=namespace_to_namespace_data(found_namespace),
        )

    @API_V1.arguments(NamespaceSchema(only=("name", "description")))
    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def put(self, namespace_data, namespace: str):  # restore action
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        namespace_id = int(namespace)
        found_namespace: Optional[Namespace] = Namespace.query.filter(
            Namespace.id == namespace_id
        ).first()

        if found_namespace is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Namespace not found."))

        if found_namespace.name != namespace_data.get("name"):
            existing: bool = (
                DB.session.query(literal(True))
                .filter(
                    Namespace.query.filter(
                        Namespace.name == namespace_data["name"]
                    ).exists()
                )
                .scalar()
            )
            if existing:
                abort(
                    400,
                    f"Name {namespace_data['name']} is already used for another Namespace!",
                )

        found_namespace.update(**namespace_data)
        DB.session.add(found_namespace)
        DB.session.commit()

        namespace_link = namespace_to_namespace_data(found_namespace).self
        namespace_rsponse_data = namespace_to_api_response(found_namespace)

        return ApiResponse(
            links=[namespace_link],
            embedded=[namespace_rsponse_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True),
                    rel=(
                        "changed",
                        "create",
                        "post",
                        "ont-namespace",
                    ),
                    resource_type="changed",
                ),
                changed=namespace_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def post(self, namespace: str):  # restore action
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        namespace_id = int(namespace)
        found_namespace: Optional[Namespace] = Namespace.query.filter(
            Namespace.id == namespace_id
        ).first()

        if found_namespace is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Namespace not found."))

        # only actually restore when not already restored
        if found_namespace.deleted_on is not None:
            # restore namespace
            found_namespace.deleted_on = None
            DB.session.add(found_namespace)
            DB.session.commit()

        namespace_link = namespace_to_namespace_data(found_namespace).self
        namespace_data = namespace_to_api_response(found_namespace)

        return ApiResponse(
            links=[namespace_link],
            embedded=[namespace_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True),
                    rel=(
                        "changed",
                        "create",
                        "post",
                        "ont-namespace",
                    ),
                    resource_type="changed",
                ),
                changed=namespace_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def delete(self, namespace: str):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        namespace_id = int(namespace)
        found_namespace: Optional[Namespace] = Namespace.query.filter(
            Namespace.id == namespace_id
        ).first()

        if found_namespace is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Namespace not found."))

        # only actually delete when not already deleted
        if found_namespace.deleted_on is None:
            # soft delete namespace
            found_namespace.deleted_on = datetime.now()
            DB.session.add(found_namespace)
            DB.session.commit()

        namespace_link = namespace_to_namespace_data(found_namespace).self
        namespace_data = namespace_to_api_response(found_namespace)

        return ApiResponse(
            links=[namespace_link],
            embedded=[namespace_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True),
                    rel=(
                        "changed",
                        "create",
                        "post",
                        "ont-namespace",
                    ),
                    resource_type="changed",
                ),
                changed=namespace_link,
            ),
        )

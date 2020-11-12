"""Module containing the namespace API endpoints of the v1 API."""

from muse_for_anything.api.util import template_url_for
from typing import Any, Callable, Dict, List, Optional
from flask.helpers import url_for
from flask.views import MethodView
from dataclasses import dataclass
from sqlalchemy.sql.expression import asc, desc
from sqlalchemy.orm.query import Query

from .root import API_V1
from ..base_models import (
    ApiLink,
    ApiResponse,
    CursorPage,
    CursorPageArgumentsSchema,
    CursorPageSchema,
    DynamicApiResponseSchema,
    KeyedApiLink,
)
from .models.ontology import NamespaceSchema
from ...db.db import DB
from ...db.models.namespace import Namespace


def namespace_to_api_response(namespace: Namespace) -> ApiResponse:
    raw_namespace: Dict[str, Any] = NamespaceSchema().dump(namespace)
    raw_namespace["self"] = ApiLink(
        href=url_for("api-v1.NamespaceView", namespace=str(namespace.id), _external=True),
        rel=("namespace",),
        resource_type="ont-namespace",
    )
    return ApiResponse(
        links=(
            ApiLink(
                href=url_for("api-v1.NamespacesView", _external=True),
                rel=("first", "collection", "namespace"),
                resource_type="ont-namespace",
            ),
        ),
        data=raw_namespace,
        key={"namespaceId": namespace.id},
    )


@API_V1.route("/namespaces/")
class NamespacesView(MethodView):
    """Endpoint for all namespaces collection resource."""

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    def get(self, **kwargs: Any):
        """Get the page of namespaces."""
        cursor: Optional[str] = kwargs.get("cursor", None)
        item_count: int = kwargs.get("item_count", 50)
        sort: str = kwargs.get("sort", "name").lstrip("+")
        sort_function: Callable[..., Any] = (
            desc if sort is not None and sort.startswith("-") else asc
        )
        sort_key: str = sort.lstrip("+-") if sort is not None else "name"

        collection_size: int = Namespace.query.enable_eagerloads(False).count()

        query: Query = Namespace.query
        query.limit(item_count + 1)

        if sort_key == "name":
            query.order_by(sort_function(Namespace.name))

        if cursor is not None:
            query.filter(Namespace.name > cursor)

        _namespaces: List[Namespace] = query.all()
        next_cursor = _namespaces[item_count : item_count + 1]
        namespaces = _namespaces[:item_count]
        embedded_items: List[ApiResponse] = [
            namespace_to_api_response(namespace) for namespace in namespaces
        ]
        items: List[ApiLink] = [item.data.get("self") for item in embedded_items]

        query_params = {
            "item_count": item_count,
            "sort": sort,
        }

        if namespaces:
            query_params["cursor"] = str(namespaces[0].id)

        self = ApiLink(
            href=url_for("api-v1.NamespacesView", _external=True, **query_params),
            rel=("first", "collection", "namespace"),
            resource_type="ont-namespace",
        )

        last: ApiLink  # TODO find out how to get more than a next cursor...

        extra_links: List[ApiLink] = []

        if not next_cursor:
            extra_links.append(
                ApiLink(
                    href=self.href,
                    rel=("last", "collection", "namespace"),
                    resource_type="ont-namespace",
                )
            )
        else:
            params = {key: val for key, val in query_params.items()}
            params["cursor"] = str(next_cursor[0].id)
            extra_links.append(
                ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True, **params),
                    rel=("next", "collection", "namespace"),
                    resource_type="ont-namespace",
                )
            )

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for(
                        "api-v1.NamespacesView",
                        _external=True,
                        item_count=item_count,
                        sort=sort,
                    ),
                    rel=("first", "collection", "ont-namespace"),
                    resource_type="ont-namespace",
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
            key=query_params,
            data=CursorPage(
                self=self,
                collection_size=collection_size,
                items=items,
            ),
        )


@API_V1.route("/namespaces/<string:namespace>/")
class NamespaceView(MethodView):
    """Endpoint a single namespace resource."""

    @API_V1.response(DynamicApiResponseSchema(NamespaceSchema()))
    def get(self, namespace, **kwargs: Any):
        pass

"""Module containing the namespace API endpoints of the v1 API."""

from datetime import datetime

from muse_for_anything.db.models.users import User
from flask.globals import g
from flask_babel import gettext
from typing import Any, Callable, Dict, List, Optional, Union, cast
from flask.helpers import url_for
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
from .models.ontology import NamespaceSchema
from ...db.db import DB
from ...db.pagination import get_page_info
from ...db.models.namespace import Namespace

from ...oso_helpers import FLASK_OSO, OsoResource

from .request_helpers import ApiResponseGenerator, LinkGenerator, PageResource
from .namespace_helpers import NAMESPACE_EXTRA_LINK_RELATIONS


@API_V1.route("/namespaces/")
class NamespacesView(MethodView):
    """Endpoint for all namespaces collection resource."""

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt", optional=True)
    def get(self, **kwargs: Any):
        """Get the page of namespaces."""
        FLASK_OSO.authorize_and_set_resource(
            OsoResource("ont-namespace", is_collection=True)
        )

        cursor: Optional[str] = kwargs.get("cursor", None)
        item_count: int = cast(int, kwargs.get("item_count", 25))
        sort: str = cast(str, kwargs.get("sort", "name").lstrip("+"))

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

        namespaces: List[Namespace] = pagination_info.page_items_query.all()

        embedded_items: List[ApiResponse] = []
        items: List[ApiLink] = []

        dump = NamespaceSchema().dump
        for namespace in namespaces:
            response = ApiResponseGenerator.get_api_response(
                namespace, linkt_to_relations=NAMESPACE_EXTRA_LINK_RELATIONS
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

        self_rels = []
        if pagination_info.cursor_page == 1:
            self_rels.append("first")
        if (
            pagination_info.last_page
            and pagination_info.cursor_page == pagination_info.last_page.page
        ):
            self_rels.append("last")

        page_resource = PageResource(
            Namespace,
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
        )

    @API_V1.arguments(NamespaceSchema(only=("name", "description")))
    @API_V1.response(DynamicApiResponseSchema(NewApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def post(self, namespace_data):
        FLASK_OSO.authorize_and_set_resource(
            OsoResource("ont-namespace"), action="CREATE"
        )

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
        DB.session.flush()
        user: User = g.current_user
        user.set_role_for_resource("owner", namespace)
        DB.session.commit()

        namespace_response = ApiResponseGenerator.get_api_response(
            namespace, linkt_to_relations=NAMESPACE_EXTRA_LINK_RELATIONS
        )
        namespace_link = namespace_response.data.self
        namespace_response.data = NamespaceSchema().dump(namespace_response.data)

        return ApiResponse(
            links=[namespace_link],
            embedded=[namespace_response],
            data=NewApiObject(
                self=ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True),
                    rel=(
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
    @API_V1.require_jwt("jwt", optional=True)
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

        FLASK_OSO.set_current_resource(found_namespace)
        FLASK_OSO.authorize()

        return ApiResponseGenerator.get_api_response(
            found_namespace, linkt_to_relations=NAMESPACE_EXTRA_LINK_RELATIONS
        )

    @API_V1.arguments(NamespaceSchema(only=("name", "description")))
    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def put(self, namespace_data, namespace: str):
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
        if found_namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )

        FLASK_OSO.authorize_and_set_resource(found_namespace, action="EDIT")

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

        namespace_response = ApiResponseGenerator.get_api_response(
            found_namespace, linkt_to_relations=NAMESPACE_EXTRA_LINK_RELATIONS
        )
        namespace_link = namespace_response.data.self
        namespace_response.data = NamespaceSchema().dump(namespace_response.data)

        return ApiResponse(
            links=[namespace_link],
            embedded=[namespace_response],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True),
                    rel=(
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
    @API_V1.require_jwt("jwt")
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

        FLASK_OSO.authorize_and_set_resource(found_namespace, action="RESTORE")

        # only actually restore when not already restored
        if found_namespace.deleted_on is not None:
            # restore namespace
            found_namespace.deleted_on = None
            DB.session.add(found_namespace)
            DB.session.commit()

        namespace_response = ApiResponseGenerator.get_api_response(
            found_namespace, linkt_to_relations=NAMESPACE_EXTRA_LINK_RELATIONS
        )
        namespace_link = namespace_response.data.self
        namespace_response.data = NamespaceSchema().dump(namespace_response.data)

        return ApiResponse(
            links=[namespace_link],
            embedded=[namespace_response],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.NamespaceView", namespace=namespace, _external=True
                    ),
                    rel=(
                        "restore",
                        "post",
                        "ont-namespace",
                    ),
                    resource_type="changed",
                ),
                changed=namespace_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
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

        FLASK_OSO.authorize_and_set_resource(found_namespace)

        # only actually delete when not already deleted
        if found_namespace.deleted_on is None:
            # soft delete namespace
            found_namespace.deleted_on = datetime.utcnow()
            DB.session.add(found_namespace)
            DB.session.commit()

        namespace_response = ApiResponseGenerator.get_api_response(
            found_namespace, linkt_to_relations=NAMESPACE_EXTRA_LINK_RELATIONS
        )
        namespace_link = namespace_response.data.self
        namespace_response.data = NamespaceSchema().dump(namespace_response.data)

        return ApiResponse(
            links=[namespace_link],
            embedded=[namespace_response],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.NamespaceView", namespace=namespace, _external=True
                    ),
                    rel=(
                        "delete",
                        "ont-namespace",
                    ),
                    resource_type="changed",
                ),
                changed=namespace_link,
            ),
        )

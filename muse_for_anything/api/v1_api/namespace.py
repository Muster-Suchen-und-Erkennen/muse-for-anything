"""Module containing the namespace API endpoints of the v1 API."""

from datetime import datetime
from http import HTTPStatus
from typing import Any, List, Optional

from flask.globals import g
from flask.views import MethodView
from flask_babel import gettext
from flask_smorest import abort
from sqlalchemy.sql.expression import literal

from muse_for_anything.api.pagination_util import (
    PaginationOptions,
    default_get_page_info,
    dump_embedded_page_items,
    generate_page_links,
    prepare_pagination_query_args,
)
from muse_for_anything.db.models.users import User

from .constants import (
    CHANGED_REL,
    CREATE,
    CREATE_REL,
    DELETE_REL,
    NAMESPACE_EXTRA_LINK_RELATIONS,
    NAMESPACE_REL_TYPE,
    NEW_REL,
    RESTORE,
    RESTORE_REL,
    UPDATE,
    UPDATE_REL,
)
from .models.ontology import NamespaceSchema
from .request_helpers import ApiResponseGenerator, LinkGenerator, PageResource
from .root import API_V1
from ..base_models import (
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
from ...db.models.namespace import Namespace
from ...oso_helpers import FLASK_OSO, OsoResource

# import namespace specific generators to load them
from .generators import namespace  # noqa


@API_V1.route("/namespaces/")
class NamespacesView(MethodView):
    """Endpoint for all namespaces collection resource."""

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(200, DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt", optional=True)
    def get(self, **kwargs: Any):
        """Get the page of namespaces."""
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(NAMESPACE_REL_TYPE, is_collection=True)
        )

        pagination_options: PaginationOptions = prepare_pagination_query_args(
            **kwargs, _sort_default="name"
        )

        namespace_filter = (Namespace.deleted_on == None,)

        pagination_info = default_get_page_info(
            Namespace, namespace_filter, pagination_options, [Namespace.name]
        )

        namespaces: List[Namespace] = pagination_info.page_items_query.all()

        embedded_items, items = dump_embedded_page_items(
            namespaces, NamespaceSchema(), NAMESPACE_EXTRA_LINK_RELATIONS
        )

        page_resource = PageResource(
            Namespace,
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
        )

    @API_V1.arguments(NamespaceSchema(only=("name", "description")))
    @API_V1.response(200, DynamicApiResponseSchema(NewApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def post(self, namespace_data):
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(NAMESPACE_REL_TYPE), action=CREATE
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
            namespace, link_to_relations=NAMESPACE_EXTRA_LINK_RELATIONS
        )
        namespace_link = namespace_response.data.self
        namespace_response.data = NamespaceSchema().dump(namespace_response.data)

        self_link = LinkGenerator.get_link_of(
            PageResource(Namespace),
            for_relation=CREATE_REL,
            extra_relations=(NAMESPACE_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = NEW_REL

        return ApiResponse(
            links=[namespace_link],
            embedded=[namespace_response],
            data=NewApiObject(
                self=self_link,
                new=namespace_link,
            ),
        )


@API_V1.route("/namespaces/<string:namespace>/")
class NamespaceView(MethodView):
    """Endpoint a single namespace resource."""

    @API_V1.response(200, DynamicApiResponseSchema(NamespaceSchema()))
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
            found_namespace, link_to_relations=NAMESPACE_EXTRA_LINK_RELATIONS
        )

    @API_V1.arguments(NamespaceSchema(only=("name", "description")))
    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
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

        FLASK_OSO.authorize_and_set_resource(found_namespace, action=UPDATE)

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
            found_namespace, link_to_relations=NAMESPACE_EXTRA_LINK_RELATIONS
        )
        namespace_link = namespace_response.data.self
        namespace_response.data = NamespaceSchema().dump(namespace_response.data)

        self_link = LinkGenerator.get_link_of(
            found_namespace,
            for_relation=UPDATE_REL,
            extra_relations=(NAMESPACE_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[namespace_link],
            embedded=[namespace_response],
            data=ChangedApiObject(
                self=self_link,
                changed=namespace_link,
            ),
        )

    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
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

        FLASK_OSO.authorize_and_set_resource(found_namespace, action=RESTORE)

        # only actually restore when not already restored
        if found_namespace.deleted_on is not None:
            # restore namespace
            found_namespace.deleted_on = None
            DB.session.add(found_namespace)
            DB.session.commit()

        namespace_response = ApiResponseGenerator.get_api_response(
            found_namespace, link_to_relations=NAMESPACE_EXTRA_LINK_RELATIONS
        )
        namespace_link = namespace_response.data.self
        namespace_response.data = NamespaceSchema().dump(namespace_response.data)

        self_link = LinkGenerator.get_link_of(
            found_namespace,
            for_relation=RESTORE_REL,
            extra_relations=(NAMESPACE_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[namespace_link],
            embedded=[namespace_response],
            data=ChangedApiObject(
                self=self_link,
                changed=namespace_link,
            ),
        )

    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
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
            found_namespace, link_to_relations=NAMESPACE_EXTRA_LINK_RELATIONS
        )
        namespace_link = namespace_response.data.self
        namespace_response.data = NamespaceSchema().dump(namespace_response.data)

        self_link = LinkGenerator.get_link_of(
            found_namespace,
            for_relation=DELETE_REL,
            extra_relations=(NAMESPACE_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[namespace_link],
            embedded=[namespace_response],
            data=ChangedApiObject(
                self=self_link,
                changed=namespace_link,
            ),
        )

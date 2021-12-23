"""Module containing the user management endpoints of the api."""

from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Dict, List, Optional

from flask.globals import g
from flask.helpers import url_for
from flask.views import MethodView
from flask_babel import gettext
from flask_jwt_extended import create_access_token, create_refresh_token, current_user
from flask_smorest import abort
from sqlalchemy.sql.expression import true

from muse_for_anything.api.pagination_util import (
    PaginationOptions,
    default_get_page_info,
    dump_embedded_page_items,
    generate_page_links,
    prepare_pagination_query_args,
)
from muse_for_anything.api.v1_api.constants import NAMESPACE_REL_TYPE, USER_REL_TYPE
from muse_for_anything.db.models.users import User
from muse_for_anything.db.pagination import PaginationInfo
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource

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
    USER_EXTRA_LINK_RELATIONS,
    VIEW_ALL_USERS_EXTRA_ARG,
)
from .models.auth import (
    AccessTokenSchema,
    LoginPostSchema,
    LoginTokensSchema,
    UserCreateSchema,
    UserSchema,
)
from .request_helpers import ApiResponseGenerator, LinkGenerator, PageResource
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

# import namespace specific generators to load them
from .generators import user_management  # noqa


@API_V1.route("/auth/users/")
class UsersView(MethodView):
    """Endpoint for the users collection resource."""

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, **kwargs: Any):
        """Get the page of users."""
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(USER_REL_TYPE, is_collection=True)
        )

        can_view_all_users = FLASK_OSO.is_allowed(
            OsoResource(
                USER_REL_TYPE,
                is_collection=True,
                arguments={VIEW_ALL_USERS_EXTRA_ARG: True},
            )
        )

        pagination_options: PaginationOptions = prepare_pagination_query_args(
            **kwargs, _sort_default="username"
        )

        users: List[User]

        if can_view_all_users:
            pagination_info = default_get_page_info(
                User, tuple(), pagination_options, [User.username]
            )

            users = pagination_info.page_items_query.all()
        else:
            users = [g.current_user]
            pagination_info = PaginationInfo(
                collection_size=1,
                cursor_row=0,
                cursor_page=1,
                surrounding_pages=[],
                last_page=None,
                page_items_query=None,
            )

        embedded_items, items = dump_embedded_page_items(
            users, UserSchema(), USER_EXTRA_LINK_RELATIONS
        )

        page_resource = PageResource(
            User,
            page_number=pagination_info.cursor_page,
            active_page=pagination_info.cursor_page,
            last_page=pagination_info.last_page.page
            if pagination_info.last_page
            else None,
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

    @API_V1.arguments(UserCreateSchema())
    @API_V1.response(DynamicApiResponseSchema(NewApiObjectSchema()))
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


@API_V1.route("/auth/users/<string:username>/")
class UserView(MethodView):
    """Endpoint for a single user resource."""

    @API_V1.response(DynamicApiResponseSchema(UserSchema()))
    @API_V1.require_jwt("jwt", optional=True)
    def get(self, username: str, **kwargs: Any):
        if not username:
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested username has the wrong format!"),
            )

        FLASK_OSO.authorize(OsoResource(USER_REL_TYPE, arguments={"username": username}))

        found_user: Optional[User] = User.query.filter(User.username == username).first()

        if found_user is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("User not found."))

        FLASK_OSO.authorize_and_set_resource(found_user)

        return ApiResponseGenerator.get_api_response(
            found_user, link_to_relations=USER_EXTRA_LINK_RELATIONS
        )

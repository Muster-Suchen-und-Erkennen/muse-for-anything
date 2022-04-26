"""Module containing the user management endpoints of the api."""

from http import HTTPStatus
from typing import Any, Dict, List, Optional

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
from muse_for_anything.db.pagination import PaginationInfo
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource

from .constants import (
    CHANGED_REL,
    CREATE,
    CREATE_REL,
    DELETE_REL,
    DELETED_REL,
    EDIT,
    LOGOUT_REL,
    NEW_REL,
    UPDATE,
    UPDATE_REL,
    USER_EXTRA_LINK_RELATIONS,
    USER_REL_TYPE,
    VIEW_ALL_USERS_EXTRA_ARG,
)
from .models.auth import UserCreateSchema, UserSchema, UserUpdateSchema
from .request_helpers import ApiResponseGenerator, LinkGenerator, PageResource
from .root import API_V1
from ..base_models import (
    ApiLink,
    ApiResponse,
    ChangedApiObject,
    ChangedApiObjectSchema,
    CursorPageArgumentsSchema,
    CursorPageSchema,
    DeletedApiObject,
    DeletedApiObjectSchema,
    DynamicApiResponseSchema,
    NewApiObject,
    NewApiObjectSchema,
)
from ...db.db import DB

# import user management specific generators to load them
from .generators import user_management  # noqa


@API_V1.route("/auth/users/")
class UsersView(MethodView):
    """Endpoint for the users collection resource."""

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(200, DynamicApiResponseSchema(CursorPageSchema()))
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
    @API_V1.response(200, DynamicApiResponseSchema(NewApiObjectSchema()))
    @API_V1.require_jwt("jwt", fresh=True)
    def post(self, user_data):
        FLASK_OSO.authorize_and_set_resource(OsoResource(USER_REL_TYPE), action=CREATE)

        email_in_use: bool = (
            DB.session.query(literal(True))
            .filter(User.query.filter(User.username == user_data["username"]).exists())
            .scalar()
        )
        if email_in_use:
            abort(
                HTTPStatus.BAD_REQUEST,
                f"Username {user_data['username']} is already used for another User!",
            )

        if user_data.get("e_mail"):
            email_in_use: bool = (
                DB.session.query(literal(True))
                .filter(User.query.filter(User.e_mail == user_data["e_mail"]).exists())
                .scalar()
            )
            if email_in_use:
                abort(
                    HTTPStatus.BAD_REQUEST,
                    f"E-Mail {user_data['e_mail']} is already used for another User!",
                )

        retype_password = user_data.pop("retype_password", None)
        password = user_data["password"]
        if len(password) < 4:
            abort(HTTPStatus.BAD_REQUEST, "Passwords must have at least 4 characters!")
        if password != retype_password:
            abort(HTTPStatus.BAD_REQUEST, "Passwords did not match, please retry.")

        user = User(**user_data)
        DB.session.add(user)
        DB.session.flush()
        DB.session.commit()

        user_response = ApiResponseGenerator.get_api_response(
            user, link_to_relations=USER_EXTRA_LINK_RELATIONS
        )
        user_link = user_response.data.self
        user_response.data = UserSchema().dump(user_response.data)

        self_link = LinkGenerator.get_link_of(
            PageResource(User),
            for_relation=CREATE_REL,
            extra_relations=(USER_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = NEW_REL

        return ApiResponse(
            links=[user_link],
            embedded=[user_response],
            data=NewApiObject(
                self=self_link,
                new=user_link,
            ),
        )


@API_V1.route("/auth/users/<string:username>/")
class UserView(MethodView):
    """Endpoint for a single user resource."""

    @API_V1.response(200, DynamicApiResponseSchema(UserSchema()))
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

    @API_V1.arguments(UserUpdateSchema())
    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt", fresh=True)
    def post(self, user_data, username: str):
        if not username:
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested username has the wrong format!"),
            )

        FLASK_OSO.authorize(
            OsoResource(USER_REL_TYPE, arguments={"username": username}), action=EDIT
        )

        found_user: Optional[User] = User.query.filter(User.username == username).first()

        if found_user is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("User not found."))

        FLASK_OSO.authorize_and_set_resource(found_user, action=EDIT)

        if found_user.username != user_data.get("username"):
            existing: bool = (
                DB.session.query(literal(True))
                .filter(
                    User.query.filter(User.username == user_data["username"]).exists()
                )
                .scalar()
            )
            if existing:
                abort(
                    400,
                    f"Username {user_data['name']} is already taken!",
                )

        if (
            found_user.e_mail != user_data.get("e_mail")
            and user_data.get("e_mail", None) is not None
        ):
            existing: bool = (
                DB.session.query(literal(True))
                .filter(User.query.filter(User.e_mail == user_data["e_mail"]).exists())
                .scalar()
            )
            if existing:
                abort(
                    400,
                    f"E-Mail {user_data['name']} is already use by another user!",
                )

        retype_password = user_data.pop("retype_password", None)
        password = user_data.get("password", None)
        if password and len(password) < 4:
            abort(HTTPStatus.BAD_REQUEST, "Passwords must have at least 4 characters!")
        if password != retype_password:
            abort(HTTPStatus.BAD_REQUEST, "Passwords did not match, please retry.")

        found_user.update(**user_data)
        DB.session.add(found_user)
        DB.session.commit()

        user_response = ApiResponseGenerator.get_api_response(
            found_user, link_to_relations=USER_EXTRA_LINK_RELATIONS
        )
        user_link = user_response.data.self
        user_response.data = UserSchema().dump(user_response.data)

        self_link = LinkGenerator.get_link_of(
            found_user,
            for_relation=UPDATE_REL,
            extra_relations=(USER_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[user_link],
            embedded=[user_response],
            data=ChangedApiObject(
                self=self_link,
                changed=user_link,
            ),
        )

    @API_V1.response(200, DynamicApiResponseSchema(DeletedApiObjectSchema()))
    @API_V1.require_jwt("jwt", fresh=True)
    def delete(self, username: str):
        if not username:
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested username has the wrong format!"),
            )

        FLASK_OSO.authorize(OsoResource(USER_REL_TYPE, arguments={"username": username}))

        found_user: Optional[User] = User.query.filter(User.username == username).first()

        deleted_self = False

        if found_user is not None:
            FLASK_OSO.authorize_and_set_resource(found_user)
            deleted_self = found_user == g.current_user
            for role in found_user.roles:
                DB.session.delete(role)
            for grant in found_user.grants:
                DB.session.delete(grant)
            DB.session.delete(found_user)
            DB.session.commit()
        else:
            found_user = User(username, "")

        deleted_resource_link = LinkGenerator.get_link_of(found_user)
        redirect_to_link = LinkGenerator.get_link_of(PageResource(User, page_number=1))

        self_link = LinkGenerator.get_link_of(
            found_user,
            for_relation=DELETE_REL,
            extra_relations=(USER_REL_TYPE,)
            if deleted_self
            else (USER_REL_TYPE, LOGOUT_REL),
            ignore_deleted=True,
        )
        self_link.resource_type = DELETED_REL

        return ApiResponse(
            links=[],
            data=DeletedApiObject(
                self=self_link,
                deleted=deleted_resource_link,
                redirect_to=redirect_to_link,
            ),
        )

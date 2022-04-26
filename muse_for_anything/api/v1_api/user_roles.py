"""Module containing the user role management endpoints of the api."""

from http import HTTPStatus
from typing import Any, Dict, List, Optional

from flask.globals import g
from flask.views import MethodView
from flask_babel import gettext
from flask_smorest import abort
from sqlalchemy.sql.expression import literal

from muse_for_anything.api.pagination_util import (
    dump_embedded_page_items,
)
from muse_for_anything.db.models.users import User, UserRole
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource

from .constants import (
    CHANGED_REL,
    CREATE,
    CREATE_REL,
    DELETE_REL,
    DELETED_REL,
    NEW_REL,
    USER_ROLE_EXTRA_LINK_RELATIONS,
    USER_ROLE_REL_TYPE,
)
from .models.auth import UserRoleSchema
from .request_helpers import (
    ApiResponseGenerator,
    CollectionResource,
    LinkGenerator,
)
from .root import API_V1
from ..base_models import (
    ApiLink,
    ApiResponse,
    CursorPageSchema,
    DeletedApiObject,
    DeletedApiObjectSchema,
    DynamicApiResponseSchema,
    NewApiObject,
    NewApiObjectSchema,
)
from ...db.db import DB

# import user management specific generators to load them
from .generators import user_roles  # noqa


@API_V1.route("/auth/users/<string:username>/roles/")
class UserRolesView(MethodView):
    """Endpoint for the user roles collection resource."""

    @API_V1.response(200, DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, username: str, **kwargs: Any):
        """Get the all user roles."""
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                USER_ROLE_REL_TYPE, is_collection=True, arguments={"username": username}
            )
        )

        user: Optional[User] = User.query.filter(User.username == username).first()
        if user is None:
            # not found response only after already authorized!
            abort(HTTPStatus.NOT_FOUND, "Requested user does not exist!")

        user_roles: List[UserRole] = user.roles

        embedded_items, items = dump_embedded_page_items(
            user_roles, UserRoleSchema(), USER_ROLE_EXTRA_LINK_RELATIONS
        )

        collection = CollectionResource(
            UserRole,
            user,
            len(user_roles),
            items,
        )

        self_link = LinkGenerator.get_link_of(collection)

        return ApiResponseGenerator.get_api_response(
            collection,
            extra_links=[
                self_link,
            ],
            extra_embedded=embedded_items,
        )

    @API_V1.arguments(UserRoleSchema())
    @API_V1.response(200, DynamicApiResponseSchema(NewApiObjectSchema()))
    @API_V1.require_jwt("jwt", fresh=True)
    def post(self, user_role_data, username: str):
        FLASK_OSO.authorize(
            OsoResource(USER_ROLE_REL_TYPE, arguments={"username": username}),
            action=CREATE,
        )

        found_user: Optional[User] = User.query.filter(User.username == username).first()
        if found_user is None:
            # not found response only after already authorized!
            abort(HTTPStatus.NOT_FOUND, "Requested user does not exist!")

        FLASK_OSO.authorize_and_set_resource(
            OsoResource(USER_ROLE_REL_TYPE, parent_resource=found_user), action=CREATE
        )

        role_to_create = user_role_data["role"]

        created_role: UserRole

        for role in found_user.roles:
            if role.role == role_to_create:
                created_role = role
                break
        else:
            created_role = UserRole(found_user, role_to_create)
            DB.session.add(created_role)
            DB.session.commit()

        user_role_response = ApiResponseGenerator.get_api_response(
            created_role, link_to_relations=USER_ROLE_EXTRA_LINK_RELATIONS
        )
        user_role_link = user_role_response.data.self
        user_role_response.data = UserRoleSchema().dump(user_role_response.data)

        changed_link = LinkGenerator.get_link_of(
            CollectionResource(UserRole, resource=found_user),
            extra_relations=(CHANGED_REL,),
            ignore_deleted=True,
        )

        self_link = LinkGenerator.get_link_of(
            CollectionResource(UserRole, resource=found_user),
            for_relation=CREATE_REL,
            extra_relations=(USER_ROLE_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = NEW_REL

        return ApiResponse(
            links=[user_role_link, changed_link],
            embedded=[user_role_response],
            data=NewApiObject(
                self=self_link,
                new=user_role_link,
            ),
        )


@API_V1.route("/auth/users/<string:username>/roles/<string:role>/")
class UserRoleView(MethodView):
    """Endpoint for a single user-role resource."""

    @API_V1.response(200, DynamicApiResponseSchema(UserRoleSchema()))
    @API_V1.require_jwt("jwt", optional=True)
    def get(self, username: str, role: str, **kwargs: Any):
        if not username or not role:
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested username or role has the wrong format!"),
            )

        FLASK_OSO.authorize(
            OsoResource(USER_ROLE_REL_TYPE, arguments={"username": username})
        )

        found_user: Optional[User] = User.query.filter(User.username == username).first()

        if found_user is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("User not found."))

        found_role: Optional[UserRole] = None
        for r in found_user.roles:
            if r.role == role:
                found_role = r
                break
        else:
            abort(HTTPStatus.NOT_FOUND, message=gettext("User Role not found."))

        FLASK_OSO.authorize_and_set_resource(found_role)

        return ApiResponseGenerator.get_api_response(
            found_role, link_to_relations=USER_ROLE_EXTRA_LINK_RELATIONS
        )

    @API_V1.response(200, DynamicApiResponseSchema(DeletedApiObjectSchema()))
    @API_V1.require_jwt("jwt", fresh=True)
    def delete(self, username: str, role: str):
        if not username or not role:
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested username or role has the wrong format!"),
            )

        FLASK_OSO.authorize(
            OsoResource(USER_ROLE_REL_TYPE, arguments={"username": username})
        )

        found_user: Optional[User] = User.query.filter(User.username == username).first()

        if found_user is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("User not found."))

        found_role: Optional[UserRole] = None
        for r in found_user.roles:
            if r.role == role:
                found_role = r
                break

        if found_role:
            FLASK_OSO.authorize_and_set_resource(found_role)

        to_delete = [r for r in found_user.roles if r.role == role]
        if to_delete:
            for r in to_delete:
                DB.session.delete(r)
            DB.session.commit()

        dummy_role = UserRole(found_user, role=role)

        deleted_resource_link = LinkGenerator.get_link_of(dummy_role)
        redirect_to_link = LinkGenerator.get_link_of(found_user)

        changed_link = LinkGenerator.get_link_of(
            CollectionResource(UserRole, resource=found_user),
            extra_relations=(CHANGED_REL,),
            ignore_deleted=True,
        )

        self_link = LinkGenerator.get_link_of(
            dummy_role,
            for_relation=DELETE_REL,
            extra_relations=(USER_ROLE_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = DELETED_REL

        return ApiResponse(
            links=[changed_link],
            data=DeletedApiObject(
                self=self_link,
                deleted=deleted_resource_link,
                redirect_to=redirect_to_link,
            ),
        )

"""Module containing the authentication API of the v1 API."""

from dataclasses import dataclass
from typing import Dict, Optional

from flask.globals import g
from flask.helpers import url_for
from flask.views import MethodView
from flask_babel import gettext
from flask_jwt_extended import create_access_token, create_refresh_token, current_user
from flask_smorest import abort

from muse_for_anything.api.v1_api.constants import (
    COLLECTION_REL,
    FRESH_LOGIN_REL,
    LOGIN_REL,
    PAGE_REL,
    POST_REL,
    REFRESH_TOKEN_REL,
    USER_REL_TYPE,
)

from .models.auth import (
    AccessTokenSchema,
    FreshLoginPostSchema,
    LoginPostSchema,
    LoginTokensSchema,
    UserData,
    UserSchema,
)
from .root import API_V1
from ..base_models import ApiLink, ApiResponse, DynamicApiResponseSchema
from ...db.models.users import Guest, User


@dataclass
class AuthRootData:
    self: ApiLink


@dataclass
class LoginTokensData:
    self: ApiLink
    access_token: str
    refresh_token: str


@dataclass
class RefreshedTokenData:
    self: ApiLink
    access_token: str


@API_V1.route("/auth/")
class AuthRootView(MethodView):
    """Root endpoint for all authentication resources."""

    @API_V1.response(200, DynamicApiResponseSchema())
    def get(self):
        """Get the urls for the authentication api."""
        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.LoginView", _external=True),
                    rel=(POST_REL,),
                    resource_type=LOGIN_REL,
                ),
                ApiLink(
                    href=url_for("api-v1.FreshLoginView", _external=True),
                    rel=(POST_REL,),
                    resource_type=FRESH_LOGIN_REL,
                ),
                ApiLink(
                    href=url_for("api-v1.RefreshView", _external=True),
                    rel=(POST_REL,),
                    resource_type=REFRESH_TOKEN_REL,
                ),
                ApiLink(
                    href=url_for("api-v1.WhoamiView", _external=True),
                    rel=("whoami",),
                    resource_type=USER_REL_TYPE,
                ),
                ApiLink(
                    href=url_for("api-v1.UsersView", _external=True),
                    rel=(COLLECTION_REL, PAGE_REL),
                    resource_type=USER_REL_TYPE,
                ),
            ],
            data=AuthRootData(
                self=ApiLink(
                    href=url_for("api-v1.AuthRootView", _external=True),
                    rel=("authentication",),
                    resource_type="api",
                )
            ),
        )


@API_V1.route("/auth/login/")
class LoginView(MethodView):
    """Login endpoint to retrieve api tokens."""

    @API_V1.arguments(
        LoginPostSchema(),
        location="json",
        description="The login credentials of the user.",
    )
    @API_V1.response(200, DynamicApiResponseSchema(data_schema=LoginTokensSchema()))
    def post(self, credentials: Dict[str, str]):
        """Login with the user credentials to receive a access and refresh token pair.

        The access token can be used for all authorized api endpoints.
        The refresh token can only be used with the refresh endpoint to get a new access token.
        """
        username = credentials.get("username", "")
        user_query = None
        if "@" in username:
            user_query = User.query.filter(User.e_mail == username)
        else:
            user_query = User.query.filter(User.username == username)
        user: Optional[User] = user_query.first()
        error_message = gettext("Username or password invalid!")
        if user is None:
            # call fake_authenticate to not leak usernames through timing difference
            User.fake_authenticate(credentials.get("password", ""))
            abort(400, error_message)
        elif not user.authenticate(credentials.get("password", "")):
            abort(400, error_message)
        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.RefreshView", _external=True),
                    rel=(POST_REL,),
                    resource_type=REFRESH_TOKEN_REL,
                ),
                ApiLink(
                    href=url_for("api-v1.FreshLoginView", _external=True),
                    rel=(POST_REL,),
                    resource_type=FRESH_LOGIN_REL,
                ),
                ApiLink(
                    href=url_for("api-v1.WhoamiView", _external=True),
                    rel=("whoami",),
                    resource_type=USER_REL_TYPE,
                ),
            ],
            data=LoginTokensData(
                self=ApiLink(
                    href=url_for("api-v1.LoginView", _external=True),
                    rel=(POST_REL,),
                    resource_type=LOGIN_REL,
                ),
                access_token=create_access_token(identity=user, fresh=True),
                refresh_token=create_refresh_token(identity=user),
            ),
        )


@API_V1.route("/auth/fresh-login/")
class FreshLoginView(MethodView):
    """Login endpoint to retrieve new fresh api tokens for logged in users."""

    @API_V1.arguments(
        FreshLoginPostSchema(),
        location="json",
        description="The login credentials of the user.",
    )
    @API_V1.response(200, DynamicApiResponseSchema(data_schema=LoginTokensSchema()))
    @API_V1.require_jwt("jwt")
    def post(self, credentials: Dict[str, str]):
        """Login with the user credentials to receive fresh access token.

        The fresh access token can be used for all authorized api endpoints,
        including endpoints requiring recent authentication using a password.
        """
        user: Optional[User] = g.current_user
        error_message = gettext("Username or password invalid!")
        if user is None or type(user) == Guest:
            # call fake_authenticate to not leak usernames through timing difference
            User.fake_authenticate(credentials.get("password", ""))
            abort(400, error_message)
        elif not user.authenticate(credentials.get("password", "")):
            abort(400, error_message)
        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.RefreshView", _external=True),
                    rel=(POST_REL,),
                    resource_type=REFRESH_TOKEN_REL,
                ),
                ApiLink(
                    href=url_for("api-v1.WhoamiView", _external=True),
                    rel=("whoami",),
                    resource_type=USER_REL_TYPE,
                ),
            ],
            data=LoginTokensData(
                self=ApiLink(
                    href=url_for("api-v1.FreshLoginView", _external=True),
                    rel=(POST_REL,),
                    resource_type=FRESH_LOGIN_REL,
                ),
                access_token=create_access_token(identity=user, fresh=True),
                refresh_token=create_refresh_token(identity=user),
            ),
        )


@API_V1.route("/auth/refresh/")
class RefreshView(MethodView):
    """Refresh endpoint to retrieve new api access tokens."""

    @API_V1.response(200, DynamicApiResponseSchema(AccessTokenSchema()))
    @API_V1.require_jwt("jwt-refresh-token", refresh_token=True)
    def post(self):
        """Get a new access token.

        This method requires the jwt refresh token!
        """
        identity = current_user
        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.WhoamiView", _external=True),
                    rel=("whoami",),
                    resource_type=USER_REL_TYPE,
                ),
                ApiLink(
                    href=url_for("api-v1.FreshLoginView", _external=True),
                    rel=(POST_REL,),
                    resource_type=FRESH_LOGIN_REL,
                ),
            ],
            data=RefreshedTokenData(
                self=ApiLink(
                    href=url_for("api-v1.RefreshView", _external=True),
                    rel=(POST_REL,),
                    resource_type=REFRESH_TOKEN_REL,
                ),
                access_token=create_access_token(identity=identity),
            ),
        )


@API_V1.route("/auth/whoami/")
class WhoamiView(MethodView):
    """Whoami endpoint to test the api token and get the current user info."""

    @API_V1.response(200, DynamicApiResponseSchema(UserSchema()))
    @API_V1.require_jwt("jwt")
    def get(self):
        """Get the user object of the current user."""
        return ApiResponse(
            links=[],
            data=UserData(
                self=ApiLink(
                    href=url_for("api-v1.WhoamiView", _external=True),
                    rel=("whoami",),
                    resource_type=USER_REL_TYPE,
                ),
                username=current_user.username,
                e_mail=current_user.e_mail,
            ),
        )

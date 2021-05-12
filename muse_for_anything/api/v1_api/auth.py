"""Module containing the authentication API of the v1 API."""

from typing import Dict
from flask.helpers import url_for
from flask.views import MethodView
from flask_babel import gettext
from dataclasses import dataclass
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    current_user,
)
from flask_smorest import abort

from .root import API_V1
from ..base_models import ApiLink, ApiResponse, DynamicApiResponseSchema
from .models import (
    LoginPostSchema,
    LoginTokensSchema,
    AccessTokenSchema,
    UserSchema,
)

from ...db.models.users import User


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


@dataclass
class UserData:
    self: ApiLink
    username: str
    e_mail: str


@API_V1.route("/auth/")
class AuthRootView(MethodView):
    """Root endpoint for all authentication resources."""

    @API_V1.response(DynamicApiResponseSchema())
    def get(self):
        """Get the urls for the authentication api."""
        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.LoginView", _external=True),
                    rel=("login", "post"),
                    resource_type="login",
                ),
                ApiLink(
                    href=url_for("api-v1.RefreshView", _external=True),
                    rel=("refresh", "post"),
                    resource_type="refresh",
                ),
                ApiLink(
                    href=url_for("api-v1.WhoamiView", _external=True),
                    rel=("whoami", "user"),
                    resource_type="user",
                ),
            ],
            data=AuthRootData(
                self=ApiLink(
                    href=url_for("api-v1.AuthRootView", _external=True),
                    rel=("api", "authentication"),
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
    @API_V1.response(DynamicApiResponseSchema(data_schema=LoginTokensSchema()))
    def post(self, credentials: Dict[str, str]):
        """Login with the user credentials to receive a access and refresh token pair.

        The access token can be used for all authorized api endpoints.
        The refresh token can only be used with the refresh endpoint to get a new access token.
        """
        username = credentials.get("username")
        user_query = None
        if "@" in username:
            user_query = User.query.filter(User.e_mail == username)
        else:
            user_query = User.query.filter(User.username == username)
        user: Optiona[User] = user_query.first()
        error_message = gettext("Username or password invalid!")
        if user is None:
            # call fake_authenticate to not leak usernames through timing difference
            User.fake_authenticate(credentials.get("password"))
            abort(400, error_message)
        elif not user.authenticate(credentials.get("password")):
            abort(400, error_message)
        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.RefreshView", _external=True),
                    rel=("refresh", "post"),
                    resource_type="refresh",
                ),
                ApiLink(
                    href=url_for("api-v1.WhoamiView", _external=True),
                    rel=("whoami", "user"),
                    resource_type="user",
                ),
            ],
            data=LoginTokensData(
                self=ApiLink(
                    href=url_for("api-v1.LoginView", _external=True),
                    rel=("login", "post"),
                    resource_type="login",
                ),
                access_token=create_access_token(identity=user),
                refresh_token=create_refresh_token(identity=user),
            ),
        )


@API_V1.route("/auth/refresh/")
class RefreshView(MethodView):
    """Refresh endpoint to retrieve new api access tokens."""

    @API_V1.response(DynamicApiResponseSchema(AccessTokenSchema()))
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
                    rel=("whoami", "user"),
                    resource_type="user",
                ),
            ],
            data=RefreshedTokenData(
                self=ApiLink(
                    href=url_for("api-v1.RefreshView", _external=True),
                    rel=("refresh", "post"),
                    resource_type="refresh",
                ),
                access_token=create_access_token(identity=identity, fresh=True),
            ),
        )


@API_V1.route("/auth/whoami/")
class WhoamiView(MethodView):
    """Whoami endpoint to test the api token and get the current user info."""

    @API_V1.response(DynamicApiResponseSchema(UserSchema()))
    @API_V1.require_jwt("jwt")
    def get(self):
        """Get the user object of the current user."""
        return ApiResponse(
            links=[],
            data=UserData(
                self=ApiLink(
                    href=url_for("api-v1.WhoamiView", _external=True),
                    rel=("whoami", "user"),
                    resource_type="user",
                ),
                username=current_user.username,
                e_mail=current_user.e_mail,
            ),
        )

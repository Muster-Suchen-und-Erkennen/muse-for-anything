"""Module containing all API related code of the project."""

from flask import Flask
from flask.helpers import url_for
from flask.views import MethodView
import marshmallow as ma
from flask_smorest import Api, Blueprint as SmorestBlueprint
from .base_models import (
    ApiLink,
    ApiObjectSchema,
    ApiResponse,
    DynamicApiResponseSchema,
)
from .v1_api import API_V1
from .jwt import SECURITY_SCHEMES

"""A single API instance. All api versions should be blueprints."""
ROOT_API = Api(spec_kwargs={"title": "API Root", "version": "v0.1.0"})


class RootDataSchema(ApiObjectSchema):
    title = ma.fields.String(required=True, allow_none=False, dump_only=True)
    latest = ma.fields.String(required=True, allow_none=False, dump_only=True)
    v0_1 = ma.fields.String(
        data_key="v0.1", required=True, allow_none=False, dump_only=True
    )
    v0_1_0 = ma.fields.String(
        data_key="v0.1.0", required=True, allow_none=False, dump_only=True
    )


ROOT_ENDPOINT = SmorestBlueprint(
    "api-root",
    "root",
    url_prefix="/api",
    description="The API endpoint pointing towards all api versions.",
)


@ROOT_ENDPOINT.route("/")
class RootView(MethodView):
    @ROOT_ENDPOINT.response(200, DynamicApiResponseSchema(RootDataSchema()))
    def get(self) -> ApiResponse:
        """Get the Root API information containing the links to all versions of this api."""
        api_data = {
            "self": ApiLink(
                href=url_for("api-root.RootView", _external=True),
                rel=("self", "api"),
                resource_type="api",
            ),
            "title": ROOT_API.spec.title,
            "latest": "v0.1.0",
            "v0_1": "v0.1.0",
            "v0_1_0": "v0.1.0",
        }
        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.RootView", _external=True),
                    rel=("api", "v0.1.0", "latest"),
                    resource_type="api",
                ),
            ],
            embedded=[],
            data=api_data,
        )


def register_root_api(app: Flask):
    """Register the API with the flask app."""
    ROOT_API.init_app(app)

    # register security schemes in doc
    for name, scheme in SECURITY_SCHEMES.items():
        ROOT_API.spec.components.security_scheme(name, scheme)

    # register API blueprints (only do this after the API is registered with flask!)
    ROOT_API.register_blueprint(ROOT_ENDPOINT)
    ROOT_API.register_blueprint(API_V1)

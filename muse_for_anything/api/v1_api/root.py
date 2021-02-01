"""Module containing the root endpoint of the v1 API."""

from dataclasses import dataclass
from flask.helpers import url_for
from flask.views import MethodView
from ..util import SecurityBlueprint as SmorestBlueprint, template_url_for
from ..base_models import ApiResponse, ApiLink, DynamicApiResponseSchema, KeyedApiLink


API_V1 = SmorestBlueprint(
    "api-v1", "API v1", description="Version 1 of the API.", url_prefix="/api/v1"
)


@dataclass()
class RootData:
    self: ApiLink


@API_V1.route("/")
class RootView(MethodView):
    """Root endpoint of the v1 api."""

    @API_V1.response(DynamicApiResponseSchema())
    def get(self):
        """Get the urls of the next endpoints of the v1 api to call."""
        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.AuthRootView", _external=True),
                    rel=("api", "authentication"),
                    resource_type="api",
                ),
                ApiLink(
                    href=url_for("api-v1.SchemaRootView", _external=True),
                    rel=("api", "schema"),
                    resource_type="api",
                ),
                ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True),
                    rel=("first", "page", "collection"),
                    resource_type="ont-namespace",
                ),
            ],
            embedded=[],
            keyed_links=[
                KeyedApiLink(
                    href=template_url_for(
                        "api-v1.NamespaceView",
                        {"namespace": "namespaceId"},
                        _external=True,
                    ),
                    rel=tuple(),
                    resource_type="ont-namespace",
                    key=("namespaceId",),
                ),
                KeyedApiLink(
                    href=template_url_for(
                        "api-v1.NamespacesView",
                        {},
                        _external=True,
                    ),
                    rel=("collection", "page"),
                    resource_type="ont-namespace",
                    query_key=("item-count", "cursor", "sort"),
                ),
                KeyedApiLink(
                    href=template_url_for(
                        "api-v1.TypesView",
                        {
                            "namespace": "namespaceId",
                        },
                        _external=True,
                    ),
                    rel=("collection", "page"),
                    resource_type="ont-type",
                    key=("namespaceId",),
                    query_key=("item-count", "cursor", "sort"),
                ),
                KeyedApiLink(
                    href=template_url_for(
                        "api-v1.TypeView",
                        {
                            "namespace": "namespaceId",
                            "object_type": "typeId",
                        },
                        _external=True,
                    ),
                    rel=tuple(),
                    resource_type="ont-type",
                    key=("namespaceId", "typeId"),
                ),
                KeyedApiLink(
                    href=template_url_for(
                        "api-v1.TypeVersionsView",
                        {
                            "namespace": "namespaceId",
                            "object_type": "typeId",
                        },
                        _external=True,
                    ),
                    rel=("collection", "page"),
                    resource_type="ont-type-version",
                    key=("namespaceId", "typeId"),
                    query_key=("item-count", "cursor", "sort"),
                ),
                KeyedApiLink(
                    href=template_url_for(
                        "api-v1.TypeVersionView",
                        {
                            "namespace": "namespaceId",
                            "object_type": "typeId",
                            "version": "typeVersion",
                        },
                        _external=True,
                    ),
                    rel=tuple(),
                    resource_type="ont-type-version",
                    key=("namespaceId", "typeId", "typeVersion"),
                ),
            ],
            data=RootData(
                self=ApiLink(
                    href=url_for("api-v1.RootView", _external=True),
                    rel=("api", "v0.1.0"),
                    resource_type="api",
                )
            ),
        )

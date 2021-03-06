"""Module containing the type versions API endpoints of the v1 API."""

from flask import request, Response, jsonify
from flask.helpers import url_for
from marshmallow.utils import INCLUDE
from muse_for_anything.api.v1_api.ontology_type_versions_helpers import (
    nav_links_for_type_version,
    nav_links_for_type_versions_page,
    type_version_page_params_to_key,
    type_version_to_api_response,
    type_version_to_type_data,
)
from flask_babel import gettext
from typing import Any, Callable, Dict, List, Optional, Union, cast
from flask.views import MethodView
from sqlalchemy.sql.expression import asc, desc, literal
from sqlalchemy.orm.query import Query
from flask_smorest import abort
from http import HTTPStatus

from .root import API_V1
from ..util import JSON_MIMETYPE, JSON_SCHEMA_MIMETYPE
from ..base_models import (
    ApiLink,
    ApiResponse,
    CursorPage,
    CursorPageArgumentsSchema,
    CursorPageSchema,
    DynamicApiResponseSchema,
)
from .models.ontology import ObjectTypeSchema
from ...db.db import DB
from ...db.pagination import get_page_info
from ...db.models.namespace import Namespace
from ...db.models.ontology_objects import OntologyObjectType, OntologyObjectTypeVersion

from .namespace_helpers import (
    query_params_to_api_key,
)


@API_V1.route("/namespaces/<string:namespace>/types/<string:object_type>/versions/")
class TypeVersionsView(MethodView):
    """Endpoint for all versions of a type."""

    def _check_path_params(self, namespace: str, object_type: str):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not object_type or not object_type.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested type id has the wrong format!"),
            )

    def _get_object_type(self, namespace: str, object_type: str) -> OntologyObjectType:
        namespace_id = int(namespace)
        object_type_id = int(object_type)
        found_object_type: Optional[OntologyObjectType] = OntologyObjectType.query.filter(
            OntologyObjectType.id == object_type_id,
            OntologyObjectType.namespace_id == namespace_id,
        ).first()

        if found_object_type is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Object Type not found."))
        return found_object_type  # is not None because abort raises exception

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    def get(self, namespace: str, object_type: str, **kwargs: Any):
        """Get all versions of a type."""
        self._check_path_params(namespace=namespace, object_type=object_type)
        found_object_type: OntologyObjectType = self._get_object_type(
            namespace=namespace, object_type=object_type
        )

        cursor: Optional[str] = kwargs.get("cursor", None)
        item_count: int = cast(int, kwargs.get("item_count", 50))
        sort: str = cast(str, kwargs.get("sort", "-version").lstrip("+"))
        sort_function: Callable[..., Any] = (
            desc if sort is not None and sort.startswith("-") else asc
        )
        sort_key: str = sort.lstrip("+-") if sort is not None else "version"

        ontology_type_version_filter = (
            OntologyObjectTypeVersion.deleted_on == None,
            OntologyObjectTypeVersion.ontology_type == found_object_type,
        )

        pagination_info = get_page_info(
            OntologyObjectTypeVersion,
            OntologyObjectTypeVersion.id,
            [OntologyObjectTypeVersion.version],
            cursor,
            sort,
            item_count,
            filter_criteria=ontology_type_version_filter,
        )

        query: Query = OntologyObjectTypeVersion.query.filter(
            *ontology_type_version_filter
        )

        query = query.order_by(sort_function(OntologyObjectTypeVersion.version))

        if cursor is not None and cursor.isdigit():
            # hope that cursor row has not jumped compared to last query in get_page_info
            query = query.offset(pagination_info.cursor_row)

        query = query.limit(item_count)

        type_versions: List[OntologyObjectTypeVersion] = query.all()

        embedded_items: List[ApiResponse] = [
            type_version_to_api_response(type_version) for type_version in type_versions
        ]
        items: List[ApiLink] = [item.data.get("self") for item in embedded_items]

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

        self_link = ApiLink(
            href=url_for(
                "api-v1.TypeVersionsView",
                namespace=namespace,
                object_type=object_type,
                _external=True,
                **self_query_params,
            ),
            rel=(
                *self_rels,
                "page",
                f"page-{pagination_info.cursor_page}",
                "collection",
                "schema",
            ),
            resource_type="ont-type-version",
            resource_key=type_version_page_params_to_key(
                found_object_type, self_query_params
            ),
            schema=url_for(
                "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
            ),
        )

        extra_links: List[ApiLink] = [self_link]

        if pagination_info.last_page is not None:
            if pagination_info.cursor_page != pagination_info.last_page.page:
                # only if current page is not last page
                last_query_params = dict(query_params)
                last_query_params["cursor"] = str(pagination_info.last_page.cursor)

                extra_links.append(
                    ApiLink(
                        href=url_for(
                            "api-v1.TypeVersionsView",
                            namespace=namespace,
                            object_type=object_type,
                            _external=True,
                            **last_query_params,
                        ),
                        rel=(
                            "last",
                            "page",
                            f"page-{pagination_info.last_page.page}",
                            "collection",
                            "schema",
                        ),
                        resource_type="ont-type-version",
                        resource_key=type_version_page_params_to_key(
                            found_object_type, last_query_params
                        ),
                        schema=url_for(
                            "api-v1.ApiSchemaView",
                            schema_id="OntologyType",
                            _external=True,
                        ),
                    )
                )

        for page in pagination_info.surrounding_pages:
            if page == pagination_info.last_page:
                continue  # link already included
            page_query_params = dict(query_params)
            page_query_params["cursor"] = str(page.cursor)

            extra_rels = []
            if page.page + 1 == pagination_info.cursor_page:
                extra_rels.append("prev")
            if page.page - 1 == pagination_info.cursor_page:
                extra_rels.append("next")

            extra_links.append(
                ApiLink(
                    href=url_for(
                        "api-v1.TypeVersionsView",
                        namespace=namespace,
                        object_type=object_type,
                        _external=True,
                        **page_query_params,
                    ),
                    rel=(
                        *extra_rels,
                        "page",
                        f"page-{page.page}",
                        "collection",
                        "schema",
                    ),
                    resource_type="ont-type-version",
                    resource_key=type_version_page_params_to_key(
                        found_object_type, page_query_params
                    ),
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
                    ),
                )
            )

        extra_links.extend(nav_links_for_type_versions_page(found_object_type))

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for("api-v1.NamespacesView", _external=True, **query_params),
                    rel=("first", "page", "page-1", "collection", "nav"),
                    resource_type="ont-namespace",
                    resource_key=query_params_to_api_key({"item-count": item_count}),
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                ApiLink(
                    href=url_for(
                        "api-v1.TypeVersionsView",
                        namespace=namespace,
                        object_type=object_type,
                        _external=True,
                        **query_params,
                    ),
                    rel=("first", "page", "page-1", "collection", "schema"),
                    resource_type="ont-type-version",
                    resource_key=type_version_page_params_to_key(
                        found_object_type, query_params
                    ),
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
                    ),
                ),
                *extra_links,
            ],
            embedded=embedded_items,
            data=CursorPage(
                self=self_link,
                collection_size=pagination_info.collection_size,
                page=pagination_info.cursor_page,
                first_row=pagination_info.cursor_row + 1,
                items=items,
            ),
        )


@API_V1.route(
    "/namespaces/<string:namespace>/types/<string:object_type>/versions/<string:version>/"
)
class TypeVersionView(MethodView):
    """Endpoint a single object type resource."""

    def _check_path_params(self, namespace: str, object_type: str, version: str):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not object_type or not object_type.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested type id has the wrong format!"),
            )
        if not version or not version.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested version has the wrong format!"),
            )

    def _get_object_type_version(
        self, namespace: str, object_type: str, version: str
    ) -> OntologyObjectTypeVersion:
        namespace_id = int(namespace)
        object_type_id = int(object_type)
        version_number = int(version)
        found_object_type_version: Optional[
            OntologyObjectTypeVersion
        ] = OntologyObjectTypeVersion.query.filter(
            OntologyObjectTypeVersion.version == version_number,
            OntologyObjectTypeVersion.object_type_id == object_type_id,
        ).first()

        if (
            found_object_type_version is None
            or found_object_type_version.ontology_type.namespace_id != namespace_id
        ):
            abort(HTTPStatus.NOT_FOUND, message=gettext("Object Type not found."))
        return found_object_type_version  # is not None because abort raises exception

    @API_V1.response(DynamicApiResponseSchema(ObjectTypeSchema()))
    def get(self, namespace: str, object_type: str, version: str, **kwargs: Any):
        """Get a specific version of a type."""
        self._check_path_params(
            namespace=namespace, object_type=object_type, version=version
        )
        found_object_type_version: OntologyObjectTypeVersion = (
            self._get_object_type_version(
                namespace=namespace, object_type=object_type, version=version
            )
        )

        match = request.accept_mimetypes.best_match(
            (JSON_MIMETYPE, JSON_SCHEMA_MIMETYPE),
            default=JSON_MIMETYPE,
        )

        if match == JSON_SCHEMA_MIMETYPE:
            # only return jsonschema if schema mimetype is requested
            response: Response = jsonify(found_object_type_version.data)
            response.mimetype = JSON_SCHEMA_MIMETYPE
            return response

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for(
                        "api-v1.NamespacesView",
                        _external=True,
                        **{"item-count": 50},
                        sort="name",
                    ),
                    rel=("first", "page", "collection", "ont-namespace"),
                    resource_type="ont-namespace",
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                *nav_links_for_type_version(found_object_type_version),
            ],
            data=type_version_to_type_data(found_object_type_version),
        )

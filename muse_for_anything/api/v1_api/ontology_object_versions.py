"""Module containing the object API endpoints of the v1 API."""

from datetime import datetime
from muse_for_anything.api.v1_api.ontology_object_validation import validate_object

from marshmallow.utils import INCLUDE
from flask_babel import gettext
from muse_for_anything.api.util import template_url_for
from typing import Any, Callable, Dict, List, Optional, Union, cast
from flask.helpers import url_for
from flask.views import MethodView
from sqlalchemy.sql.expression import asc, desc, literal
from sqlalchemy.orm.query import Query
from flask_smorest import abort
from http import HTTPStatus

from .root import API_V1
from ..base_models import (
    ApiLink,
    ApiResponse,
    ChangedApiObject,
    ChangedApiObjectSchema,
    CursorPage,
    CursorPageArgumentsSchema,
    CursorPageSchema,
    DynamicApiResponseSchema,
    NewApiObject,
    NewApiObjectSchema,
)
from .models.ontology import (
    ObjectSchema,
)
from ...db.db import DB
from ...db.pagination import get_page_info
from ...db.models.namespace import Namespace
from ...db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectVersion,
)

from .namespace_helpers import (
    query_params_to_api_key,
)

from muse_for_anything.api.v1_api.ontology_object_helpers import (
    nav_links_for_object_version,
    nav_links_for_object_versions_page,
    object_to_object_data,
    object_version_page_params_to_key,
    object_version_to_api_response,
)


@API_V1.route("/namespaces/<string:namespace>/objects/<string:object_id>/versions/")
class ObjectVersionsView(MethodView):
    """Endpoint for all versions of a type."""

    def _check_path_params(self, namespace: str, object_id: str):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not object_id or not object_id.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested object id has the wrong format!"),
            )

    def _get_object(self, namespace: str, object_id: str) -> OntologyObject:
        namespace_id = int(namespace)
        ontology_object_id = int(object_id)
        found_object: Optional[OntologyObject] = OntologyObject.query.filter(
            OntologyObject.id == ontology_object_id,
            OntologyObject.namespace_id == namespace_id,
        ).first()

        if found_object is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Object not found."))
        return found_object  # is not None because abort raises exception

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    def get(self, namespace: str, object_id: str, **kwargs: Any):
        """Get all versions of an object."""
        self._check_path_params(namespace=namespace, object_id=object_id)
        found_object: OntologyObject = self._get_object(
            namespace=namespace, object_id=object_id
        )

        cursor: Optional[str] = kwargs.get("cursor", None)
        item_count: int = cast(int, kwargs.get("item_count", 25))
        sort: str = cast(str, kwargs.get("sort", "-version").lstrip("+"))

        object_version_filter = (
            OntologyObjectVersion.deleted_on == None,
            OntologyObjectVersion.ontology_object == found_object,
        )

        pagination_info = get_page_info(
            OntologyObjectVersion,
            OntologyObjectVersion.id,
            [OntologyObjectVersion.version],
            cursor,
            sort,
            item_count,
            filter_criteria=object_version_filter,
        )

        object_versions: List[
            OntologyObjectVersion
        ] = pagination_info.page_items_query.all()

        embedded_items: List[ApiResponse] = [
            object_version_to_api_response(object_version)
            for object_version in object_versions
        ]
        items: List[ApiLink] = [item.data.get("self") for item in embedded_items]

        query_params = {
            "item-count": item_count,
            "sort": sort,
        }

        self_query_params = dict(query_params)

        if cursor:
            self_query_params["cursor"] = cursor

        self_rels: List[str] = []
        if pagination_info.cursor_page == 1:
            self_rels.append("first")
        if (
            pagination_info.last_page
            and pagination_info.cursor_page == pagination_info.last_page.page
        ):
            self_rels.append("last")

        self_link = ApiLink(
            href=url_for(
                "api-v1.ObjectVersionsView",
                namespace=namespace,
                object_id=object_id,
                _external=True,
                **self_query_params,
            ),
            rel=(
                *self_rels,
                "page",
                f"page-{pagination_info.cursor_page}",
                "collection",
            ),
            resource_type="ont-object-version",
            resource_key=object_version_page_params_to_key(
                found_object, self_query_params
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
                            "api-v1.ObjectVersionsView",
                            namespace=namespace,
                            object_id=object_id,
                            _external=True,
                            **last_query_params,
                        ),
                        rel=(
                            "last",
                            "page",
                            f"page-{pagination_info.last_page.page}",
                            "collection",
                        ),
                        resource_type="ont-object-version",
                        resource_key=object_version_page_params_to_key(
                            found_object, last_query_params
                        ),
                    )
                )

        for page in pagination_info.surrounding_pages:
            if page == pagination_info.last_page:
                continue  # link already included
            page_query_params = dict(query_params)
            page_query_params["cursor"] = str(page.cursor)

            extra_rels: List[str] = []
            if page.page + 1 == pagination_info.cursor_page:
                extra_rels.append("prev")
            if page.page - 1 == pagination_info.cursor_page:
                extra_rels.append("next")

            extra_links.append(
                ApiLink(
                    href=url_for(
                        "api-v1.ObjectVersionsView",
                        namespace=namespace,
                        object_id=object_id,
                        _external=True,
                        **page_query_params,
                    ),
                    rel=(
                        *extra_rels,
                        "page",
                        f"page-{page.page}",
                        "collection",
                    ),
                    resource_type="ont-object-version",
                    resource_key=object_version_page_params_to_key(
                        found_object, page_query_params
                    ),
                )
            )

        extra_links.extend(nav_links_for_object_versions_page(found_object))

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
                        "api-v1.ObjectVersionsView",
                        namespace=namespace,
                        object_id=object_id,
                        _external=True,
                        **query_params,
                    ),
                    rel=("first", "page", "page-1", "collection"),
                    resource_type="ont-object-version",
                    resource_key=object_version_page_params_to_key(
                        found_object, query_params
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
    "/namespaces/<string:namespace>/objects/<string:object_id>/versions/<string:version>/"
)
class ObjectVersionView(MethodView):
    """Endpoint for all versions of a type."""

    def _check_path_params(self, namespace: str, object_id: str, version: str):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not object_id or not object_id.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested object id has the wrong format!"),
            )
        if not version or not version.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested version has the wrong format!"),
            )

    def _get_object_version(
        self, namespace: str, object_id: str, version: str
    ) -> OntologyObjectVersion:
        namespace_id = int(namespace)
        ontology_object_id = int(object_id)
        version_number = int(version)
        found_object_version: Optional[
            OntologyObjectVersion
        ] = OntologyObjectVersion.query.filter(
            OntologyObjectVersion.version == version_number,
            OntologyObjectVersion.object_id == ontology_object_id,
        ).first()

        if (
            found_object_version is None
            or found_object_version.ontology_object.namespace_id != namespace_id
        ):
            abort(HTTPStatus.NOT_FOUND, message=gettext("Object version not found."))
        return found_object_version  # is not None because abort raises exception

    @API_V1.response(DynamicApiResponseSchema(ObjectSchema()))
    def get(self, namespace: str, object_id: str, version: str, **kwargs: Any):
        """Get a specific version of an object."""
        self._check_path_params(namespace=namespace, object_id=object_id, version=version)
        found_object_version: OntologyObjectVersion = self._get_object_version(
            namespace=namespace, object_id=object_id, version=version
        )

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for(
                        "api-v1.NamespacesView",
                        _external=True,
                        **{"item-count": 25},
                        sort="name",
                    ),
                    rel=("first", "page", "collection", "ont-namespace"),
                    resource_type="ont-namespace",
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                *nav_links_for_object_version(found_object_version),
            ],
            data=object_to_object_data(found_object_version),
        )

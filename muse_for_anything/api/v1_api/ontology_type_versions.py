"""Module containing the type versions API endpoints of the v1 API."""

from http import HTTPStatus
from typing import Any, List, Optional, cast

from flask import Response, jsonify, request
from flask.views import MethodView
from flask_babel import gettext
from flask_smorest import abort
from marshmallow.utils import INCLUDE

from muse_for_anything.api.pagination_util import (
    PaginationOptions,
    default_get_page_info,
    dump_embedded_page_items,
    generate_page_links,
    prepare_pagination_query_args,
)
from muse_for_anything.api.v1_api.constants import (
    TYPE_VERSION_EXTRA_LINK_RELATIONS,
    TYPE_VERSION_PAGE_EXTRA_LINK_RELATIONS,
    TYPE_VERSION_REL_TYPE,
)
from muse_for_anything.api.v1_api.request_helpers import (
    ApiResponseGenerator,
    LinkGenerator,
    PageResource,
)
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource

from .models.ontology import ObjectTypeSchema, ObjectTypeVersionsPageParamsSchema
from .root import API_V1
from ..base_models import (
    CollectionFilter,
    CollectionFilterOption,
    CursorPageSchema,
    DynamicApiResponseSchema,
)
from ..util import JSON_MIMETYPE, JSON_SCHEMA_MIMETYPE
from ...db.db import DB
from ...db.models.ontology_objects import OntologyObjectType, OntologyObjectTypeVersion

# import type specific generators to load them
from .generators import type as type_  # noqa
from .generators import type_version  # noqa


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

    @API_V1.arguments(
        ObjectTypeVersionsPageParamsSchema, location="query", as_kwargs=True
    )
    @API_V1.response(200, DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, object_type: str, deleted: bool = False, **kwargs: Any):
        """Get all versions of a type."""
        self._check_path_params(namespace=namespace, object_type=object_type)
        found_object_type: OntologyObjectType = self._get_object_type(
            namespace=namespace, object_type=object_type
        )
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                TYPE_VERSION_REL_TYPE,
                is_collection=True,
                parent_resource=found_object_type,
            )
        )

        pagination_options: PaginationOptions = prepare_pagination_query_args(
            **kwargs, _sort_default="-version"
        )

        is_admin = FLASK_OSO.is_admin()

        if deleted and not is_admin:
            deleted = False

        ontology_type_version_filter = (
            (
                OntologyObjectTypeVersion.deleted_on == None
                if not deleted
                else OntologyObjectTypeVersion.deleted_on != None
            ),
            OntologyObjectTypeVersion.ontology_type == found_object_type,
        )

        pagination_info = default_get_page_info(
            OntologyObjectTypeVersion,
            ontology_type_version_filter,
            pagination_options,
            [OntologyObjectTypeVersion.version],
        )

        type_versions: List[OntologyObjectTypeVersion] = (
            pagination_info.page_items_query.all()
        )

        embedded_items, items = dump_embedded_page_items(
            type_versions, ObjectTypeSchema(), TYPE_VERSION_EXTRA_LINK_RELATIONS
        )

        page_resource = PageResource(
            OntologyObjectTypeVersion,
            resource=found_object_type,
            page_number=pagination_info.cursor_page,
            active_page=pagination_info.cursor_page,
            last_page=pagination_info.last_page.page,
            collection_size=pagination_info.collection_size,
            item_links=items,
        )

        filter_query_params = {}
        if deleted:
            filter_query_params["deleted"] = deleted

        page_resource.filters = [
            CollectionFilter(
                key="?sort",
                type="sort",
                options=[CollectionFilterOption(value="version")],
            ),
        ]

        if is_admin:
            page_resource.filters.append(
                CollectionFilter(
                    key="?deleted",
                    type="boolean",
                    options=[CollectionFilterOption(value="True")],
                )
            )

        self_link = LinkGenerator.get_link_of(
            page_resource,
            query_params=pagination_options.to_query_params(
                extra_params=filter_query_params
            ),
        )

        extra_links = generate_page_links(
            page_resource,
            pagination_info,
            pagination_options,
            extra_params=filter_query_params,
        )

        return ApiResponseGenerator.get_api_response(
            page_resource,
            query_params=pagination_options.to_query_params(
                extra_params=filter_query_params
            ),
            extra_links=[
                LinkGenerator.get_link_of(
                    page_resource.get_page(1),
                    query_params=pagination_options.to_query_params(
                        cursor=None, extra_params=filter_query_params
                    ),
                ),
                self_link,
                *extra_links,
            ],
            extra_embedded=embedded_items,
            link_to_relations=TYPE_VERSION_PAGE_EXTRA_LINK_RELATIONS,
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
        found_object_type_version: Optional[OntologyObjectTypeVersion] = (
            OntologyObjectTypeVersion.query.filter(
                OntologyObjectTypeVersion.version == version_number,
                OntologyObjectTypeVersion.object_type_id == object_type_id,
            ).first()
        )

        if (
            found_object_type_version is None
            or found_object_type_version.ontology_type.namespace_id != namespace_id
        ):
            abort(HTTPStatus.NOT_FOUND, message=gettext("Object Type version not found."))
        return found_object_type_version  # is not None because abort raises exception

    @API_V1.response(200, DynamicApiResponseSchema(ObjectTypeSchema()))
    @API_V1.alt_response(200, content_type=JSON_SCHEMA_MIMETYPE, success=True)
    @API_V1.require_jwt("jwt")
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

        FLASK_OSO.authorize_and_set_resource(found_object_type_version)

        match = request.accept_mimetypes.best_match(
            (JSON_MIMETYPE, JSON_SCHEMA_MIMETYPE),
            default=JSON_MIMETYPE,
        )

        if match == JSON_SCHEMA_MIMETYPE:
            # only return jsonschema if schema mimetype is requested
            response: Response = jsonify(found_object_type_version.data)
            response.mimetype = JSON_SCHEMA_MIMETYPE
            return response

        return ApiResponseGenerator.get_api_response(
            found_object_type_version, link_to_relations=TYPE_VERSION_EXTRA_LINK_RELATIONS
        )

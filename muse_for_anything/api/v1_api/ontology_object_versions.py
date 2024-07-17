"""Module containing the object API endpoints of the v1 API."""


from http import HTTPStatus
from typing import Any, List, Optional

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
    OBJECT_VERSION_EXTRA_LINK_RELATIONS,
    OBJECT_VERSION_PAGE_EXTRA_LINK_RELATIONS,
    OBJECT_VERSION_REL_TYPE,
)
from muse_for_anything.api.v1_api.request_helpers import (
    ApiResponseGenerator,
    LinkGenerator,
    PageResource,
)
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource

from .models.ontology import ObjectSchema
from .root import API_V1
from ..base_models import (
    CursorPageArgumentsSchema,
    CursorPageSchema,
    DynamicApiResponseSchema,
    CollectionFilter,
    CollectionFilterOption,
)
from ...db.db import DB
from ...db.models.ontology_objects import OntologyObject, OntologyObjectVersion


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
    @API_V1.response(200, DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, object_id: str, **kwargs: Any):
        """Get all versions of an object."""
        self._check_path_params(namespace=namespace, object_id=object_id)
        found_object: OntologyObject = self._get_object(
            namespace=namespace, object_id=object_id
        )
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                OBJECT_VERSION_REL_TYPE,
                is_collection=True,
                parent_resource=found_object,
            )
        )

        pagination_options: PaginationOptions = prepare_pagination_query_args(
            **kwargs, _sort_default="-version"
        )

        object_version_filter = (
            OntologyObjectVersion.deleted_on == None,
            OntologyObjectVersion.ontology_object == found_object,
        )

        pagination_info = default_get_page_info(
            OntologyObjectVersion,
            object_version_filter,
            pagination_options,
            [OntologyObjectVersion.version],
        )

        object_versions: List[
            OntologyObjectVersion
        ] = pagination_info.page_items_query.all()

        embedded_items, items = dump_embedded_page_items(
            object_versions, ObjectSchema(), OBJECT_VERSION_EXTRA_LINK_RELATIONS
        )

        page_resource = PageResource(
            OntologyObjectVersion,
            resource=found_object,
            page_number=pagination_info.cursor_page,
            active_page=pagination_info.cursor_page,
            last_page=pagination_info.last_page.page,
            collection_size=pagination_info.collection_size,
            item_links=items,
        )

        page_resource.filters = [
            CollectionFilter(
                key="?sort",
                type="sort",
                options=[CollectionFilterOption(value="version")],
            ),
        ]

        self_link = LinkGenerator.get_link_of(
            page_resource,
            query_params=pagination_options.to_query_params(),
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
            link_to_relations=OBJECT_VERSION_PAGE_EXTRA_LINK_RELATIONS,
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

    @API_V1.response(200, DynamicApiResponseSchema(ObjectSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, object_id: str, version: str, **kwargs: Any):
        """Get a specific version of an object."""
        self._check_path_params(namespace=namespace, object_id=object_id, version=version)
        found_object_version: OntologyObjectVersion = self._get_object_version(
            namespace=namespace, object_id=object_id, version=version
        )

        FLASK_OSO.authorize_and_set_resource(found_object_version)

        return ApiResponseGenerator.get_api_response(
            found_object_version, link_to_relations=OBJECT_VERSION_EXTRA_LINK_RELATIONS
        )

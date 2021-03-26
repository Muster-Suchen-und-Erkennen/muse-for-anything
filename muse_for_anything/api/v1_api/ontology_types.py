"""Module containing the type API endpoints of the v1 API."""

from datetime import datetime

from marshmallow.utils import INCLUDE
from muse_for_anything.api.v1_api.models.schema import JSONSchemaSchema
from muse_for_anything.api.v1_api.ontology_types_helpers import (
    action_links_for_type,
    action_links_for_type_page,
    create_action_link_for_type_page,
    nav_links_for_type,
    nav_links_for_type_page,
    type_page_params_to_key,
    type_to_api_response,
    type_to_type_data,
    validate_type_schema,
)
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
from .models.ontology import ObjectTypeSchema
from ...db.db import DB
from ...db.pagination import get_page_info
from ...db.models.namespace import Namespace
from ...db.models.ontology_objects import OntologyObjectType, OntologyObjectTypeVersion

from .namespace_helpers import (
    query_params_to_api_key,
)


@API_V1.route("/namespaces/<string:namespace>/types/")
class TypesView(MethodView):
    """Endpoint for all namespace types."""

    def _check_path_params(self, namespace: str):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )

    def _get_namespace(self, namespace: str) -> Namespace:
        namespace_id = int(namespace)
        found_namespace: Optional[Namespace] = Namespace.query.filter(
            Namespace.id == namespace_id
        ).first()

        if found_namespace is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Namespace not found."))
        return found_namespace  # is not None because abort raises exception

    @API_V1.arguments(CursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    def get(self, namespace: str, **kwargs: Any):
        """Get the page of types."""
        self._check_path_params(namespace=namespace)
        found_namespace = self._get_namespace(namespace=namespace)

        cursor: Optional[str] = kwargs.get("cursor", None)
        item_count: int = cast(int, kwargs.get("item_count", 25))
        sort: str = cast(str, kwargs.get("sort", "name").lstrip("+"))
        sort_function: Callable[..., Any] = (
            desc if sort is not None and sort.startswith("-") else asc
        )
        sort_key: str = sort.lstrip("+-") if sort is not None else "name"

        ontology_type_filter = (
            OntologyObjectType.deleted_on == None,
            OntologyObjectType.namespace_id == int(namespace),
        )

        pagination_info = get_page_info(
            OntologyObjectType,
            OntologyObjectType.id,
            [OntologyObjectType.name],
            cursor,
            sort,
            item_count,
            filter_criteria=ontology_type_filter,
        )

        object_types: List[OntologyObjectType] = pagination_info.page_items_query.all()

        embedded_items: List[ApiResponse] = [
            type_to_api_response(object_type) for object_type in object_types
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
                "api-v1.TypesView",
                namespace=namespace,
                _external=True,
                **self_query_params,
            ),
            rel=(
                *self_rels,
                "page",
                f"page-{pagination_info.cursor_page}",
                "collection",
            ),
            resource_type="ont-type",
            resource_key=type_page_params_to_key(namespace, self_query_params),
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
                            "api-v1.TypesView",
                            namespace=namespace,
                            _external=True,
                            **last_query_params,
                        ),
                        rel=(
                            "last",
                            "page",
                            f"page-{pagination_info.last_page.page}",
                            "collection",
                        ),
                        resource_type="ont-type",
                        resource_key=type_page_params_to_key(
                            namespace, last_query_params
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
                        "api-v1.TypesView",
                        namespace=namespace,
                        _external=True,
                        **page_query_params,
                    ),
                    rel=(
                        *extra_rels,
                        "page",
                        f"page-{page.page}",
                        "collection",
                    ),
                    resource_type="ont-type",
                    resource_key=type_page_params_to_key(namespace, page_query_params),
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="OntologyType", _external=True
                    ),
                )
            )

        extra_links.extend(nav_links_for_type_page(namespace))

        extra_links.extend(action_links_for_type_page(found_namespace))

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
                        "api-v1.TypesView",
                        namespace=namespace,
                        _external=True,
                        **query_params,
                    ),
                    rel=("first", "page", "page-1", "collection"),
                    resource_type="ont-type",
                    resource_key=type_page_params_to_key(namespace, query_params),
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

    @API_V1.arguments(JSONSchemaSchema(unknown=INCLUDE))
    @API_V1.response(DynamicApiResponseSchema(NewApiObjectSchema()))
    def post(self, data, namespace: str):
        """Create a new type."""
        self._check_path_params(namespace=namespace)
        validate_type_schema(data)
        # FIXME add proper introspection to get linked types out of the schema
        is_abstract: bool = data.get("abstract", False)
        title: str = data.get("title", "")
        description: str = data.get("description", "")

        found_namespace = self._get_namespace(namespace=namespace)
        if found_namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )

        object_type = OntologyObjectType(
            namespace=found_namespace,
            name=title,
            description=description,
            is_top_level_type=(not is_abstract),
        )
        DB.session.add(object_type)
        DB.session.flush()
        object_type_version = OntologyObjectTypeVersion(
            ontology_type=object_type, version=1, data=data
        )
        object_type.current_version = object_type_version
        DB.session.add(object_type)
        DB.session.add(object_type_version)
        DB.session.commit()

        object_type_link = type_to_type_data(object_type).self
        object_type_data = type_to_api_response(object_type)

        self_link = create_action_link_for_type_page(namespace=namespace)
        self_link.rel = (*self_link.rel, "ont-type")
        self_link.resource_type = "new"

        return ApiResponse(
            links=[object_type_link],
            embedded=[object_type_data],
            data=NewApiObject(
                self=self_link,
                new=object_type_link,
            ),
        )


@API_V1.route("/namespaces/<string:namespace>/types/<string:object_type>/")
class TypeView(MethodView):
    """Endpoint a single object type resource."""

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

    def _check_if_namespace_modifiable(self, object_type: OntologyObjectType):
        if object_type.namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )

    def _check_if_modifiable(self, object_type: OntologyObjectType):
        self._check_if_namespace_modifiable(object_type=object_type)
        if object_type.deleted_on is not None:
            # cannot modify deleted type!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Object Type is marked as deleted and cannot be modified further."
                ),
            )

    @API_V1.response(DynamicApiResponseSchema(ObjectTypeSchema()))
    def get(self, namespace: str, object_type: str, **kwargs: Any):
        """Get a single type."""
        self._check_path_params(namespace=namespace, object_type=object_type)
        found_object_type: OntologyObjectType = self._get_object_type(
            namespace=namespace, object_type=object_type
        )

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for(
                        "api-v1.NamespacesView",
                        _external=True,
                        **{"item-count": 50},
                        sort="name",
                    ),
                    rel=("first", "page", "collection", "nav"),
                    resource_type="ont-namespace",
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                *nav_links_for_type(found_object_type),
                *action_links_for_type(found_object_type),
            ],
            data=type_to_type_data(found_object_type),
        )

    @API_V1.arguments(JSONSchemaSchema(unknown=INCLUDE))
    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def put(self, data, namespace: str, object_type: str):
        """Update type (creates a new version)."""
        validate_type_schema(data)
        # FIXME add proper introspection to get linked types out of the schema and type compatibility
        self._check_path_params(namespace=namespace, object_type=object_type)
        found_object_type: OntologyObjectType = self._get_object_type(
            namespace=namespace, object_type=object_type
        )
        self._check_if_modifiable(found_object_type)

        object_type_version = OntologyObjectTypeVersion(
            ontology_type=found_object_type,
            version=found_object_type.version + 1,
            data=data,
        )
        found_object_type.update(
            name=object_type_version.name,
            description=object_type_version.description,
            is_top_level_type=not object_type_version.abstract,
        )
        found_object_type.current_version = object_type_version
        DB.session.add(object_type_version)
        DB.session.add(found_object_type)
        DB.session.commit()

        object_type_link = type_to_type_data(found_object_type).self
        object_type_data = type_to_api_response(found_object_type)

        return ApiResponse(
            links=[object_type_link],
            embedded=[object_type_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.TypeView",
                        namespace=namespace,
                        object_type=object_type,
                        _external=True,
                    ),
                    rel=(
                        "update",
                        "put",
                        "ont-type",
                    ),
                    resource_type="changed",
                ),
                changed=object_type_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def post(self, namespace: str, object_type: str):  # restore action
        """Restore a deleted type."""
        self._check_path_params(namespace=namespace, object_type=object_type)
        found_object_type: OntologyObjectType = self._get_object_type(
            namespace=namespace, object_type=object_type
        )
        self._check_if_namespace_modifiable(object_type=found_object_type)

        # only actually restore when not already restored
        if found_object_type.deleted_on is not None:
            # restore object type
            found_object_type.deleted_on = None
            DB.session.add(found_object_type)
            DB.session.commit()

        object_type_link = type_to_type_data(found_object_type).self
        object_type_data = type_to_api_response(found_object_type)

        return ApiResponse(
            links=[object_type_link],
            embedded=[object_type_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.TypeView",
                        namespace=namespace,
                        object_type=object_type,
                        _external=True,
                    ),
                    rel=(
                        "restore",
                        "post",
                        "ont-type",
                    ),
                    resource_type="changed",
                ),
                changed=object_type_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def delete(self, namespace: str, object_type: str):
        """Delete a type."""
        self._check_path_params(namespace=namespace, object_type=object_type)
        found_object_type: OntologyObjectType = self._get_object_type(
            namespace=namespace, object_type=object_type
        )
        self._check_if_namespace_modifiable(object_type=found_object_type)

        # only actually delete when not already deleted
        if found_object_type.deleted_on is None:
            # soft delete namespace
            found_object_type.deleted_on = datetime.utcnow()
            DB.session.add(found_object_type)
            DB.session.commit()

        object_type_link = type_to_type_data(found_object_type).self
        object_type_data = type_to_api_response(found_object_type)

        return ApiResponse(
            links=[object_type_link],
            embedded=[object_type_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.TypeView",
                        namespace=namespace,
                        object_type=object_type,
                        _external=True,
                    ),
                    rel=(
                        "delete",
                        "ont-type",
                    ),
                    resource_type="changed",
                ),
                changed=object_type_link,
            ),
        )

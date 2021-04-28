"""Module containing the object API endpoints of the v1 API."""

from datetime import datetime

from marshmallow.utils import INCLUDE
from muse_for_anything.api.v1_api.models.schema import JSONSchemaSchema
from muse_for_anything.api.v1_api.ontology_types_helpers import (
    create_action_link_for_type_page,
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
from .models.ontology import (
    ObjectSchema,
    ObjectTypeSchema,
    ObjectsCursorPageArgumentsSchema,
)
from ...db.db import DB
from ...db.pagination import get_page_info
from ...db.models.namespace import Namespace
from ...db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectType,
    OntologyObjectTypeVersion,
    OntologyObjectVersion,
)

from .namespace_helpers import (
    query_params_to_api_key,
)

from muse_for_anything.api.v1_api.ontology_object_helpers import (
    action_links_for_object,
    action_links_for_object_page,
    nav_links_for_object,
    object_page_params_to_key,
    object_to_api_response,
    nav_links_for_object_page,
    object_to_object_data,
    validate_object_schema,
)


@API_V1.route("/namespaces/<string:namespace>/objects/")
class ObjectsView(MethodView):
    """Endpoint for all objects of a namespace."""

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

    def _check_type_param(self, type_id: str):
        if not type_id or not type_id.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested type id has the wrong format!"),
            )

    def _get_ontology_type(self, namespace: str, type_id: str) -> OntologyObjectType:
        namespace_id = int(namespace)
        object_type_id = int(type_id)
        found_type: Optional[OntologyObjectType] = OntologyObjectType.query.filter(
            OntologyObjectType.id == object_type_id,
            OntologyObjectType.namespace_id == namespace_id,
        ).first()

        if found_type is None:
            abort(HTTPStatus.NOT_FOUND, message=gettext("Object type not found."))
        return found_type  # is not None because abort raises exception

    @API_V1.arguments(ObjectsCursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.response(DynamicApiResponseSchema(CursorPageSchema()))
    def get(self, namespace: str, **kwargs: Any):
        """Get the page of objects."""
        self._check_path_params(namespace=namespace)
        found_namespace = self._get_namespace(namespace=namespace)

        cursor: Optional[str] = kwargs.get("cursor", None)
        item_count: int = cast(int, kwargs.get("item_count", 25))
        sort: str = cast(str, kwargs.get("sort", "name").lstrip("+"))

        ontology_object_filter = (
            OntologyObject.deleted_on == None,
            OntologyObject.namespace_id == int(namespace),
        )

        found_type: Optional[OntologyObjectType] = None
        if "type_id" in kwargs:
            type_id: str = kwargs.get("type_id")
            self._check_type_param(type_id=type_id)
            found_type = self._get_ontology_type(namespace=namespace, type_id=type_id)
            ontology_object_filter = (
                *ontology_object_filter,
                OntologyObject.object_type_id == found_type.id,
            )

        pagination_info = get_page_info(
            OntologyObject,
            OntologyObject.id,
            [OntologyObject.name],
            cursor,
            sort,
            item_count,
            filter_criteria=ontology_object_filter,
        )

        objects: List[OntologyObject] = pagination_info.page_items_query.all()

        embedded_items: List[ApiResponse] = [
            object_to_api_response(object) for object in objects
        ]
        items: List[ApiLink] = [item.data.get("self") for item in embedded_items]

        query_params = {
            "item-count": item_count,
            "sort": sort,
        }

        if found_type is not None:
            query_params["type-id"] = str(found_type.id)

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
                "api-v1.ObjectsView",
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
            resource_type="ont-object",
            resource_key=object_page_params_to_key(namespace, self_query_params),
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
                            "api-v1.ObjectsView",
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
                        resource_type="ont-object",
                        resource_key=object_page_params_to_key(
                            namespace, last_query_params
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
                        "api-v1.ObjectsView",
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
                    resource_type="ont-object",
                    resource_key=object_page_params_to_key(namespace, page_query_params),
                )
            )

        extra_links.extend(nav_links_for_object_page(found_namespace))

        extra_links.extend(action_links_for_object_page(found_namespace, type=found_type))

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
                        "api-v1.ObjectsView",
                        namespace=namespace,
                        _external=True,
                        **query_params,
                    ),
                    rel=("first", "page", "page-1", "collection"),
                    resource_type="ont-object",
                    resource_key=object_page_params_to_key(namespace, query_params),
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

    @API_V1.arguments(ObjectsCursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.arguments(ObjectSchema())
    @API_V1.response(DynamicApiResponseSchema(NewApiObjectSchema()))
    def post(self, data, namespace: str, **kwargs):
        """Create a new object."""
        self._check_path_params(namespace=namespace)
        self._check_type_param(type_id=kwargs.get("type_id"))

        found_namespace = self._get_namespace(namespace=namespace)
        if found_namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )

        found_object_type = self._get_ontology_type(
            namespace=namespace, type_id=kwargs.get("type_id")
        )
        if found_object_type.deleted_on is not None:
            # cannot modify deleted object type!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Object type is marked as deleted. No new Objects of this type can be created!"
                ),
            )

        validate_object_schema(object_data=data.get("data"), type=found_object_type)

        name = data.get("name")
        description = data.get("description", "")

        object = OntologyObject(
            namespace=found_namespace,
            ontology_type=found_object_type,
            name=name,
            description=description,
        )
        DB.session.add(object)
        DB.session.flush()
        object_version = OntologyObjectVersion(
            object=object,
            type_version=found_object_type.current_version,
            version=1,
            name=name,
            description=description,
            data=data.get("data"),
        )
        object.current_version = object_version
        DB.session.add(object)
        DB.session.add(object_version)
        DB.session.commit()

        object_link = object_to_object_data(object).self
        object_data = object_to_api_response(object)

        self_link = create_action_link_for_type_page(namespace=found_namespace)
        self_link.rel = (*self_link.rel, "ont-object")
        self_link.resource_type = "new"

        return ApiResponse(
            links=[object_link],
            embedded=[object_data],
            data=NewApiObject(
                self=self_link,
                new=object_link,
            ),
        )


@API_V1.route("/namespaces/<string:namespace>/objects/<string:object_id>/")
class ObjectView(MethodView):
    """Endpoint a single object resource."""

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

    def _check_if_namespace_and_type_modifiable(self, object: OntologyObject):
        if object.namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )
        if object.ontology_type.deleted_on is not None:
            # cannot modify deleted object type!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Object type is marked as deleted and objects of that type cannot be modified further."
                ),
            )

    def _check_if_modifiable(self, object: OntologyObject):
        self._check_if_namespace_and_type_modifiable(object=object)
        if object.deleted_on is not None:
            # cannot modify deleted type!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Object is marked as deleted and cannot be modified further."
                ),
            )

    @API_V1.response(DynamicApiResponseSchema(ObjectSchema()))
    def get(self, namespace: str, object_id: str, **kwargs: Any):
        """Get a single object."""
        self._check_path_params(namespace=namespace, object_id=object_id)
        found_object: OntologyObject = self._get_object(
            namespace=namespace, object_id=object_id
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
                *nav_links_for_object(found_object),
                *action_links_for_object(found_object),
            ],
            data=object_to_object_data(found_object),
        )

    @API_V1.arguments(ObjectSchema())
    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def put(self, data, namespace: str, object_id: str):
        """Update object (creates a new version)."""
        # FIXME add validation… validate_type_schema(data)
        # FIXME add proper introspection to get linked types out of the schema and type compatibility
        self._check_path_params(namespace=namespace, object_id=object_id)
        found_object: OntologyObject = self._get_object(
            namespace=namespace, object_id=object_id
        )
        self._check_if_modifiable(found_object)

        validate_object_schema(
            object_data=data.get("data"), type=found_object.ontology_type
        )

        name = data.get("name")
        description = data.get("description", "")

        object_version = OntologyObjectVersion(
            object=found_object,
            type_version=found_object.ontology_type.current_version,
            version=found_object.version + 1,
            name=name,
            description=description,
            data=data.get("data"),
        )
        found_object.update(
            name=name,
            description=description,
        )
        found_object.current_version = object_version
        DB.session.add(object_version)
        DB.session.add(found_object)
        DB.session.commit()

        object_link = object_to_object_data(found_object).self
        object_data = object_to_api_response(found_object)

        return ApiResponse(
            links=[object_link],
            embedded=[object_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.ObjectView",
                        namespace=namespace,
                        object_id=object_id,
                        _external=True,
                    ),
                    rel=(
                        "update",
                        "put",
                        "ont-object",
                    ),
                    resource_type="changed",
                ),
                changed=object_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def post(self, namespace: str, object_id: str):  # restore action
        """Restore a deleted object."""
        self._check_path_params(namespace=namespace, object_id=object_id)
        found_object: OntologyObject = self._get_object(
            namespace=namespace, object_id=object_id
        )
        self._check_if_namespace_and_type_modifiable(object=found_object)

        # only actually restore when not already restored
        if found_object.deleted_on is not None:
            # restore object
            found_object.deleted_on = None
            DB.session.add(found_object)
            DB.session.commit()

        object_link = object_to_object_data(found_object).self
        object_data = object_to_api_response(found_object)

        return ApiResponse(
            links=[object_link],
            embedded=[object_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.ObjectView",
                        namespace=namespace,
                        object_id=object_id,
                        _external=True,
                    ),
                    rel=(
                        "restore",
                        "post",
                        "ont-object",
                    ),
                    resource_type="changed",
                ),
                changed=object_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def delete(self, namespace: str, object_id: str):
        """Delete an object."""
        self._check_path_params(namespace=namespace, object_id=object_id)
        found_object: OntologyObject = self._get_object(
            namespace=namespace, object_id=object_id
        )
        self._check_if_namespace_and_type_modifiable(object=found_object)

        # only actually delete when not already deleted
        if found_object.deleted_on is None:
            # soft delete object
            found_object.deleted_on = datetime.utcnow()
            # TODO soft delete komposition objects (also implement undelete…)
            DB.session.add(found_object)
            DB.session.commit()

        object_link = object_to_object_data(found_object).self
        object_data = object_to_api_response(found_object)

        return ApiResponse(
            links=[object_link],
            embedded=[object_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.ObjectView",
                        namespace=namespace,
                        object_id=object_id,
                        _external=True,
                    ),
                    rel=(
                        "delete",
                        "ont-object",
                    ),
                    resource_type="changed",
                ),
                changed=object_link,
            ),
        )

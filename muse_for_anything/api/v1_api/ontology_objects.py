"""Module containing the object API endpoints of the v1 API."""

from datetime import datetime
from http import HTTPStatus
from typing import Any, List, Optional

from flask.globals import g
from flask.views import MethodView
from flask_babel import gettext
from flask_smorest import abort
from marshmallow.utils import INCLUDE
from sqlalchemy.sql.expression import or_

from muse_for_anything.api.pagination_util import (
    PaginationOptions,
    default_get_page_info,
    dump_embedded_page_items,
    generate_page_links,
    prepare_pagination_query_args,
)
from muse_for_anything.api.v1_api.constants import (
    CHANGED_REL,
    CREATE,
    CREATE_REL,
    DELETE_REL,
    NEW_REL,
    OBJECT_EXTRA_LINK_RELATIONS,
    OBJECT_PAGE_EXTRA_LINK_RELATIONS,
    OBJECT_REL_TYPE,
    RESTORE,
    RESTORE_REL,
    TYPE_EXTRA_ARG,
    TYPE_ID_QUERY_KEY,
    UPDATE,
    UPDATE_REL,
)
from muse_for_anything.api.v1_api.ontology_object_validation import validate_object
from muse_for_anything.api.v1_api.request_helpers import (
    ApiResponseGenerator,
    LinkGenerator,
    PageResource,
)
from muse_for_anything.db.models.object_relation_tables import (
    OntologyObjectVersionToObject,
    OntologyObjectVersionToTaxonomyItem,
)
from muse_for_anything.db.models.users import User
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource

from ...db.db import DB
from ...db.models.namespace import Namespace
from ...db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectType,
    OntologyObjectVersion,
)
from ..base_models import (
    ApiResponse,
    ChangedApiObject,
    ChangedApiObjectSchema,
    CollectionFilter,
    CollectionFilterOption,
    CursorPageSchema,
    DynamicApiResponseSchema,
    NewApiObject,
    NewApiObjectSchema,
)

# import object specific generators to load them
from .generators import object as object_  # noqa
from .generators import object_version  # noqa
from .models.ontology import ObjectSchema, ObjectsCursorPageArgumentsSchema
from .root import API_V1


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

    def _check_type_param(self, type_id: Optional[str]):
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
    @API_V1.response(200, DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, search: Optional[str] = None, **kwargs: Any):
        """Get the page of objects."""
        self._check_path_params(namespace=namespace)
        found_namespace = self._get_namespace(namespace=namespace)

        found_type: Optional[OntologyObjectType] = None

        if "type_id" in kwargs:
            type_id: Optional[str] = kwargs.pop("type_id")
            self._check_type_param(type_id=type_id)
            found_type = self._get_ontology_type(namespace=namespace, type_id=type_id)

        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                OBJECT_REL_TYPE,
                is_collection=True,
                parent_resource=found_namespace,
                arguments={TYPE_EXTRA_ARG: found_type} if found_type else None,
            )
        )

        pagination_options: PaginationOptions = prepare_pagination_query_args(
            **kwargs, _sort_default="name"
        )

        ontology_object_filter = (
            OntologyObject.deleted_on == None,
            OntologyObject.namespace_id == int(namespace),
        )

        if found_type:
            ontology_object_filter = (
                *ontology_object_filter,
                OntologyObject.object_type_id == found_type.id,
            )
            pagination_options.extra_query_params = {
                TYPE_ID_QUERY_KEY: str(found_type.id),
            }

        if search:
            ontology_object_filter = (
                *ontology_object_filter,
                or_(
                    # TODO switch from contains to match depending on DB...
                    OntologyObject.name.contains(search),
                    OntologyObject.description.contains(search),
                ),
            )

        pagination_info = default_get_page_info(
            OntologyObject,
            ontology_object_filter,
            pagination_options,
            [
                OntologyObject.name,
                OntologyObject.created_on,
                OntologyObject.updated_on,
                OntologyObject.object_type_id,
            ],
        )

        objects: List[OntologyObject] = pagination_info.page_items_query.all()

        embedded_items, items = dump_embedded_page_items(
            objects, ObjectSchema(), OBJECT_EXTRA_LINK_RELATIONS
        )

        page_resource = PageResource(
            OntologyObject,
            resource=found_namespace,
            page_number=pagination_info.cursor_page,
            active_page=pagination_info.cursor_page,
            last_page=pagination_info.last_page.page,
            collection_size=pagination_info.collection_size,
            item_links=items,
            extra_arguments={TYPE_EXTRA_ARG: found_type} if found_type else {},
        )

        filter_query_params = {}
        if search:
            filter_query_params["search"] = search

        sort_options = [
            CollectionFilterOption("name"),
            CollectionFilterOption("created_on"),
            CollectionFilterOption("updated_on"),
        ]

        if found_type is None:
            # sort by type is only useful if not already filtered by type
            sort_options.append(CollectionFilterOption("object_type_id"))

        page_resource.filters = [
            CollectionFilter(key="?search", type="search"),
            CollectionFilter(
                key="?sort",
                type="sort",
                options=sort_options,
            ),
        ]

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
            link_to_relations=OBJECT_PAGE_EXTRA_LINK_RELATIONS,
        )

    @API_V1.arguments(ObjectsCursorPageArgumentsSchema, location="query", as_kwargs=True)
    @API_V1.arguments(ObjectSchema())
    @API_V1.response(200, DynamicApiResponseSchema(NewApiObjectSchema()))
    @API_V1.require_jwt("jwt")
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
        if not found_object_type.is_toplevel_type:
            # can only create objects for non abstract top level object type!
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext(
                    "Object type is marked as abstract. No Objects of this type can be created!"
                ),
            )

        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                OBJECT_REL_TYPE,
                parent_resource=found_namespace,
                arguments={TYPE_EXTRA_ARG: found_object_type},
            ),
            action=CREATE,
        )

        name = data.get("name")
        description = data.get("description", "")

        object_ = OntologyObject(
            namespace=found_namespace,
            ontology_type=found_object_type,
            name=name,
            description=description,
        )
        object_version = OntologyObjectVersion(
            object=object_,
            type_version=found_object_type.current_version,
            version=1,
            name=name,
            description=description,
            data=data.get("data"),
        )

        # validate against object type and validate and extract resource references
        metadata = validate_object(
            object_version=object_version, type_version=found_object_type.current_version
        )

        # add object to session and flush to prevent circular references
        DB.session.add(object_)
        DB.session.flush()

        object_.current_version = object_version

        # object is flushed, safe to add user rights here
        user: User = g.current_user
        user.set_role_for_resource("owner", object_)

        DB.session.add(object_)
        DB.session.add(object_version)

        # add references
        for object_ref in metadata.referenced_objects:
            object_relation = OntologyObjectVersionToObject(
                object_version_source=object_version, object_target=object_ref
            )
            DB.session.add(object_relation)
        for taxonomy_item in metadata.referenced_taxonomy_items:
            taxonomy_item_relation = OntologyObjectVersionToTaxonomyItem(
                object_version_source=object_version, taxonomy_item_target=taxonomy_item
            )
            DB.session.add(taxonomy_item_relation)

        DB.session.commit()

        object_response = ApiResponseGenerator.get_api_response(
            object_, link_to_relations=OBJECT_EXTRA_LINK_RELATIONS
        )
        object_link = object_response.data.self
        object_response.data = ObjectSchema().dump(object_response.data)

        self_link = LinkGenerator.get_link_of(
            PageResource(OntologyObjectType, resource=found_namespace),
            for_relation=CREATE_REL,
            extra_relations=(OBJECT_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = NEW_REL

        return ApiResponse(
            links=[object_link],
            embedded=[object_response],
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

    @API_V1.response(200, DynamicApiResponseSchema(ObjectSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, object_id: str, **kwargs: Any):
        """Get a single object."""
        self._check_path_params(namespace=namespace, object_id=object_id)
        found_object: OntologyObject = self._get_object(
            namespace=namespace, object_id=object_id
        )
        FLASK_OSO.authorize_and_set_resource(found_object)

        # TODO embed referenced objects, types and taxonomies?

        return ApiResponseGenerator.get_api_response(
            found_object, link_to_relations=OBJECT_EXTRA_LINK_RELATIONS
        )

    @API_V1.arguments(ObjectSchema())
    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def put(self, data, namespace: str, object_id: str):
        """Update object (creates a new version)."""
        self._check_path_params(namespace=namespace, object_id=object_id)
        found_object: OntologyObject = self._get_object(
            namespace=namespace, object_id=object_id
        )
        self._check_if_modifiable(found_object)

        FLASK_OSO.authorize_and_set_resource(found_object, action=UPDATE)

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

        # validate against object type and validate and extract resource references
        metadata = validate_object(
            object_version=object_version,
            type_version=found_object.ontology_type.current_version,
        )

        # add references
        for object_ref in metadata.referenced_objects:
            object_relation = OntologyObjectVersionToObject(
                object_version_source=object_version, object_target=object_ref
            )
            DB.session.add(object_relation)
        for taxonomy_item in metadata.referenced_taxonomy_items:
            taxonomy_item_relation = OntologyObjectVersionToTaxonomyItem(
                object_version_source=object_version, taxonomy_item_target=taxonomy_item
            )
            DB.session.add(taxonomy_item_relation)

        # update existing object
        found_object.update(
            name=name,
            description=description,
        )
        found_object.current_version = object_version
        DB.session.add(object_version)
        DB.session.add(found_object)
        DB.session.commit()

        object_response = ApiResponseGenerator.get_api_response(
            found_object, link_to_relations=OBJECT_EXTRA_LINK_RELATIONS
        )
        object_link = object_response.data.self
        object_response.data = ObjectSchema().dump(object_response.data)

        self_link = LinkGenerator.get_link_of(
            found_object,
            for_relation=UPDATE_REL,
            extra_relations=(OBJECT_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[object_link],
            embedded=[object_response],
            data=ChangedApiObject(
                self=self_link,
                changed=object_link,
            ),
        )

    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def post(self, namespace: str, object_id: str):  # restore action
        """Restore a deleted object."""
        self._check_path_params(namespace=namespace, object_id=object_id)
        found_object: OntologyObject = self._get_object(
            namespace=namespace, object_id=object_id
        )
        self._check_if_namespace_and_type_modifiable(object=found_object)

        FLASK_OSO.authorize_and_set_resource(found_object, action=RESTORE)

        # only actually restore when not already restored
        if found_object.deleted_on is not None:
            # restore object
            found_object.deleted_on = None
            DB.session.add(found_object)
            DB.session.commit()

        object_response = ApiResponseGenerator.get_api_response(
            found_object, link_to_relations=OBJECT_EXTRA_LINK_RELATIONS
        )
        object_link = object_response.data.self
        object_response.data = ObjectSchema().dump(object_response.data)

        self_link = LinkGenerator.get_link_of(
            found_object,
            for_relation=RESTORE_REL,
            extra_relations=(OBJECT_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[object_link],
            embedded=[object_response],
            data=ChangedApiObject(
                self=self_link,
                changed=object_link,
            ),
        )

    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
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

        object_response = ApiResponseGenerator.get_api_response(
            found_object, link_to_relations=OBJECT_EXTRA_LINK_RELATIONS
        )
        object_link = object_response.data.self
        object_response.data = ObjectSchema().dump(object_response.data)

        self_link = LinkGenerator.get_link_of(
            found_object,
            for_relation=DELETE_REL,
            extra_relations=(OBJECT_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[object_link],
            embedded=[object_response],
            data=ChangedApiObject(
                self=self_link,
                changed=object_link,
            ),
        )

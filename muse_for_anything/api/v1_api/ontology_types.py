"""Module containing the type API endpoints of the v1 API."""

from datetime import datetime, timezone
from celery import group
from flask import request
from http import HTTPStatus
from typing import Any, List, Optional

from flask.globals import g
from flask.views import MethodView
from flask_babel import gettext
from flask_smorest import abort
from marshmallow.utils import INCLUDE
from sqlalchemy.sql.expression import or_, select

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
    RESTORE,
    RESTORE_REL,
    TYPE_EXTRA_LINK_RELATIONS,
    TYPE_PAGE_EXTRA_LINK_RELATIONS,
    TYPE_REL_TYPE,
    UPDATE,
    UPDATE_REL,
)
from muse_for_anything.api.v1_api.models.schema import JSONSchemaSchema
from muse_for_anything.api.v1_api.ontology_type_validation import validate_object_type
from muse_for_anything.api.v1_api.request_helpers import (
    ApiResponseGenerator,
    LinkGenerator,
    PageResource,
)
from muse_for_anything.db.models.users import User
from muse_for_anything.json_migrations.jsonschema_validator import validate_schema
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource
from muse_for_anything.tasks.migration import run_migration

from .generators import type_version  # noqa
from .models.ontology import ObjectTypePageParamsSchema, ObjectTypeSchema
from .root import API_V1
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
from ...db.db import DB
from ...db.models.namespace import Namespace
from ...db.models.object_relation_tables import (
    OntologyTypeVersionToTaxonomy,
    OntologyTypeVersionToType,
    OntologyTypeVersionToTypeVersion,
)
from ...db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectType,
    OntologyObjectTypeVersion,
)

# import type specific generators to load them
from .generators import type as type_  # noqa


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

    @API_V1.arguments(ObjectTypePageParamsSchema, location="query", as_kwargs=True)
    @API_V1.response(200, DynamicApiResponseSchema(CursorPageSchema()))
    @API_V1.require_jwt("jwt")
    def get(
        self,
        namespace: str,
        search: Optional[str] = None,
        deleted: bool = False,
        **kwargs: Any,
    ):
        """Get the page of types."""
        self._check_path_params(namespace=namespace)
        found_namespace = self._get_namespace(namespace=namespace)
        FLASK_OSO.authorize_and_set_resource(
            OsoResource(
                TYPE_REL_TYPE, is_collection=True, parent_resource=found_namespace
            )
        )

        pagination_options: PaginationOptions = prepare_pagination_query_args(
            **kwargs, _sort_default="name"
        )

        is_admin = FLASK_OSO.is_admin()

        if deleted and not is_admin:
            deleted = False

        ontology_type_filter = (
            (
                OntologyObjectType.deleted_on == None
                if not deleted
                else OntologyObjectType.deleted_on != None
            ),
            OntologyObjectType.namespace_id == int(namespace),
        )

        if search:
            ontology_type_filter = (
                *ontology_type_filter,
                or_(
                    # TODO switch from contains to match depending on DB...
                    OntologyObjectType.name.contains(search),
                    OntologyObjectType.description.contains(search),
                ),
            )

        pagination_info = default_get_page_info(
            OntologyObjectType,
            ontology_type_filter,
            pagination_options,
            [
                OntologyObjectType.name,
                OntologyObjectType.created_on,
                OntologyObjectType.updated_on,
            ],
        )

        object_types: List[OntologyObjectType] = pagination_info.page_items_query.all()

        embedded_items, items = dump_embedded_page_items(
            object_types, ObjectTypeSchema(), TYPE_EXTRA_LINK_RELATIONS
        )

        page_resource = PageResource(
            OntologyObjectType,
            resource=found_namespace,
            page_number=pagination_info.cursor_page,
            active_page=pagination_info.cursor_page,
            last_page=pagination_info.last_page.page,
            collection_size=pagination_info.collection_size,
            item_links=items,
        )

        filter_query_params = {}
        if search:
            filter_query_params["search"] = search
        if deleted:
            filter_query_params["deleted"] = deleted

        self_link = LinkGenerator.get_link_of(
            page_resource,
            query_params=pagination_options.to_query_params(
                extra_params=filter_query_params
            ),
        )

        page_resource.filters = [
            CollectionFilter(key="?search", type="search"),
            CollectionFilter(
                key="?sort",
                type="sort",
                options=[
                    CollectionFilterOption("name"),
                    CollectionFilterOption("created_on"),
                    CollectionFilterOption("updated_on"),
                ],
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
            link_to_relations=TYPE_PAGE_EXTRA_LINK_RELATIONS,
        )

    @API_V1.arguments(JSONSchemaSchema(unknown=INCLUDE))
    @API_V1.response(200, DynamicApiResponseSchema(NewApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def post(self, data, namespace: str):
        """Create a new type."""
        self._check_path_params(namespace=namespace)
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

        FLASK_OSO.authorize_and_set_resource(
            OsoResource(TYPE_REL_TYPE, parent_resource=found_namespace), action=CREATE
        )

        object_type = OntologyObjectType(
            namespace=found_namespace,
            name=title,
            description=description,
            is_top_level_type=(not is_abstract),
        )
        object_type_version = OntologyObjectTypeVersion(
            ontology_type=object_type, version=1, data=data
        )

        # validate and extract references
        metadata = validate_object_type(object_type_version)

        # flush object type to db to prevent circular references
        DB.session.add(object_type)
        DB.session.flush()

        object_type.current_version = object_type_version

        # object_type is flushed, safe to add user rights here
        user: User = g.current_user
        user.set_role_for_resource("owner", object_type)

        DB.session.add(object_type)
        DB.session.add(object_type_version)

        # add references to session
        for type_version in metadata.imported_types:
            import_relation = OntologyTypeVersionToTypeVersion(
                type_version_source=object_type_version, type_version_target=type_version
            )
            DB.session.add(import_relation)
        for type_ref in metadata.referenced_types:
            type_relation = OntologyTypeVersionToType(
                type_version_source=object_type_version, type_target=type_ref
            )
            DB.session.add(type_relation)
        for taxonomy in metadata.referenced_taxonomies:
            taxonomy_relation = OntologyTypeVersionToTaxonomy(
                type_version_source=object_type_version, taxonomy_target=taxonomy
            )
            DB.session.add(taxonomy_relation)

        DB.session.commit()

        object_type_response = ApiResponseGenerator.get_api_response(
            object_type, link_to_relations=TYPE_EXTRA_LINK_RELATIONS
        )
        object_type_link = object_type_response.data.self
        object_type_response.data = ObjectTypeSchema().dump(object_type_response.data)

        self_link = LinkGenerator.get_link_of(
            PageResource(OntologyObjectType, resource=found_namespace),
            for_relation=CREATE_REL,
            extra_relations=(TYPE_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = NEW_REL

        return ApiResponse(
            links=[object_type_link],
            embedded=[object_type_response],
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

    @API_V1.response(200, DynamicApiResponseSchema(ObjectTypeSchema()))
    @API_V1.require_jwt("jwt")
    def get(self, namespace: str, object_type: str, **kwargs: Any):
        """Get a single type."""
        self._check_path_params(namespace=namespace, object_type=object_type)
        found_object_type: OntologyObjectType = self._get_object_type(
            namespace=namespace, object_type=object_type
        )
        FLASK_OSO.authorize_and_set_resource(found_object_type)

        # TODO embed referenced types and taxonomies?

        return ApiResponseGenerator.get_api_response(
            found_object_type, link_to_relations=TYPE_EXTRA_LINK_RELATIONS
        )

    @API_V1.arguments(JSONSchemaSchema(unknown=INCLUDE))
    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def put(self, data, namespace: str, object_type: str):
        """Update type (creates a new version)."""
        self._check_path_params(namespace=namespace, object_type=object_type)
        found_object_type: OntologyObjectType = self._get_object_type(
            namespace=namespace, object_type=object_type
        )
        self._check_if_modifiable(found_object_type)

        FLASK_OSO.authorize_and_set_resource(found_object_type, action=UPDATE)

        # Check if update is valid
        valid = validate_schema(
            source_schema=found_object_type.current_version.data,
            target_schema=data,
        )
        if not valid:
            # TODO Handle error in UI
            raise ValueError("Type conversion is not supported!")

        object_type_version = OntologyObjectTypeVersion(
            ontology_type=found_object_type,
            version=found_object_type.version + 1,
            data=data,
        )
        # validate schema and references and extract references
        metadata = validate_object_type(object_type_version)

        # add references to session
        for type_version in metadata.imported_types:
            import_relation = OntologyTypeVersionToTypeVersion(
                type_version_source=object_type_version, type_version_target=type_version
            )
            DB.session.add(import_relation)
        for type_ref in metadata.referenced_types:
            type_relation = OntologyTypeVersionToType(
                type_version_source=object_type_version, type_target=type_ref
            )
            DB.session.add(type_relation)
        for taxonomy in metadata.referenced_taxonomies:
            taxonomy_relation = OntologyTypeVersionToTaxonomy(
                type_version_source=object_type_version, taxonomy_target=taxonomy
            )
            DB.session.add(taxonomy_relation)

        # update object type
        found_object_type.update(
            name=object_type_version.name,
            description=object_type_version.description,
            is_top_level_type=not object_type_version.abstract,
        )
        found_object_type.current_version = object_type_version
        DB.session.add(object_type_version)
        DB.session.add(found_object_type)
        DB.session.commit()

        # Start migration on all objects of updated type
        q = (
            select(OntologyObject.id)
            .where(OntologyObject.namespace_id == namespace)
            .where(OntologyObject.object_type_id == found_object_type.id)
            .where(OntologyObject.deleted_on == None)
        )

        host_url = request.host_url
        data_objects_ids = DB.session.execute(q).scalars().all()
        task_group = group(
            run_migration.s(data_object_id, host_url)
            for data_object_id in data_objects_ids
        )
        task_group.apply_async()

        object_type_response = ApiResponseGenerator.get_api_response(
            found_object_type, link_to_relations=TYPE_EXTRA_LINK_RELATIONS
        )
        object_type_link = object_type_response.data.self
        object_type_response.data = ObjectTypeSchema().dump(object_type_response.data)

        self_link = LinkGenerator.get_link_of(
            found_object_type,
            for_relation=UPDATE_REL,
            extra_relations=(TYPE_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[object_type_link],
            embedded=[object_type_response],
            data=ChangedApiObject(
                self=self_link,
                changed=object_type_link,
            ),
        )

    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def post(self, namespace: str, object_type: str):  # restore action
        """Restore a deleted type."""
        self._check_path_params(namespace=namespace, object_type=object_type)
        found_object_type: OntologyObjectType = self._get_object_type(
            namespace=namespace, object_type=object_type
        )
        self._check_if_namespace_modifiable(object_type=found_object_type)

        FLASK_OSO.authorize_and_set_resource(found_object_type, action=RESTORE)

        # only actually restore when not already restored
        if found_object_type.deleted_on is not None:
            # restore object type
            found_object_type.deleted_on = None
            DB.session.add(found_object_type)
            DB.session.commit()

        object_type_response = ApiResponseGenerator.get_api_response(
            found_object_type, link_to_relations=TYPE_EXTRA_LINK_RELATIONS
        )
        object_type_link = object_type_response.data.self
        object_type_response.data = ObjectTypeSchema().dump(object_type_response.data)

        self_link = LinkGenerator.get_link_of(
            found_object_type,
            for_relation=RESTORE_REL,
            extra_relations=(TYPE_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[object_type_link],
            embedded=[object_type_response],
            data=ChangedApiObject(
                self=self_link,
                changed=object_type_link,
            ),
        )

    @API_V1.response(200, DynamicApiResponseSchema(ChangedApiObjectSchema()))
    @API_V1.require_jwt("jwt")
    def delete(self, namespace: str, object_type: str):
        """Delete a type."""
        self._check_path_params(namespace=namespace, object_type=object_type)
        found_object_type: OntologyObjectType = self._get_object_type(
            namespace=namespace, object_type=object_type
        )
        self._check_if_namespace_modifiable(object_type=found_object_type)

        FLASK_OSO.authorize_and_set_resource(found_object_type)

        # only actually delete when not already deleted
        if found_object_type.deleted_on is None:
            # soft delete namespace
            found_object_type.deleted_on = datetime.now(timezone.utc)
            DB.session.add(found_object_type)
            DB.session.commit()

        object_type_response = ApiResponseGenerator.get_api_response(
            found_object_type, link_to_relations=TYPE_EXTRA_LINK_RELATIONS
        )
        object_type_link = object_type_response.data.self
        object_type_response.data = ObjectTypeSchema().dump(object_type_response.data)

        self_link = LinkGenerator.get_link_of(
            found_object_type,
            for_relation=DELETE_REL,
            extra_relations=(TYPE_REL_TYPE,),
            ignore_deleted=True,
        )
        self_link.resource_type = CHANGED_REL

        return ApiResponse(
            links=[object_type_link],
            embedded=[object_type_response],
            data=ChangedApiObject(
                self=self_link,
                changed=object_type_link,
            ),
        )

"""Module containing resource and link generators for object types."""

from typing import Any, Dict, Iterable, List, Optional, Union

from flask import url_for

from muse_for_anything.api.base_models import ApiLink, ApiResponse
from muse_for_anything.api.v1_api.constants import (
    COLLECTION_REL,
    CREATE,
    CREATE_REL,
    DELETE,
    DELETE_REL,
    GET,
    ITEM_COUNT_DEFAULT,
    ITEM_COUNT_QUERY_KEY,
    LATEST_REL,
    NAMESPACE_REL_TYPE,
    NAV_REL,
    OBJECT_REL_TYPE,
    PAGE_REL,
    POST_REL,
    PUT_REL,
    RESTORE,
    RESTORE_REL,
    SCHEMA_RESOURCE,
    TYPE_EXTRA_ARG,
    TYPE_EXTRA_LINK_RELATIONS,
    TYPE_ID_KEY,
    TYPE_ID_QUERY_KEY,
    TYPE_PAGE_RESOURCE,
    TYPE_REL_TYPE,
    TYPE_RESOURCE,
    TYPE_SCHEMA,
    TYPE_SCHEMA_POST,
    TYPE_VERSION_REL_TYPE,
    UP_REL,
    UPDATE,
    UPDATE_REL,
)
from muse_for_anything.api.v1_api.models.ontology import ObjectTypeData
from muse_for_anything.api.v1_api.request_helpers import (
    ApiObjectGenerator,
    ApiResponseGenerator,
    KeyGenerator,
    LinkGenerator,
    PageResource,
)
from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectType,
    OntologyObjectTypeVersion,
)
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource


# Types page ###################################################################
class ObjectTypePageKeyGenerator(
    KeyGenerator, resource_type=OntologyObjectType, page=True
):
    def update_key(self, key: Dict[str, str], resource: PageResource) -> Dict[str, str]:
        assert isinstance(resource, PageResource)
        assert resource.resource_type == OntologyObjectType
        assert resource.resource is not None
        key.update(KeyGenerator.generate_key(resource.resource))
        return key


class ObjectTypePageLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectType, page=True
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]],
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(
            OsoResource(TYPE_REL_TYPE, is_collection=True), action=GET
        ):
            return
        namespace = resource.resource
        assert namespace is not None
        assert isinstance(namespace, Namespace)
        if query_params is None:
            query_params = {ITEM_COUNT_QUERY_KEY: ITEM_COUNT_DEFAULT}
        return ApiLink(
            href=url_for(
                TYPE_PAGE_RESOURCE,
                namespace=str(namespace.id),
                **query_params,
                _external=True,
            ),
            rel=(COLLECTION_REL, PAGE_REL),
            resource_type=TYPE_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for(SCHEMA_RESOURCE, schema_id=TYPE_SCHEMA, _external=True),
        )


class ObjectTypePageCreateLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectType, page=True, relation=CREATE_REL
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, PageResource)
        assert resource.resource is not None and isinstance(resource.resource, Namespace)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(
                OsoResource(TYPE_REL_TYPE, parent_resource=resource.resource),
                action=CREATE,
            ):
                return
        if not ignore_deleted:
            if resource.resource.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(resource, query_params=query_params)
        link.rel = (CREATE_REL, POST_REL)
        link.schema = url_for(SCHEMA_RESOURCE, schema_id=TYPE_SCHEMA_POST, _external=True)
        return link


class ObjectTypePageUpLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectType, page=True, relation=UP_REL
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            resource.resource,
            extra_relations=(UP_REL,),
        )


class ObjectTypePageNamespacesNavLinkGenerator(
    LinkGenerator,
    resource_type=OntologyObjectType,
    page=True,
    relation=NAMESPACE_REL_TYPE,
):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            PageResource(Namespace, page_number=1),
            extra_relations=(NAV_REL,),
        )


# ObjectTypes ##################################################################
class ObjectTypeKeyGenerator(KeyGenerator, resource_type=OntologyObjectType):
    def update_key(
        self, key: Dict[str, str], resource: OntologyObjectType
    ) -> Dict[str, str]:
        assert isinstance(resource, OntologyObjectType)
        key.update(KeyGenerator.generate_key(resource.namespace))
        key[TYPE_ID_KEY] = str(resource.id)
        return key


class ObjectTypeSelfLinkGenerator(LinkGenerator, resource_type=OntologyObjectType):
    def generate_link(
        self,
        resource: OntologyObjectType,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                TYPE_RESOURCE,
                namespace=str(resource.namespace_id),
                object_type=str(resource.id),
                _external=True,
            ),
            rel=tuple(),
            resource_type=TYPE_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(SCHEMA_RESOURCE, schema_id=TYPE_SCHEMA, _external=True),
            name=resource.name,
        )


class ObjectTypeApiObjectGenerator(ApiObjectGenerator, resource_type=OntologyObjectType):
    def generate_api_object(
        self,
        resource: OntologyObjectType,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[ObjectTypeData]:
        assert isinstance(resource, OntologyObjectType)

        if not FLASK_OSO.is_allowed(resource, action=GET):
            return

        return ObjectTypeData(
            self=LinkGenerator.get_link_of(
                resource, query_params=query_params, ignore_deleted=True
            ),
            name=resource.name,
            description=resource.description,
            created_on=resource.created_on,
            updated_on=resource.updated_on,
            deleted_on=resource.deleted_on,
            version=resource.version,
            abstract=(not resource.is_toplevel_type),
            schema=resource.schema,
        )


class ObjectTypeApiResponseGenerator(
    ApiResponseGenerator, resource_type=OntologyObjectType
):
    def generate_api_response(
        self, resource, *, link_to_relations: Optional[Iterable[str]], **kwargs
    ) -> Optional[ApiResponse]:
        link_to_relations = (
            TYPE_EXTRA_LINK_RELATIONS if link_to_relations is None else link_to_relations
        )
        return ApiResponseGenerator.default_generate_api_response(
            resource, link_to_relations=link_to_relations, **kwargs
        )


class CreateObjectTypeLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectType, relation=CREATE_REL
):
    def generate_link(
        self,
        resource: OntologyObjectType,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectType)
        return LinkGenerator.get_link_of(
            PageResource(OntologyObjectType, resource=resource.namespace, page_number=1),
            query_params={},
            ignore_deleted=ignore_deleted,
            for_relation=CREATE_REL,
        )


class UpdateObjectTypeLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectType, relation=UPDATE_REL
):
    def generate_link(
        self,
        resource: OntologyObjectType,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectType)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=UPDATE):
                return  # not allowed
        if not ignore_deleted:
            if resource.is_deleted or resource.namespace.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (UPDATE_REL, PUT_REL)
        link.schema = url_for(SCHEMA_RESOURCE, schema_id=TYPE_SCHEMA_POST, _external=True)
        return link


class DeleteObjectTypeLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectType, relation=DELETE_REL
):
    def generate_link(
        self,
        resource: OntologyObjectType,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectType)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=DELETE):
                return  # not allowed
        if not ignore_deleted:
            if resource.is_deleted or resource.namespace.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (DELETE_REL,)
        return link


class RestoreObjectTypeLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectType, relation=RESTORE_REL
):
    def generate_link(
        self,
        resource: OntologyObjectType,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectType)
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=RESTORE):
                return  # not allowed
        if not ignore_deleted:
            if (not resource.is_deleted) or resource.namespace.is_deleted:
                return  # not deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (RESTORE_REL, POST_REL)
        return link


class ObjectTypeCreateObjectLinkGenerator(
    LinkGenerator,
    resource_type=OntologyObjectType,
    relation=f"{CREATE_REL}_{OBJECT_REL_TYPE}",
):
    def generate_link(
        self,
        resource: OntologyObjectType,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectType)
        if not ignore_deleted:
            if resource.is_deleted or resource.namespace.is_deleted:
                return  # deleted
        if not resource.is_toplevel_type:
            return  # type is abstract and should not be instantiated
        return LinkGenerator.get_link_of(
            PageResource(
                OntologyObject,
                resource=resource.namespace,
                page_number=1,
                extra_arguments={TYPE_EXTRA_ARG: resource},
            ),
            query_params={TYPE_ID_QUERY_KEY: str(resource.id)},
            ignore_deleted=ignore_deleted,
            for_relation=CREATE_REL,
        )


class ObjectTypeUpLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectType, relation=UP_REL
):
    def generate_link(
        self,
        resource: OntologyObjectType,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectType)
        return LinkGenerator.get_link_of(
            PageResource(OntologyObjectType, resource=resource.namespace, page_number=1),
            extra_relations=(UP_REL,),
        )


class ObjectTypeNamespaceNavLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectType, relation=NAMESPACE_REL_TYPE
):
    def generate_link(
        self,
        resource: OntologyObjectType,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectType)
        return LinkGenerator.get_link_of(
            resource.namespace,
            extra_relations=(NAV_REL,),
        )


class ObjectTypeTypeVersionsNavLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectType, relation=TYPE_VERSION_REL_TYPE
):
    def generate_link(
        self,
        resource: OntologyObjectType,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectType)
        return LinkGenerator.get_link_of(
            PageResource(OntologyObjectTypeVersion, resource=resource, page_number=1),
            extra_relations=(NAV_REL,),
        )


class ObjectTypeObjectsNavLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectType, relation=OBJECT_REL_TYPE
):
    def generate_link(
        self,
        resource: OntologyObjectType,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectType)
        return LinkGenerator.get_link_of(
            PageResource(OntologyObject, resource=resource.namespace, page_number=1),
            query_params={
                ITEM_COUNT_QUERY_KEY: ITEM_COUNT_DEFAULT,
                TYPE_ID_QUERY_KEY: str(resource.id),
            },
            extra_relations=(NAV_REL,),
        )


class ObjectTypeCurrentTypeVersionLinkGenerator(
    LinkGenerator, resource_type=OntologyObjectType, relation=LATEST_REL
):
    def generate_link(
        self,
        resource: OntologyObjectType,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObjectType)
        return LinkGenerator.get_link_of(
            resource.current_version,
            extra_relations=(LATEST_REL,),
        )

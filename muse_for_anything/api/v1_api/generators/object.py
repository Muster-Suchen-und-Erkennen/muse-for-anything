"""Module containing resource and link generators for objects."""

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
    NAMESPACE_REL_TYPE,
    NAV_REL,
    OBJECT_EXTRA_LINK_RELATIONS,
    OBJECT_ID_KEY,
    OBJECT_PAGE_RESOURCE,
    OBJECT_REL_TYPE,
    OBJECT_RESOURCE,
    OBJECT_VERSION_REL_TYPE,
    PAGE_REL,
    POST_REL,
    PUT_REL,
    RESTORE,
    RESTORE_REL,
    TYPE_EXTRA_ARG,
    TYPE_ID_QUERY_KEY,
    TYPE_REL_TYPE,
    TYPE_SCHEMA_RESOURCE,
    UP_REL,
    UPDATE,
    UPDATE_REL,
)
from muse_for_anything.api.v1_api.models.ontology import ObjectData
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
    OntologyObjectVersion,
)
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource


def object_type_schema_url(
    object_type: Union[OntologyObjectType, OntologyObjectTypeVersion]
) -> str:
    """Get the schema URL for a specific object type (version)."""
    if isinstance(object_type, OntologyObjectType):
        version = object_type.current_version_id
    else:
        version = object_type.id
    return url_for(
        TYPE_SCHEMA_RESOURCE,
        schema_id=str(version),
        _external=True,
    )


# Objects page #################################################################
class ObjectPageKeyGenerator(KeyGenerator, resource_type=OntologyObject, page=True):
    def update_key(self, key: Dict[str, str], resource: PageResource) -> Dict[str, str]:
        assert isinstance(resource, PageResource)
        assert resource.resource_type == OntologyObject
        assert resource.resource is not None
        key.update(KeyGenerator.generate_key(resource.resource))
        return key


class ObjectPageLinkGenerator(LinkGenerator, resource_type=OntologyObject, page=True):
    def generate_link(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]],
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(
            OsoResource(
                OBJECT_REL_TYPE,
                is_collection=True,
                parent_resource=resource.resource,
                arguments=resource.extra_arguments,
            ),
            action=GET,
        ):
            return
        namespace = resource.resource
        assert namespace is not None
        assert isinstance(namespace, Namespace)
        if query_params is None:
            query_params = {ITEM_COUNT_QUERY_KEY: ITEM_COUNT_DEFAULT}
        link = ApiLink(
            href=url_for(
                OBJECT_PAGE_RESOURCE,
                namespace=str(namespace.id),
                **query_params,
                _external=True,
            ),
            rel=(COLLECTION_REL, PAGE_REL),
            resource_type=OBJECT_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
        )
        if resource.extra_arguments and TYPE_EXTRA_ARG in resource.extra_arguments:
            object_type = resource.extra_arguments[TYPE_EXTRA_ARG]
            assert isinstance(object_type, OntologyObjectType)
            link.schema = object_type_schema_url(object_type)
        return link


class ObjectPageCreateLinkGenerator(
    LinkGenerator, resource_type=OntologyObject, page=True, relation=CREATE_REL
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
                OsoResource(
                    OBJECT_REL_TYPE,
                    parent_resource=resource.resource,
                    arguments=resource.extra_arguments,
                ),
                action=CREATE,
            ):
                return
        if not ignore_deleted:
            if resource.resource.is_deleted:
                return  # deleted

        if not resource.extra_arguments or TYPE_EXTRA_ARG not in resource.extra_arguments:
            return  # need a specific type to create objects!
        object_type = resource.extra_arguments[TYPE_EXTRA_ARG]
        assert isinstance(object_type, OntologyObjectType)

        if not ignore_deleted:
            if object_type.is_deleted or object_type.namespace.is_deleted:
                return  # deleted

        if not object_type.is_toplevel_type:
            return  # type is abstract and should not be instantiated

        link = LinkGenerator.get_link_of(resource, query_params=query_params)
        link.rel = (CREATE_REL, POST_REL)
        return link


class ObjectPageUpLinkGenerator(
    LinkGenerator, resource_type=OntologyObject, page=True, relation=UP_REL
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


class ObjectPageNamespacesNavLinkGenerator(
    LinkGenerator,
    resource_type=OntologyObject,
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


# Objects ######################################################################
class ObjectKeyGenerator(KeyGenerator, resource_type=OntologyObject):
    def update_key(self, key: Dict[str, str], resource: OntologyObject) -> Dict[str, str]:
        assert isinstance(resource, OntologyObject)
        key.update(KeyGenerator.generate_key(resource.namespace))
        key[OBJECT_ID_KEY] = str(resource.id)
        return key


class ObjectSelfLinkGenerator(LinkGenerator, resource_type=OntologyObject):
    def generate_link(
        self,
        resource: OntologyObject,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                OBJECT_RESOURCE,
                namespace=str(resource.namespace_id),
                object_id=str(resource.id),
                _external=True,
            ),
            rel=tuple(),
            resource_type=OBJECT_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource),
            schema=object_type_schema_url(resource.current_version.ontology_type_version),
            name=resource.name,
        )


class ObjectApiObjectGenerator(ApiObjectGenerator, resource_type=OntologyObject):
    def generate_api_object(
        self,
        resource: OntologyObject,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[ObjectData]:
        assert isinstance(resource, OntologyObject)

        if not FLASK_OSO.is_allowed(resource, action=GET):
            return

        return ObjectData(
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
            name=resource.name,
            description=resource.description,
            created_on=resource.created_on,
            updated_on=resource.updated_on,
            deleted_on=resource.deleted_on,
            version=resource.version or 1,
            data=resource.data,
        )


class ObjectApiResponseGenerator(ApiResponseGenerator, resource_type=OntologyObject):
    def generate_api_response(
        self, resource, *, link_to_relations: Optional[Iterable[str]], **kwargs
    ) -> Optional[ApiResponse]:
        link_to_relations = (
            OBJECT_EXTRA_LINK_RELATIONS
            if link_to_relations is None
            else link_to_relations
        )
        return ApiResponseGenerator.default_generate_api_response(
            resource, link_to_relations=link_to_relations, **kwargs
        )


class CreateObjectLinkGenerator(
    LinkGenerator, resource_type=OntologyObject, relation=CREATE_REL
):
    def generate_link(
        self,
        resource: OntologyObject,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObject)
        return LinkGenerator.get_link_of(
            PageResource(
                OntologyObject,
                resource=resource.namespace,
                page_number=1,
                extra_arguments={TYPE_EXTRA_ARG: resource.ontology_type},
            ),
            query_params={TYPE_ID_QUERY_KEY: str(resource.object_type_id)},
            ignore_deleted=ignore_deleted,
            for_relation=CREATE_REL,
        )


class UpdateObjectLinkGenerator(
    LinkGenerator, resource_type=OntologyObject, relation=UPDATE_REL
):
    def generate_link(
        self,
        resource: OntologyObject,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObject)
        object_type = resource.ontology_type
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=UPDATE):
                return  # not allowed
        if not ignore_deleted:
            if (
                resource.is_deleted
                or resource.namespace.is_deleted
                or object_type.is_deleted
                or object_type.namespace.is_deleted
            ):
                return  # deleted
        if not object_type.is_toplevel_type:
            return  # object_type is abstract and cannot be instantiated
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (UPDATE_REL, PUT_REL)
        return link


class DeleteObjectLinkGenerator(
    LinkGenerator, resource_type=OntologyObject, relation=DELETE_REL
):
    def generate_link(
        self,
        resource: OntologyObject,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObject)
        object_type = resource.ontology_type
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=DELETE):
                return  # not allowed
        if not ignore_deleted:
            if (
                resource.is_deleted
                or resource.namespace.is_deleted
                or object_type.is_deleted
                or object_type.namespace.is_deleted
            ):
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (DELETE_REL,)
        return link


class RestoreObjectLinkGenerator(
    LinkGenerator, resource_type=OntologyObject, relation=RESTORE_REL
):
    def generate_link(
        self,
        resource: OntologyObject,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObject)
        object_type = resource.ontology_type
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=RESTORE):
                return  # not allowed
        if not ignore_deleted:
            if (
                (not resource.is_deleted)
                or resource.namespace.is_deleted
                or object_type.is_deleted
                or object_type.namespace.is_deleted
            ):
                return  # not deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = (RESTORE_REL, POST_REL)
        return link


class ObjectUpLinkGenerator(LinkGenerator, resource_type=OntologyObject, relation=UP_REL):
    def generate_link(
        self,
        resource: OntologyObject,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObject)
        return LinkGenerator.get_link_of(
            PageResource(OntologyObject, resource=resource.namespace, page_number=1),
            extra_relations=(UP_REL,),
        )


class ObjectNamespaceNavLinkGenerator(
    LinkGenerator, resource_type=OntologyObject, relation=NAMESPACE_REL_TYPE
):
    def generate_link(
        self,
        resource: OntologyObject,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObject)
        return LinkGenerator.get_link_of(
            resource.namespace,
            extra_relations=(NAV_REL,),
        )


class ObjectVersionsNavLinkGenerator(
    LinkGenerator, resource_type=OntologyObject, relation=OBJECT_VERSION_REL_TYPE
):
    def generate_link(
        self,
        resource: OntologyObject,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObject)
        return LinkGenerator.get_link_of(
            PageResource(OntologyObjectVersion, resource=resource, page_number=1),
            extra_relations=(NAV_REL,),
        )


class ObjectTypeNavLinkGenerator(
    LinkGenerator, resource_type=OntologyObject, relation=TYPE_REL_TYPE
):
    def generate_link(
        self,
        resource: OntologyObject,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, OntologyObject)
        return LinkGenerator.get_link_of(
            resource.ontology_type,
            extra_relations=(NAV_REL,),
        )

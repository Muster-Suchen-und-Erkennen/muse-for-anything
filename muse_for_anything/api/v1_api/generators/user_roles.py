"""Generators for all user management resources."""

from typing import Dict, Iterable, List, Optional, Tuple

from flask import url_for
from flask.globals import g

from muse_for_anything.api.base_models import ApiLink, ApiResponse
from muse_for_anything.api.v1_api.constants import (
    COLLECTION_REL,
    CREATE,
    CREATE_REL,
    DANGER_REL,
    DELETE,
    DELETE_REL,
    GET,
    NAV_REL,
    PERMANENT_REL,
    POST_REL,
    REQUIRES_FRESH_LOGIN_REL,
    SCHEMA_RESOURCE,
    UP_REL,
    USER_ROLE_COLLECTION_RESOURCE,
    USER_ROLE_EXTRA_LINK_RELATIONS,
    USER_ROLE_ID_KEY,
    USER_ROLE_POST_SCHEMA,
    USER_ROLE_REL_TYPE,
    USER_ROLE_RESOURCE,
    USER_ROLE_SCHEMA,
)
from muse_for_anything.api.v1_api.models.auth import UserRoleData
from muse_for_anything.api.v1_api.request_helpers import (
    ApiObjectGenerator,
    ApiResponseGenerator,
    CollectionResource,
    KeyGenerator,
    LinkGenerator,
    PageResource,
)
from muse_for_anything.db.models.users import User, UserRole
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource

# Users Page ###################################################################


class UserRolesCollectionKeyGenerator(KeyGenerator, resource_type=UserRole, page=True):
    def update_key(
        self, key: Dict[str, str], resource: CollectionResource
    ) -> Dict[str, str]:
        assert isinstance(resource, CollectionResource)
        assert resource.resource_type == UserRole
        assert resource.resource is not None
        key.update(KeyGenerator.generate_key(resource.resource))
        return key


class UserRolesCollectionLinkGenerator(LinkGenerator, resource_type=UserRole, page=True):
    def generate_link(
        self,
        resource: CollectionResource,
        *,
        query_params: Optional[Dict[str, str]],
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, CollectionResource)
        assert resource.resource is not None
        username = (
            resource.resource
            if isinstance(resource.resource, str)
            else resource.resource.username
        )
        parent = resource.resource if isinstance(resource, User) else None
        if not FLASK_OSO.is_allowed(
            OsoResource(
                USER_ROLE_REL_TYPE,
                is_collection=True,
                parent_resource=parent,
                arguments={"username": username},
            ),
            action=GET,
        ):
            return
        return ApiLink(
            href=url_for(
                USER_ROLE_COLLECTION_RESOURCE, username=username, _external=True
            ),
            rel=(COLLECTION_REL,),
            resource_type=USER_ROLE_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for(SCHEMA_RESOURCE, schema_id=USER_ROLE_SCHEMA, _external=True),
        )


class UserRolesUpLinkGenerator(
    LinkGenerator, resource_type=UserRole, page=True, relation=UP_REL
):
    def generate_link(
        self,
        resource: CollectionResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            resource.resource,
            extra_relations=(UP_REL, NAV_REL),
        )


class UserRolesCollectionCreateUserRoleLinkGenerator(
    LinkGenerator, resource_type=UserRole, page=True, relation=CREATE_REL
):
    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(OsoResource(USER_ROLE_REL_TYPE), action=CREATE):
            return
        link = LinkGenerator.get_link_of(resource, query_params=query_params)
        link.rel = (CREATE_REL, POST_REL, REQUIRES_FRESH_LOGIN_REL)
        link.schema = url_for(
            SCHEMA_RESOURCE, schema_id=USER_ROLE_POST_SCHEMA, _external=True
        )
        return link


# UserRole #####################################################################


class UserRoleKeyGenerator(KeyGenerator, resource_type=UserRole):
    def update_key(self, key: Dict[str, str], resource: UserRole) -> Dict[str, str]:
        assert isinstance(resource, UserRole)
        key.update(KeyGenerator.generate_key(resource.user))
        key[USER_ROLE_ID_KEY] = str(resource.role)
        return key


class UserRoleSelfLinkGenerator(LinkGenerator, resource_type=UserRole):
    def generate_link(
        self,
        resource: UserRole,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                USER_ROLE_RESOURCE,
                username=str(resource.user.username),
                role=resource.role,
                _external=True,
            ),
            rel=tuple(),
            resource_type=USER_ROLE_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(SCHEMA_RESOURCE, schema_id=USER_ROLE_SCHEMA, _external=True),
            name=resource.role,
        )


class UserRoleUpLinkGenerator(LinkGenerator, resource_type=UserRole, relation=UP_REL):
    def generate_link(
        self,
        resource: UserRole,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            resource.user,
            extra_relations=(UP_REL,),
        )


class DeleteUserRoleLinkGenerator(
    LinkGenerator, resource_type=UserRole, relation=DELETE_REL
):
    def generate_link(
        self,
        resource: UserRole,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=DELETE):
                print("\n\n", "Deleting UserRole is not allowed!", resource, "\n\n")
                return  # not allowed

        link = LinkGenerator.get_link_of(resource)

        # deleting the user which is logged in is also a logout operation
        extra_rels: List[str] = []
        if resource.user == g.current_user:
            # deleting your users roles is dangerous!
            extra_rels.append(DANGER_REL)
            if resource.role == "admin":
                # deleting the own admin role is permanent (as admin rights are lost after deletion!)
                extra_rels.append(PERMANENT_REL)
        link.rel = (
            DELETE_REL,
            REQUIRES_FRESH_LOGIN_REL,
            *extra_rels,
        )

        return link


class UserRoleApiObjectGenerator(ApiObjectGenerator, resource_type=UserRole):
    def generate_api_object(
        self,
        resource: UserRole,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[UserRoleData]:
        assert isinstance(resource, UserRole)

        if not FLASK_OSO.is_allowed(resource, action=GET):
            print(">>> Not allowed", resource, GET)
            return

        return UserRoleData(
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
            role=resource.role,
            description=resource.description,
        )


class UserRoleApiResponseGenerator(ApiResponseGenerator, resource_type=UserRole):
    def generate_api_response(
        self, resource, *, link_to_relations: Optional[Iterable[str]], **kwargs
    ) -> Optional[ApiResponse]:
        link_to_relations = (
            USER_ROLE_EXTRA_LINK_RELATIONS
            if link_to_relations is None
            else link_to_relations
        )
        return ApiResponseGenerator.default_generate_api_response(
            resource, link_to_relations=link_to_relations, **kwargs
        )

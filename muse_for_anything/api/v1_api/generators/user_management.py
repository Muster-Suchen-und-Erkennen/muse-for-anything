"""Generators for all user management resources."""

from typing import Dict, Iterable, Optional

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
    OBJECT_REL_TYPE,
    PAGE_REL,
    POST_REL,
    PUT_REL,
    RESTORE,
    RESTORE_REL,
    SCHEMA_RESOURCE,
    TAXONOMY_REL_TYPE,
    TYPE_REL_TYPE,
    UP_REL,
    UPDATE,
    UPDATE_REL,
    USER_CREATE_SCHEMA,
    USER_EXTRA_LINK_RELATIONS,
    USER_ID_KEY,
    USER_PAGE_RESOURCE,
    USER_REL_TYPE,
    USER_RESOURCE,
    USER_SCHEMA,
)
from muse_for_anything.api.v1_api.models.auth import UserData
from muse_for_anything.api.v1_api.request_helpers import (
    ApiObjectGenerator,
    ApiResponseGenerator,
    KeyGenerator,
    LinkGenerator,
    PageResource,
)
from muse_for_anything.db.models.users import User
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource

# Users Page ###################################################################


class UsersPageKeyGenerator(KeyGenerator, resource_type=User, page=True):
    def update_key(self, key: Dict[str, str], resource: PageResource) -> Dict[str, str]:
        assert isinstance(resource, PageResource)
        assert resource.resource_type == User
        return key


class UsersPageLinkGenerator(LinkGenerator, resource_type=User, page=True):
    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, str]],
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(
            OsoResource(USER_REL_TYPE, is_collection=True), action=GET
        ):
            return
        if query_params is None:
            query_params = {ITEM_COUNT_QUERY_KEY: ITEM_COUNT_DEFAULT}
        return ApiLink(
            href=url_for(USER_PAGE_RESOURCE, **query_params, _external=True),
            rel=(COLLECTION_REL, PAGE_REL),
            resource_type=USER_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for(SCHEMA_RESOURCE, schema_id=USER_SCHEMA, _external=True),
        )


class UsersPageCreateNamespaceLinkGenerator(
    LinkGenerator, resource_type=User, page=True, relation=CREATE_REL
):
    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(OsoResource(USER_REL_TYPE), action=CREATE):
            print(">> No create user allowed!")
            return
        link = LinkGenerator.get_link_of(resource, query_params=query_params)
        link.rel = (CREATE_REL, POST_REL)
        link.schema = url_for(
            SCHEMA_RESOURCE, schema_id=USER_CREATE_SCHEMA, _external=True
        )
        return link


# User #########################################################################


class UserKeyGenerator(KeyGenerator, resource_type=User):
    def update_key(self, key: Dict[str, str], resource: User) -> Dict[str, str]:
        assert isinstance(resource, User)
        key[USER_ID_KEY] = str(resource.username)
        return key


class UserSelfLinkGenerator(LinkGenerator, resource_type=User):
    def generate_link(
        self,
        resource: User,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(USER_RESOURCE, username=str(resource.username), _external=True),
            rel=tuple(),
            resource_type=USER_REL_TYPE,
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for(SCHEMA_RESOURCE, schema_id=USER_SCHEMA, _external=True),
            name=resource.username,
        )


class UserUpLinkGenerator(LinkGenerator, resource_type=User, relation=UP_REL):
    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            PageResource(User, page_number=1),
            extra_relations=(UP_REL,),
        )


class UserApiObjectGenerator(ApiObjectGenerator, resource_type=User):
    def generate_api_object(
        self,
        resource: User,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[UserData]:
        assert isinstance(resource, User)

        if not FLASK_OSO.is_allowed(resource, action=GET):
            print(">>> Not allowed", resource, GET)
            return

        return UserData(
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
            username=resource.username,
            e_mail=resource.e_mail,
        )


class UserApiResponseGenerator(ApiResponseGenerator, resource_type=User):
    def generate_api_response(
        self, resource, *, link_to_relations: Optional[Iterable[str]], **kwargs
    ) -> Optional[ApiResponse]:
        link_to_relations = (
            USER_EXTRA_LINK_RELATIONS if link_to_relations is None else link_to_relations
        )
        return ApiResponseGenerator.default_generate_api_response(
            resource, link_to_relations=link_to_relations, **kwargs
        )

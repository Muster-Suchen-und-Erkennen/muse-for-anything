"""Generators for all user management resources."""

from typing import Dict, Iterable, Optional, Tuple

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
    EDIT,
    GET,
    ITEM_COUNT_DEFAULT,
    ITEM_COUNT_QUERY_KEY,
    LOGOUT_REL,
    NAV_REL,
    PAGE_REL,
    PERMANENT_REL,
    POST_REL,
    PUT_REL,
    REQUIRES_FRESH_LOGIN_REL,
    SCHEMA_RESOURCE,
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
    USER_UPDATE_SCHEMA,
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


class UsersPageCreateUserLinkGenerator(
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
            return
        link = LinkGenerator.get_link_of(resource, query_params=query_params)
        link.rel = (CREATE_REL, POST_REL, REQUIRES_FRESH_LOGIN_REL)
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


class UpdateUserLinkGenerator(LinkGenerator, resource_type=User, relation=UPDATE_REL):
    def generate_link(
        self,
        resource: User,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=EDIT):
                print("\n\n", "Editing User is not allowed!", resource, "\n\n")
                return  # not allowed

        link = LinkGenerator.get_link_of(resource)

        link.schema = url_for(
            SCHEMA_RESOURCE, schema_id=USER_UPDATE_SCHEMA, _external=True
        )

        link.rel = (
            UPDATE_REL,
            POST_REL,
            DANGER_REL,
            REQUIRES_FRESH_LOGIN_REL,
        )

        return link


class DeleteUserLinkGenerator(LinkGenerator, resource_type=User, relation=DELETE_REL):
    def generate_link(
        self,
        resource: User,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not LinkGenerator.skip_slow_policy_checks:
            # skip policy check for embedded resources
            if not FLASK_OSO.is_allowed(resource, action=DELETE):
                print("\n\n", "Deleting User is not allowed!", resource, "\n\n")
                return  # not allowed

        link = LinkGenerator.get_link_of(resource)

        # deleting the user which is logged in is also a logout operation
        extra_rels: Tuple[str, ...] = (
            (LOGOUT_REL,) if resource == g.current_user else tuple()
        )
        link.rel = (
            DELETE_REL,
            DANGER_REL,
            PERMANENT_REL,
            REQUIRES_FRESH_LOGIN_REL,
            *extra_rels,
        )

        return link


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

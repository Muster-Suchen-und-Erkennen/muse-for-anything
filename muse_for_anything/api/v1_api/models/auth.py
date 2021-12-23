"""Module containing all API schemas for the authentication API."""

from dataclasses import dataclass

import marshmallow as ma

from ...base_models import ApiLink, ApiObjectSchema, ApiResponseSchema, MaBaseSchema
from ....util.import_helpers import get_all_classes_of_module

__all__ = ["UserData"]  # extended later


class LoginPostSchema(MaBaseSchema):
    username = ma.fields.String(required=True, allow_none=False)
    password = ma.fields.String(required=True, allow_none=False, load_only=True)


class AccessTokenSchema(ApiObjectSchema):
    access_token = ma.fields.String(required=True, allow_none=False, dump_only=True)


class LoginTokensSchema(AccessTokenSchema):
    refresh_token = ma.fields.String(required=True, allow_none=False, dump_only=True)


class UserSchema(ApiObjectSchema):
    username = ma.fields.String(
        required=True,
        allow_none=False,
        metadata={"singleLine": True, "title": "Username"},
    )
    e_mail = ma.fields.String(
        required=False,
        allow_none=True,
        metadata={"singleLine": True, "title": "E-Mail (optional)"},
    )


class UserCreateSchema(UserSchema):
    password = ma.fields.String(
        required=True,
        allow_none=False,
        load_only=True,
        metadata={"singleLine": True, "password": True, "title": "Password"},
    )
    retype_password = ma.fields.String(
        required=True,
        allow_none=False,
        load_only=True,
        metadata={"singleLine": True, "password": True, "title": "Retype Password"},
    )


class UserUpdateSchema(UserSchema):
    password = ma.fields.String(
        required=False,
        allow_none=True,
        load_only=True,
        metadata={"password": True, "title": "Password"},
    )
    retype_password = ma.fields.String(
        required=False,
        allow_none=True,
        load_only=True,
        metadata={"password": True, "title": "Retype Password"},
    )


@dataclass
class UserData:
    self: ApiLink
    username: str
    e_mail: str


__all__.extend(get_all_classes_of_module(__name__, MaBaseSchema))

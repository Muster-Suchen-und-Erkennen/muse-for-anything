"""Module containing all API schemas for the authentication API."""

from dataclasses import dataclass

import marshmallow as ma
from marshmallow.validate import Email, OneOf, Regexp

from ...base_models import ApiLink, ApiObjectSchema, ApiResponseSchema, MaBaseSchema
from ....util.import_helpers import get_all_classes_of_module

__all__ = ["UserData"]  # extended later


class LoginPostSchema(MaBaseSchema):
    username = ma.fields.String(required=True, allow_none=False)
    password = ma.fields.String(required=True, allow_none=False, load_only=True)


class FreshLoginPostSchema(MaBaseSchema):
    password = ma.fields.String(required=True, allow_none=False, load_only=True)


class AccessTokenSchema(ApiObjectSchema):
    access_token = ma.fields.String(required=True, allow_none=False, dump_only=True)


class LoginTokensSchema(AccessTokenSchema):
    refresh_token = ma.fields.String(required=True, allow_none=False, dump_only=True)


class UserSchema(ApiObjectSchema):
    username = ma.fields.String(
        required=True,
        allow_none=False,
        validate=Regexp(r"[^@\s]+"),
        metadata={"singleLine": True, "title": "Username"},
    )
    e_mail = ma.fields.String(
        required=False,
        allow_none=True,
        validate=Email(),
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


class UserRolePostSchema(ApiObjectSchema):
    role = ma.fields.String(
        required=True,
        allow_none=False,
        metadata={"singleLine": True},
        validate=OneOf(
            choices=(
                "admin",
                "creator",
                "editor",
                "ont-namepsace_admin",
                "ont-namepsace_creator",
                "ont-namepsace_editor",
                "ont-object_admin",
                "ont-object_creator",
                "ont-object_editor",
                "ont-taxonomy_admin",
                "ont-taxonomy_creator",
                "ont-taxonomy_editor",
                "ont-type_admin",
                "ont-type_creator",
                "ont-type_editor",
            )
        ),
    )


class UserRoleSchema(UserRolePostSchema):
    description = ma.fields.String(
        required=False,
        allow_none=False,
        dump_only=True,
    )


@dataclass
class UserRoleData:
    self: ApiLink
    role: str
    description: str


__all__.extend(get_all_classes_of_module(__name__, MaBaseSchema))

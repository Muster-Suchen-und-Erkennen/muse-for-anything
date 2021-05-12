"""Module containing all API schemas for the authentication API."""

from ....util.import_helpers import get_all_classes_of_module
import marshmallow as ma
from ...base_models import MaBaseSchema, ApiResponseSchema, ApiObjectSchema

__all__ = []  # extended later


class LoginPostSchema(MaBaseSchema):
    username = ma.fields.String(required=True, allow_none=False)
    password = ma.fields.String(required=True, allow_none=False, load_only=True)


class AccessTokenSchema(ApiObjectSchema):
    access_token = ma.fields.String(required=True, allow_none=False, dump_only=True)


class LoginTokensSchema(AccessTokenSchema):
    refresh_token = ma.fields.String(required=True, allow_none=False, dump_only=True)


class UserSchema(ApiObjectSchema):
    username = ma.fields.String(required=True, allow_none=False)
    e_mail = ma.fields.String(required=False, allow_none=True)


__all__.extend(get_all_classes_of_module(__name__, MaBaseSchema))

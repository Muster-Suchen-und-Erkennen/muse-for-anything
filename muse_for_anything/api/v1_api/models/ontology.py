"""Module containing all API schemas for the ontology API."""

from dataclasses import dataclass
from datetime import datetime
import marshmallow as ma
from marshmallow.validate import Length

from ....util.import_helpers import get_all_classes_of_module

from ...base_models import (
    ApiLink,
    ApiObjectSchema,
    MaBaseSchema,
    ApiResponseSchema,
    BaseApiObject,
)


__all__ = ["NamespaceData"]


# The maximum string length the DB can handle for normal strings # TODO test this!
MAX_STRING_LENGTH = 170


class CreateSchemaMixin:
    created_on = ma.fields.DateTime(allow_none=False, dump_only=True)


class UpdateSchemaMixin:
    updated_on = ma.fields.DateTime(allow_none=False, dump_only=True)


class DeleteSchemaMixin:
    deleted_on = ma.fields.DateTime(allow_none=False, dump_only=True)


class ChangesSchemaMixin(CreateSchemaMixin, UpdateSchemaMixin, DeleteSchemaMixin):
    pass


class NamespaceSchema(ChangesSchemaMixin, ApiObjectSchema):
    name = ma.fields.String(
        required=True, allow_none=False, validate=Length(1, MAX_STRING_LENGTH)
    )
    description = ma.fields.String()


@dataclass
class NamespaceData(BaseApiObject):
    name: str
    description: str
    created_on: datetime
    updated_on: datetime
    deleted_on: datetime


__all__.extend(get_all_classes_of_module(__name__, MaBaseSchema))

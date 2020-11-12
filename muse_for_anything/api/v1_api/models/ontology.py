"""Module containing all API schemas for the ontology API."""

from ....util.import_helpers import get_all_classes_of_module
import marshmallow as ma
from marshmallow.validate import Length
from ...base_models import MaBaseSchema, ApiResponseSchema, ApiObjectSchema


# The maximum string length the DB can handle for normal strings # TODO test this!
MAX_STRING_LENGTH = 170


class CreateSchemaMixin:
    created_on = ma.fields.DateTime(required=True, allow_none=False, dump_only=True)


class UpdateSchemaMixin:
    updated_on = ma.fields.DateTime(required=True, allow_none=False, dump_only=True)


class DeleteSchemaMixin:
    deleted_on = ma.fields.DateTime(required=True, allow_none=False, dump_only=True)


class ChangesSchemaMixin(CreateSchemaMixin, UpdateSchemaMixin, DeleteSchemaMixin):
    pass


class NamespaceSchema(ChangesSchemaMixin, MaBaseSchema):
    name = ma.fields.String(
        required=True, allow_none=False, validate=Length(1, MAX_STRING_LENGTH)
    )
    description = ma.fields.String()


__all__ = list(get_all_classes_of_module(__name__, MaBaseSchema))

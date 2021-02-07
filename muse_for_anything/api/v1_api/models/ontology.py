"""Module containing all API schemas for the ontology API."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional, Sequence
import marshmallow as ma
from marshmallow.validate import Length, Regexp

from ....util.import_helpers import get_all_classes_of_module

from ...base_models import (
    ApiLink,
    ApiLinkSchema,
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
    description = ma.fields.String(missing="")


@dataclass
class CreateDeleteDataMixin:
    created_on: datetime
    deleted_on: Optional[datetime]


@dataclass
class ChangesDataMixin(CreateDeleteDataMixin):
    updated_on: datetime


@dataclass
class NameDescriptionMixin:
    name: str
    description: Optional[str]


@dataclass
class NamespaceData(BaseApiObject, ChangesDataMixin, NameDescriptionMixin):
    """Dataclass for Namespaces."""


class ObjectTypeSchema(ChangesSchemaMixin, ApiObjectSchema):
    name = ma.fields.String(
        allow_none=False, dump_only=True, validate=Length(1, MAX_STRING_LENGTH)
    )
    description = ma.fields.String(allow_none=False, dump_only=True)
    version = ma.fields.Integer(allow_none=False, dump_only=True)
    abstract = ma.fields.Boolean(required=False, missing=False, default=False)
    schema = ma.fields.Raw(allow_none=False, dump_only=True)


@dataclass
class ObjectTypeData(BaseApiObject, ChangesDataMixin, NameDescriptionMixin):
    version: int
    abstract: bool
    schema: Any


class TaxonomySchema(ChangesSchemaMixin, ApiObjectSchema):
    name = ma.fields.String(
        allow_none=False, required=True, validate=Length(1, MAX_STRING_LENGTH)
    )
    description = ma.fields.String(allow_none=True, required=False)
    items = ma.fields.List(
        ma.fields.Nested(ApiLinkSchema()), allow_none=False, dump_only=True
    )


@dataclass
class TaxonomyData(BaseApiObject, ChangesDataMixin, NameDescriptionMixin):
    items: Sequence[ApiLink] = tuple()


class TaxonomyItemSchema(ChangesSchemaMixin, ApiObjectSchema):
    name = ma.fields.String(
        allow_none=False, required=True, validate=Length(1, MAX_STRING_LENGTH)
    )
    description = ma.fields.String(allow_none=True, required=False)
    sort_key = ma.fields.Float(allow_nan=False, allow_none=True, required=False)
    is_toplevel_item = ma.fields.Boolean(allow_none=False, dump_only=True)
    version = ma.fields.Integer(allow_none=False, dump_only=True)
    children = ma.fields.List(
        ma.fields.Nested(ApiLinkSchema()), allow_none=False, dump_only=True
    )
    parents = ma.fields.List(
        ma.fields.Nested(ApiLinkSchema()), allow_none=False, dump_only=True
    )


@dataclass
class TaxonomyItemData(BaseApiObject, ChangesDataMixin, NameDescriptionMixin):
    sort_key: float
    version: int
    children: Sequence[ApiLink] = tuple()
    parents: Sequence[ApiLink] = tuple()

    @property
    def is_toplevel_item(self) -> bool:
        return len(self.parents) == 0


class TaxonomyItemRelationSchema(CreateSchemaMixin, DeleteSchemaMixin, ApiObjectSchema):
    source_item = ma.fields.Nested(ApiLinkSchema(), allow_none=False, dump_only=True)
    target_item = ma.fields.Nested(ApiLinkSchema(), allow_none=False, dump_only=True)


class TaxonomyItemRelationPostSchema(MaBaseSchema):
    namespace_id = ma.fields.String(required=True, allow_none=False, validate=Regexp(r"^[0-9]+$"))
    taxonomy_id = ma.fields.String(required=True, allow_none=False, validate=Regexp(r"^[0-9]+$"))
    taxonomy_item_id = ma.fields.String(required=True, allow_none=False, validate=Regexp(r"^[0-9]+$"))


@dataclass
class TaxonomyItemRelationData(BaseApiObject, CreateDeleteDataMixin):
    source_item: ApiLink
    target_item: ApiLink


__all__.extend(get_all_classes_of_module(__name__, MaBaseSchema))

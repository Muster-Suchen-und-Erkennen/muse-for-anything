"""Module containing all API schemas for the schema API."""

from typing import Any, Dict
from dataclasses import dataclass

import marshmallow as ma

from ....util.import_helpers import get_all_classes_of_module

from ...base_models import BaseApiObject, MaBaseSchema, ApiResponseSchema, ApiObjectSchema


__all__ = []


class SchemaApiObjectSchema(ApiObjectSchema):
    schema = ma.fields.Raw(dump_only=True)


@dataclass()
class SchemaApiObject(BaseApiObject):
    schema: Dict[str, Any]


__all__.extend(get_all_classes_of_module(__name__, MaBaseSchema))

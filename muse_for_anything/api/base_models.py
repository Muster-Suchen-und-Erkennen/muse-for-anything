"""Module containing base models for building api models."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Union
import marshmallow as ma
from marshmallow.base import SchemaABC
from marshmallow.validate import Length, Range
from marshmallow.utils import is_collection
from ..util.import_helpers import get_all_classes_of_module
from .util import camelcase

MAX_PAGE_ITEM_COUNT = 100


class MaBaseSchema(ma.Schema):
    """Base schema that automatically changes python snake case to camelCase in json."""

    # Uncomment to get ordered output
    # class Meta:
    #    ordered: bool = True

    def on_bind_field(self, field_name: str, field_obj: ma.fields.Field):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class ApiLinkBaseSchema(MaBaseSchema):
    """Schema for (non templated) api links."""

    href = ma.fields.Url(reqired=True, allow_none=False, dump_only=True)
    rel = ma.fields.List(
        ma.fields.String(allow_none=False, dump_only=True),
        validate=Length(min=1, error="At least one ref must be provided!"),
        reqired=True,
        allow_none=False,
        dump_only=True,
    )
    resource_type = ma.fields.String(reqired=True, allow_none=False, dump_only=True)
    doc = ma.fields.Url(allow_none=True, dump_only=True)
    schema = ma.fields.Url(allow_none=True, dump_only=True)

    @ma.post_dump()
    def remove_empty_attributes(
        self, data: Dict[str, Optional[Union[str, List[str]]]], **kwargs
    ):
        """Remove empty attributes from serialized links for a smaller and more readable output."""
        for key in ("doc", "schema", "resourceKey"):
            if data.get(key, False) is None:
                del data[key]
        if not data.get("queryKey", True):  # return True if not in dict
            del data["queryKey"]
        return data


class ApiLinkSchema(ApiLinkBaseSchema):
    resource_key = ma.fields.Mapping(
        ma.fields.String,
        ma.fields.String,
        reqired=False,
        allow_none=True,
        dump_only=True,
        metadata={
            "_jsonschema_type_mapping": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            }
        },
    )


class KeyedApiLinkSchema(ApiLinkSchema):
    """Schema for templated api links.

    The key attribute is a list of variable names that must be replaced in
    the url template to get a working url.
    """

    key = ma.fields.List(
        ma.fields.String(allow_none=False, dump_only=True),
        validate=Length(min=1, error="At least one ref must be provided!"),
        reqired=True,
        allow_none=False,
        dump_only=True,
    )
    query_key = ma.fields.List(
        ma.fields.String(allow_none=False, dump_only=True),
        validate=Length(min=1, error="At least one ref must be provided!"),
        reqired=True,
        allow_none=False,
        dump_only=True,
    )


class ApiObjectSchema(MaBaseSchema):
    self = ma.fields.Nested(ApiLinkSchema, allow_none=False, dump_only=True)


class NewApiObjectSchema(ApiObjectSchema):
    new = ma.fields.Nested(ApiLinkSchema, allow_none=False, dump_only=True)


class ChangedApiObjectSchema(ApiObjectSchema):
    changed = ma.fields.Nested(ApiLinkSchema, allow_none=False, dump_only=True)


class ApiResponseSchema(MaBaseSchema):
    links = ma.fields.Nested(
        ApiLinkSchema, many=True, reqired=True, allow_none=False, dump_only=True
    )
    keyed_links = ma.fields.Nested(
        KeyedApiLinkSchema, many=True, reqired=False, allow_none=True, dump_only=True
    )
    embedded = ma.fields.List(
        ma.fields.Nested(lambda: RawApiResponseSchema(exclude=("embedded",))),
        reqired=False,
        allow_none=True,
        dump_only=True,
    )
    data = ma.fields.Nested(lambda: ApiObjectSchema(), reqired=True, allow_none=False)

    @ma.post_dump()
    def remove_empty_attributes(
        self, data: Dict[str, Optional[Union[str, List[str]]]], **kwargs
    ):
        """Remove empty attributes from serialized api response for a smaller and more readable output."""
        for key in ("keyedLinks", "key", "embedded"):
            if data.get(key, False) is None:
                del data[key]
        return data


class RawApiResponseSchema(ApiResponseSchema):
    """API Response Schema to be used if data is already marshalled."""

    data = ma.fields.Raw(reqired=True, allow_none=False)


class DynamicApiResponseSchema(ApiResponseSchema):
    data = ma.fields.Method("dump_data", "load_data", reqired=True, allow_none=False)

    def __init__(
        self, data_schema: SchemaABC = ApiObjectSchema(), *args, **kwargs
    ) -> None:
        if not isinstance(data_schema, SchemaABC):
            raise TypeError("The given data_schema must be an instance not a class!")
        self._data_schema = data_schema
        super().__init__(*args, **kwargs)

    def dump_data(self, obj: Any) -> Any:
        attr: Any = super().get_attribute(obj, "data", None)
        many: bool = is_collection(attr)
        return self._data_schema.dump(attr, many=many)

    def load_data(self, value: Dict[str, Any]) -> Any:
        many: bool = is_collection(value)
        print(value, many)
        return self._data_schema.load(value, many=many)


class CursorPageSchema(ApiObjectSchema):
    collection_size = ma.fields.Integer(required=True, allow_none=False, dump_only=True)
    page = ma.fields.Integer(required=True, allow_none=False, dump_only=True)
    first_row = ma.fields.Integer(required=True, allow_none=False, dump_only=True)
    items = ma.fields.List(
        ma.fields.Nested(ApiLinkSchema), default=tuple(), required=True, dump_only=True
    )


class CursorPageArgumentsSchema(MaBaseSchema):
    cursor = ma.fields.String(allow_none=True, load_only=True)
    item_count = ma.fields.Integer(
        data_key="item-count",
        allow_none=True,
        load_only=True,
        missing=25,
        validate=Range(1, MAX_PAGE_ITEM_COUNT, min_inclusive=True, max_inclusive=True),
    )
    sort = ma.fields.String(allow_none=True, load_only=True)


@dataclass
class ApiLinkBase:
    href: str
    rel: Sequence[str]
    resource_type: str
    doc: Optional[str] = None
    schema: Optional[str] = None


@dataclass
class ApiLink(ApiLinkBase):
    resource_key: Optional[Dict[str, str]] = None


@dataclass
class KeyedApiLink(ApiLinkBase):
    key: Sequence[str] = tuple()
    query_key: Sequence[str] = tuple()


@dataclass
class BaseApiObject:
    self: ApiLink


@dataclass
class NewApiObject(BaseApiObject):
    new: ApiLink


@dataclass
class ChangedApiObject(BaseApiObject):
    changed: ApiLink


@dataclass
class ApiResponse:
    links: Sequence[ApiLink]
    data: Any
    embedded: Optional[Sequence[Any]] = None
    keyed_links: Optional[Sequence[KeyedApiLink]] = None


@dataclass
class CursorPage:
    self: ApiLink
    collection_size: int
    page: int
    first_row: int
    items: List[ApiLink]


__all__ = list(get_all_classes_of_module(__name__, MaBaseSchema))

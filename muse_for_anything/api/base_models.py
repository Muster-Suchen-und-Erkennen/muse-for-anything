"""Module containing base models for building api models."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union
import marshmallow as ma
from marshmallow.base import SchemaABC
from marshmallow.validate import Length
from marshmallow.utils import is_collection
from ..util.import_helpers import get_all_classes_of_module
from .util import camelcase


class MaBaseSchema(ma.Schema):
    """Base schema that automatically changes python snake case to camelCase in json."""

    # Uncomment to get ordered output
    # class Meta:
    #    ordered: bool = True

    def on_bind_field(self, field_name: str, field_obj: ma.fields.Field):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)


class ApiLinkSchema(MaBaseSchema):
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
        for key in ("doc", "schema"):
            if data.get(key, False) is None:
                del data[key]
        return data


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


class ApiObjectSchema(MaBaseSchema):
    self = ma.fields.Nested(ApiLinkSchema, reqired=True, allow_none=False, dump_only=True)


class ApiResponseSchema(MaBaseSchema):
    links = ma.fields.Nested(
        ApiLinkSchema, many=True, reqired=True, allow_none=False, dump_only=True
    )
    keyed_links = ma.fields.Nested(
        KeyedApiLinkSchema, many=True, reqired=False, allow_none=True, dump_only=True
    )
    embedded = ma.fields.List(
        ma.fields.Nested(lambda: ApiResponseSchema(exclude=("embedded",))),
        reqired=False,
        allow_none=True,
        dump_only=True,
    )
    key = ma.fields.Mapping(
        ma.fields.String, ma.fields.String, reqired=False, allow_none=True, dump_only=True
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


class DynamicApiResponseSchema(ApiResponseSchema):
    data = ma.fields.Method("dump_data", "load_data", reqired=True, allow_none=False)

    def __init__(
        self, data_schema: SchemaABC = ApiObjectSchema(), *args, **kwargs
    ) -> None:
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


@dataclass
class ApiLink:
    href: str
    rel: Sequence[str]
    resource_type: str
    doc: Optional[str] = None
    schema: Optional[str] = None


@dataclass
class ApiResponse:
    links: Sequence[ApiLink]
    data: Union[Sequence[Any], Any]
    embedded: Optional[Sequence[Any]] = None
    keyed_links: Optional[Sequence[ApiLink]] = None
    key: Optional[Dict[str, str]] = None


__all__ = list(get_all_classes_of_module(__name__, MaBaseSchema))

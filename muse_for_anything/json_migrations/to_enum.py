from typing import Sequence, Union

from jsonschema import Draft7Validator

from .data_migration import DataMigrator, JsonSchema


def _check_enum_properties(
    source_type: str, source_schema: dict, target_schema: dict
) -> bool:
    target_values = set(target_schema.get("enum", []))

    if source_type == "enum":
        source_values = set(source_schema.get("enum", []))
        if not target_values:
            return False  # illegal schema, enum without values!
        return not target_values.isdisjoint(source_values)
    elif source_type == "boolean":
        return not target_values.isdisjoint({True, False})
    elif source_type in ("integer", "number", "string"):
        validator = Draft7Validator(source_schema)
        converter = {"integer": int, "number": float, "string": str}[source_type]
        return any(
            v is not None and validator.is_valid(converter(v)) for v in target_values
        )

    return False


def _convert_to_enum(  # noqa: C901
    data, target_enum: Sequence[Union[None, bool, int, float, str]]
) -> Union[None, bool, int, float, str]:
    match = ...

    for value in target_enum:
        if data == value:
            if match == ...:
                match = value
            if type(data) is type(value):
                return value  # return exact match immediately
        elif match == ...:
            if isinstance(data, bool) and data == bool(value):
                match = value  # allow inexact matches for bool
            if not isinstance(data, (int, float, str)):
                continue
            if value is None:
                continue
            try:
                if type(value)(data) == value:
                    match = value  # allow exatct matches but with type conversion
            except ValueError:
                pass

    if match == ...:
        raise ValueError("Could not convert data, no enum entry matches the source data.")

    return match


class PrimitiveToEnum(DataMigrator):

    source_types = {"boolean", "enum", "integer", "number", "string"}
    target_types = {"enum"}

    def basic_check_concrete_schema_change(
        self, source_type: str, target_type: str, source_schema: dict, target_schema: dict
    ) -> bool:
        if source_type not in self.source_types:
            return False

        return _check_enum_properties(source_type, source_schema, target_schema)

    def migrate_data_concrete(
        self,
        data,
        source_type: str,
        target_type: str,
        source_schema: JsonSchema,
        target_schema: JsonSchema,
        *,
        depth: int = 0,
    ) -> Union[None, bool, int, float, str]:
        target_enum = target_schema.schema.get("enum", [])

        if None not in target_enum and data is None:
            null_default = target_schema.schema.get("default", None)
            if isinstance(null_default, (bool, int, float, str)):
                data = null_default

        if data is None or isinstance(data, (bool, int, float, str)):
            return _convert_to_enum(data, target_enum)

        raise ValueError("No transformation to enum possible!")

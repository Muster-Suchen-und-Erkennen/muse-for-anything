from json import dumps
from typing import Optional

from .data_migration import DataMigrator, JsonSchema


def _convert_to_string(data) -> str:
    if isinstance(data, str):
        return data
    elif isinstance(data, bool):
        return "True" if data else ""
    elif isinstance(data, (int, float)):
        return str(data)
    elif isinstance(data, (dict, list, tuple)):
        return dumps(data)

    raise ValueError("Unsupported data type for string conversion.")


class PrimitiveToString(DataMigrator):

    source_types = {"boolean", "enum", "integer", "number", "string"}
    target_types = {"string"}

    def basic_check_concrete_schema_change(
        self, source_type: str, target_type: str, source_schema: dict, target_schema: dict
    ) -> bool:
        if source_type not in self.source_types:
            return False
        min_length_source = source_schema.get("minLength", 0)
        min_length_target = target_schema.get("minLength", 0)
        max_length_source = source_schema.get("maxLength", None)
        max_length_target = target_schema.get("maxLength", None)

        if max_length_target is not None and min_length_target > max_length_target:
            return False  # illegal schema...

        if max_length_source is not None:
            if max_length_source < min_length_target:
                return False

        if max_length_target is not None:
            if min_length_source > max_length_target:
                return False

        return True

    def migrate_data_concrete(
        self,
        data,
        source_type: str,
        target_type: str,
        source_schema: JsonSchema,
        target_schema: JsonSchema,
        *,
        depth: int = 0,
    ) -> Optional[str]:
        if data is None and target_schema.is_nullable:
            return None

        null_default = target_schema.schema.get("default", "")

        if data is None:
            if isinstance(null_default, str):
                return null_default
            else:
                if source_type == target_type == "string":
                    return ""  # allow dropping nullable constraint on same type migration
                raise ValueError(
                    "Transformation from None to string without default value is not possible!"
                )

        if isinstance(data, (bool, int, float, str)):
            return _convert_to_string(data)

        raise ValueError("No transformation to string possible!")


class NestedToString(DataMigrator):

    source_types = {"object", "array", "tuple"}
    target_types = {"string"}

    def basic_check_concrete_schema_change(
        self, source_type: str, target_type: str, source_schema: dict, target_schema: dict
    ) -> bool:
        if source_type in self.source_types:
            return True
        return False

    def migrate_data_concrete(
        self,
        data,
        source_type: str,
        target_type: str,
        source_schema: JsonSchema,
        target_schema: JsonSchema,
        *,
        depth: int = 0,
    ) -> Optional[str]:
        null_default = target_schema.schema.get("default", None)
        if data is None and target_schema.is_nullable:
            return None

        null_default = target_schema.schema.get("default", "")

        if data is None:
            if isinstance(null_default, str):
                return null_default
            raise ValueError(
                "Transformation from None to string without default value is not possible!"
            )

        if isinstance(data, (dict, list, tuple)):
            return _convert_to_string(data)

        raise ValueError("No transformation to string possible!")

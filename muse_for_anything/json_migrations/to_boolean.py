from typing import Optional

from .data_migration import DataMigrator, JsonSchema


class PrimitiveToBoolean(DataMigrator):

    source_types = {"boolean", "enum", "integer", "number", "string"}
    target_types = {"boolean"}

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
    ) -> Optional[bool]:
        if data is None and target_schema.is_nullable:
            return None

        null_default = target_schema.schema.get("default", None)

        if data is None:
            if not isinstance(null_default, bool):
                if source_type == target_type == "boolean":
                    return (
                        False  # allow dropping nullable constraint on same type migration
                    )
                raise ValueError(
                    "Transformation from None to boolean without default value is not possible!"
                )
            return null_default

        if isinstance(data, (bool, int, float, str)):
            return bool(data)

        raise ValueError("No transformation to boolean possible!")

from typing import Optional, Type, Union

from .data_migration import DataMigrator, JsonSchema


def _check_numeric_attributes(source_schema: dict, target_schema: dict):  # noqa: C901
    """Used to check if there are contradictions in the number keywords,
    e. g., min and max, of source and target schema.

    Args:
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema

    Returns:
        boolean: True, if update valid, else false
    """
    min_source = source_schema.get("minimum", None)
    min_target = target_schema.get("minimum", None)
    max_source = source_schema.get("maximum", None)
    max_target = target_schema.get("maximum", None)
    excl_min_source = source_schema.get("exclusiveMinimum", None)
    excl_min_target = target_schema.get("exclusiveMinimum", None)
    excl_max_source = source_schema.get("exclusiveMaximum", None)
    excl_max_target = target_schema.get("exclusiveMaximum", None)

    if min_source is not None and max_target is not None:
        if min_source > max_target:
            return False

    if min_source is not None and excl_max_target is not None:
        if min_source >= excl_max_target:
            return False

    if max_source is not None and min_target is not None:
        if max_source < min_target:
            return False

    if max_source is not None and excl_min_target is not None:
        if max_source <= excl_min_target:
            return False

    if excl_min_source is not None and max_target is not None:
        if excl_min_source >= max_target:
            return False

    if excl_min_source is not None and excl_max_target is not None:
        if excl_min_source >= excl_max_target:
            return False

    if excl_max_source is not None and min_target is not None:
        if excl_max_source <= min_target:
            return False

    if excl_max_source is not None and excl_min_target is not None:
        if excl_max_source <= excl_min_target:
            return False

    return True


def _convert_to_number(
    data: Union[bool, int, float, str], target_type: Union[Type[int], Type[float]]
) -> Union[int, float]:
    if isinstance(data, target_type):
        return data  # don't convert
    if isinstance(data, (bool, int, float)):
        return target_type(data)  # numbers and boolean are safe for direct conversion

    # handle strings
    if target_type is float:
        return float(data)
    # try int first for better support of high values
    try:
        return int(data)
    except ValueError:
        # try float and then remove decimal values
        return int(float(data))


class PrimitiveToNumber(DataMigrator):

    source_types = {"boolean", "enum", "integer", "number", "string"}
    target_types = {"integer", "number"}

    def basic_check_concrete_schema_change(
        self, source_type: str, target_type: str, source_schema: dict, target_schema: dict
    ) -> bool:
        if source_type in self.source_types:
            if source_type in ("integer", "number"):
                return _check_numeric_attributes(source_schema, target_schema)
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
    ) -> Optional[Union[int, float]]:
        if data is None and target_schema.is_nullable:
            return None

        null_default = target_schema.schema.get("default", None)

        target_py_type = int if target_type == "integer" else float

        if data is None:
            if (
                target_py_type is int and not isinstance(null_default, int)
            ) or not isinstance(null_default, (int, float)):
                if source_type == target_type and source_type in ("integer", "number"):
                    return 0  # allow dropping nullable constraint on same type migration
                raise ValueError(
                    "Transformation from None to integer/number without default value is not possible!"
                )
            return null_default

        if isinstance(data, (bool, int, float, str)):
            return _convert_to_number(data, target_py_type)

        raise ValueError("No transformation to integer/number possible!")

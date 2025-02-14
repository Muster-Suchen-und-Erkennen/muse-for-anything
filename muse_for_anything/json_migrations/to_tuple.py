from copy import deepcopy
from typing import Optional, Sequence, Union

from .data_migration import DataMigrator, JsonSchema


def _get_item_schemas(
    schema_type: str, schema: JsonSchema
) -> tuple[Sequence[JsonSchema], Optional[JsonSchema]]:
    if schema_type == "array":
        additional_items = schema.get_nested(("items",))
        if not additional_items:
            return tuple(), None
        return tuple(), additional_items
    if schema_type == "tuple":
        tuple_items = schema.schema.get("items", [])
        item_schemas: tuple[JsonSchema, ...]
        if isinstance(tuple_items, (list, tuple)):
            nested_schemas = tuple(
                schema.get_nested(("items", i)) for i in range(len(tuple_items))
            )
            if all(s is not None for s in nested_schemas):
                item_schemas = nested_schemas  # type: ignore
            else:
                raise ValueError("Bad tuple schema!")
        else:
            item_schemas = tuple()
        additional_items = schema.get_nested(("additionalItems",))
        if not additional_items:
            return item_schemas, None
        return item_schemas, additional_items
    return tuple(), None


def _extract_default_value(schema: dict):
    is_nullable = "null" in schema.get("type", [])
    if None in schema.get("enum", []):
        is_nullable = True
    null_default = schema.get("default", None)
    if null_default is not None:
        return null_default
    elif is_nullable:
        return None

    raise ValueError(
        "Cannot infer missing items for non nullable items schema without a default value!"
    )


class SequenceToTuple(DataMigrator):

    source_types = {"tuple", "array"}
    target_types = {"tuple"}

    def basic_check_concrete_schema_change(
        self, source_type: str, target_type: str, source_schema: dict, target_schema: dict
    ) -> bool:
        target_min = target_schema.get("minItems", 0)
        source_max = source_schema.get("maxItems", None)
        target_max = target_schema.get("maxItems", None)

        if target_max and target_max < target_min:
            return False  # illegal schema
        if source_max and source_max < target_min:
            return False  # too few items

        return source_type in self.source_types

    def check_concrete_schema_change(  # noqa: C901
        self,
        source_type: str,
        target_type: str,
        source_schema: JsonSchema,
        target_schema: JsonSchema,
        source_visited_set: set[str],
        target_visited_set: set[str],
        depth: int,
    ) -> bool:
        if not self.basic_check_concrete_schema_change(
            source_type, target_type, source_schema.schema, target_schema.schema
        ):
            return False

        source_item_schemas, source_additional_items = _get_item_schemas(
            source_type, source_schema
        )
        target_item_schemas, target_additional_items = _get_item_schemas(
            target_type, target_schema
        )
        target_min = target_schema.schema.get("minItems", 0)
        target_max = target_schema.schema.get("maxItems", None)

        if not source_item_schemas and source_additional_items is None:
            return False

        if not target_item_schemas and target_additional_items is None:
            return False

        for i, source_item_schema in enumerate(source_item_schemas):
            if target_max is not None and (i + 1) > target_max:
                return True
            if i < len(target_item_schemas):
                target_item_schema = target_item_schemas[i]
            else:
                target_item_schema = target_additional_items
            if target_item_schema is None:
                return False
            result = DataMigrator.check_schema_changes(
                source_schema=source_item_schema,
                target_schema=target_item_schema,
                source_visited_set=set(source_visited_set),
                target_visited_set=set(target_visited_set),
                depth=depth,
            )
            if result in (False, "recursion"):
                return False

        checked_schemas = len(source_item_schemas)

        if target_max is not None and checked_schemas == target_max:
            return True  # no need to check for additional items

        if source_additional_items is None:
            if checked_schemas >= target_min:
                return True  # already enough items

        # FIXME check correctly for added items with nullable schemas...

        # check additionalItems source schema compatibility with all remaining target schemas
        targets_to_check = target_item_schemas[checked_schemas:]
        if target_additional_items:
            targets_to_check = *targets_to_check, target_additional_items

        for target_item_schema in targets_to_check:
            checked_schemas += 1
            if not source_additional_items:
                resolved_target_schema, *_ = self.resolve_references(
                    target_item_schema, set()
                )
                if not resolved_target_schema.is_nullable:
                    if resolved_target_schema.schema.get("default", None) is None:
                        # cannot infer missing iteems for non nullable schemas
                        return False
                if checked_schemas >= target_min:
                    break
                continue
            result = DataMigrator.check_schema_changes(
                source_schema=source_additional_items,
                target_schema=target_item_schema,
                source_visited_set=set(source_visited_set),
                target_visited_set=set(target_visited_set),
                depth=depth,
            )
            if result in (False, "recursion"):
                return False
        return True

    def migrate_data_concrete(  # noqa: C901
        self,
        data,
        source_type: str,
        target_type: str,
        source_schema: JsonSchema,
        target_schema: JsonSchema,
        *,
        depth: int = 0,
    ) -> Optional[Union[list, tuple]]:
        if data is None and target_schema.is_nullable:
            return None

        null_default = target_schema.schema.get("default", None)
        if data is None:
            if isinstance(null_default, (list, tuple)):
                return null_default
            raise ValueError("Cannot migrate from null to tuple without a default value.")

        if not isinstance(data, (list, tuple)):
            raise ValueError("Given data is not of an tuple type.")

        source_item_schemas, source_additional_items = _get_item_schemas(
            source_type, source_schema
        )
        target_item_schemas, target_additional_items = _get_item_schemas(
            target_type, target_schema
        )
        target_min = target_schema.schema.get("minItems", 0)
        target_max = target_schema.schema.get("maxItems", None)

        if not source_item_schemas and source_additional_items is None:
            raise ValueError("Could not retrieve item schemas from source schema.")

        if not target_item_schemas and target_additional_items is None:
            raise ValueError("Could not retrieve item schemas from target schema.")

        if target_max and len(data) > target_max:
            data = data[:target_max]  # cut off all extra values

        updated_data = []

        for i, item in enumerate(data):
            if i < len(source_item_schemas):
                source_item_schema = source_item_schemas[i]
            else:
                source_item_schema = source_additional_items
            if i < len(target_item_schemas):
                target_item_schema = target_item_schemas[i]
            else:
                target_item_schema = target_additional_items
            if source_item_schema is None:
                raise ValueError(f"Source item schema {i} could not be determined.")
            if target_item_schema is None:
                if source_type == "tuple" and len(updated_data) >= target_min:
                    # allow dropping items for tuple to tuple schemas
                    return updated_data
                raise ValueError(f"Target item schema {i} could not be determined.")
            updated_data.append(
                DataMigrator.migrate_data(
                    item, source_item_schema, target_item_schema, depth=depth
                )
            )

        if len(updated_data) < target_min:
            # infer items from any additional tuple schemas on the target side
            extra_target_schemas = target_item_schemas[len(updated_data) :]
            for target_item_schema in extra_target_schemas:
                resolved_target_items_schema, *_ = self.resolve_references(
                    target_item_schema, set()
                )
                default_item_data = _extract_default_value(
                    resolved_target_items_schema.schema
                )

                updated_data.append(deepcopy(default_item_data))
                if len(updated_data) == target_min:
                    break

        if len(updated_data) < target_min and target_additional_items:
            # infer items from additional items schema on the target side
            resolved_target_items_schema, *_ = self.resolve_references(
                target_additional_items, set()
            )
            default_item_data = _extract_default_value(
                resolved_target_items_schema.schema
            )
            updated_data.extend(
                deepcopy(default_item_data) for i in range(target_min - len(updated_data))
            )

        if len(updated_data) < target_min:
            raise ValueError(
                "Failed to convert from tuple/array to tuple, missing some items."
            )

        return updated_data

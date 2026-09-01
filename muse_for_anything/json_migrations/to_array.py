from copy import deepcopy
from typing import Optional, Union

from .data_migration import DataMigrator, JsonSchema


class ArrayToArray(DataMigrator):

    source_types = {"array"}
    target_types = {"array"}

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

        return source_type == target_type == "array"

    def check_concrete_schema_change(
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

        source_items_schema = source_schema.get_nested(("items",))
        target_items_schema = target_schema.get_nested(("items",))

        if source_items_schema is None or target_items_schema is None:
            return False

        # check items schema compatibility
        result = DataMigrator.check_schema_changes(
            source_schema=source_items_schema,
            target_schema=target_items_schema,
            source_visited_set=set(source_visited_set),
            target_visited_set=set(target_visited_set),
            depth=depth,
        )
        return False if result == "recursion" else result

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
                return deepcopy(null_default)
            raise ValueError("Cannot migrate from null to array without a default value.")

        if not isinstance(data, (list, tuple)):
            raise ValueError("Given data is not of an array type.")

        source_items_schema = source_schema.get_nested(("items",))
        target_items_schema = target_schema.get_nested(("items",))

        if source_items_schema is None or target_items_schema is None:
            raise ValueError("Source or target items schema could not be determined.")

        min_items = target_schema.schema.get("minItems", 0)
        max_items = target_schema.schema.get("maxItems", None)
        if max_items and len(data) > max_items:
            data = data[:max_items]  # cut off all extra values

        updated_data = []

        for item in data:
            updated_data.append(
                DataMigrator.migrate_data(
                    item, source_items_schema, target_items_schema, depth=depth
                )
            )

        # try to infer missing values
        if len(updated_data) < min_items:
            resolved_target_items_schema, *_ = self.resolve_references(
                target_items_schema, set()
            )
            null_default = resolved_target_items_schema.schema.get("default", None)
            if null_default is not None:
                default_item_data = null_default
            elif resolved_target_items_schema.is_nullable:
                default_item_data = None
            else:
                raise ValueError(
                    "Cannot infer missing items for non nullable items schema without a default value!"
                )

            updated_data.extend(
                deepcopy(default_item_data) for _ in range(min_items - len(updated_data))
            )

        return updated_data


class TupleToArray(DataMigrator):

    source_types = {"tuple"}
    target_types = {"array"}

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

        tuple_items = len(source_schema.get("items", []))
        has_additional_items = bool(source_schema.get("additionalItems", None))

        if not has_additional_items and tuple_items < target_min:
            return False  # too few items

        return source_type == "tuple"

    def check_concrete_schema_change(
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

        source_items_length = len(source_schema.schema.get("items", []))

        target_items_schema = target_schema.get_nested(("items",))
        target_min = target_schema.schema.get("minItems", 0)
        target_max = target_schema.schema.get("maxItems", None)

        if target_items_schema is None:
            return False

        item_count = 0

        for i in range(source_items_length):
            source_item_schema = source_schema.get_nested(("items", i))
            if not source_item_schema:
                return False
            item_count += 1
            if target_max is not None and item_count > target_max:
                return True
            result = DataMigrator.check_schema_changes(
                source_schema=source_item_schema,
                target_schema=target_items_schema,
                source_visited_set=set(source_visited_set),
                target_visited_set=set(target_visited_set),
                depth=depth,
            )
            if result in (False, "recursion"):
                return False

        if target_max is not None and item_count == target_max:
            return True  # no need to check for additional items

        additional_items_schema = source_schema.get_nested(("additionalItems",))

        if additional_items_schema is None:
            if item_count >= target_min:
                return True  # already enough items
            else:
                return False  # not enough items

        # check additionalItems schema compatibility
        result = DataMigrator.check_schema_changes(
            source_schema=additional_items_schema,
            target_schema=target_items_schema,
            source_visited_set=set(source_visited_set),
            target_visited_set=set(target_visited_set),
            depth=depth,
        )
        return False if result == "recursion" else result

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
                return deepcopy(null_default)
            raise ValueError("Cannot migrate from null to array without a default value.")

        if not isinstance(data, (list, tuple)):
            raise ValueError("Given data is not of an array type.")

        target_items_schema = target_schema.get_nested(("items",))

        if target_items_schema is None:
            raise ValueError("Target items schema could not be determined.")

        source_items_len = len(source_schema.schema.get("items", []))

        min_items = target_schema.schema.get("minItems", 0)
        max_items = target_schema.schema.get("maxItems", None)
        if max_items and len(data) > max_items:
            data = data[:max_items]  # cut off all extra values

        updated_data = []

        for i, item in enumerate(data):
            if i < source_items_len:
                source_item_schema = source_schema.get_nested(("items", i))
            else:
                source_item_schema = source_schema.get_nested(("additionalItems",))
            if source_item_schema is None or target_items_schema is None:
                raise ValueError(f"Source item schema {i} could not be determined.")
            updated_data.append(
                DataMigrator.migrate_data(
                    item, source_item_schema, target_items_schema, depth=depth
                )
            )

        if len(updated_data) < min_items:
            raise ValueError("Failed to convert from tuple to array, missing some items.")

        return updated_data

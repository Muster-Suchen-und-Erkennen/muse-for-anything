from copy import deepcopy
from json import JSONDecodeError, loads
from typing import Optional, Union

from .data_migration import DataMigrator, JsonSchema
from .jsonschema_validator import extract_type


class JsonToSequence(DataMigrator):

    source_types = {"string"}
    target_types = {"array", "tuple"}
    priority = 10  # try JSON migration first

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
    ) -> Optional[Union[list, tuple]]:
        if data in (None, "") and target_schema.is_nullable:
            return None

        null_default = target_schema.schema.get("default", None)

        if data in (None, ""):
            if not isinstance(null_default, (list, tuple)):
                raise ValueError(
                    "Transformation from None/empty string to arry/tuple without default value is not possible!"
                )
            return deepcopy(null_default)

        try:
            array_data = loads(data)
            target_min = target_schema.schema.get("minItems", 0)
            target_max = target_schema.schema.get("maxItems", None)
            if isinstance(array_data, (list, tuple)):
                if len(array_data) < target_min:
                    raise ValueError(
                        "Could not migrate json data to an array, missing some items."
                    )
                if target_max is not None and len(array_data) > target_max:
                    raise ValueError(
                        "Could not migrate json data to an array, too many items."
                    )
                return array_data
        except JSONDecodeError:
            pass

        # pass on migration to other migrator
        raise NotImplementedError(
            "Transformation from basic string to array/tuple is not implemented by this migrator."
        )


class PrimitiveToSequence(DataMigrator):

    source_types = {"boolean", "enum", "integer", "number", "string"}
    target_types = {"array", "tuple"}

    def basic_check_concrete_schema_change(
        self, source_type: str, target_type: str, source_schema: dict, target_schema: dict
    ) -> bool:
        target_min = target_schema.get("minItems", 0)
        target_max = target_schema.get("maxItems", None)

        if target_min > 1:
            return False  # resulting arrays can only have 0..1 elements

        if target_max and target_max < target_min:
            return False  # illegal schema

        if target_type == "tuple":
            tuple_items = len(target_schema.get("items", []))
            has_additional_items = bool(target_schema.get("additionalItems", None))

            if not has_additional_items and tuple_items < 1:
                return False  # too few items

        return source_type in self.source_types

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

        target_item_schema: Optional[JsonSchema] = None
        if target_type == "array":
            target_item_schema = target_schema.get_nested(("items",))
        elif target_type == "tuple":
            target_item_schema = target_schema.get_nested(("items", 0))
            if target_item_schema is None:
                target_item_schema = target_schema.get_nested(("additionalItems",))

        if target_item_schema is None:
            return False

        # resolve target schema to assert that it is a primitive type schema
        resolved_schema, *_ = self.resolve_references(target_item_schema, set())
        target_item_type, _ = extract_type(resolved_schema.schema)
        if target_item_type not in self.source_types:
            return False

        # check additionalItems schema compatibility
        result = DataMigrator.check_schema_changes(
            source_schema=source_schema,
            target_schema=target_item_schema,
            source_visited_set=source_visited_set - {source_schema.schema_url},
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

        target_item_schema: Optional[JsonSchema] = None
        if target_type == "array":
            target_item_schema = target_schema.get_nested(("items",))
        elif target_type == "tuple":
            target_item_schema = target_schema.get_nested(("items", 0))
            if target_item_schema is None:
                target_item_schema = target_schema.get_nested(("additionalItems",))

        if target_item_schema is None:
            raise ValueError("Target item schema could not be determined.")

        return [
            DataMigrator.migrate_data(
                data, source_schema, target_item_schema, depth=depth
            )
        ]

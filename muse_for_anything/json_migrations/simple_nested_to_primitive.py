import re
from copy import deepcopy
from typing import Optional, Union

from .data_migration import DataMigrator, JsonSchema
from .util import extract_type


class SimpleNestedToPrimitive(DataMigrator):

    source_types = {"object", "array", "tuple"}
    target_types = {"boolean", "enum", "integer", "number"}

    def _extract_nested_schema(  # noqa: C901
        self, schema_type: str, schema: dict
    ) -> Optional[dict]:
        if schema_type == "object":
            prop_schemas = list(schema.get("properties", {}).values())
            if len(prop_schemas) == 1:
                return prop_schemas[0]
            if "additionalProperties" in schema:
                # prefer testing additional properties
                return schema.get("additionalProperties", None)
            if "patternProperties" in schema:
                for prop_schema in schema.get("patternProperties", {}).values():
                    if "type" in prop_schema:
                        prop_schema_type, _ = extract_type(prop_schema)
                        if prop_schema_type not in (
                            "boolean",
                            "enum",
                            "integer",
                            "number",
                            "string",
                        ):
                            continue
                    return prop_schema
        if schema_type == "tuple":
            tuple_schemas = schema.get("items", [])
            if len(tuple_schemas) >= 1:
                return tuple_schemas[0]
            else:
                return schema.get("additionalItems", None)
        if schema_type in "array":
            return schema.get("items", None)
        return None

    def _extract_exact_property_schema(
        self, prop_key: str, schema: dict
    ) -> Optional[dict]:
        if prop_key in schema.get("properties", {}):
            return schema.get("properties", {}).get(prop_key, None)
        if not schema.get("patternProperties", {}):
            return schema.get("additionalProperties", None)
        for pattern, nested in schema.get("patternProperties", {}).items():
            if re.search(pattern, prop_key):
                return nested
        return None

    def basic_check_concrete_schema_change(  # noqa: C901
        self, source_type: str, target_type: str, source_schema: dict, target_schema: dict
    ) -> bool:
        nested_schema: Optional[dict] = None
        if source_type == "object":
            size = len(source_schema.get("properties", {}))
            if size > 1:
                return False
            if size == 1:
                nested_schema = next(iter(source_schema.get("properties", {}).values()))
            if source_schema.get("minProperties", 0) > 1:
                return False
            if source_schema.get("maxProperties", 1) < 1:
                return False
        if source_type == "tuple":
            size = len(source_schema.get("items", []))
            if size == 0:
                nested_schema = source_schema.get("additionalItems", None)
                if not nested_schema:
                    return False
            elif size >= 1:
                nested_schema = source_schema.get("items", [])[0]
        if source_type in "array":
            nested_schema = source_schema.get("items", {})

        if nested_schema and "$ref" not in nested_schema:
            nested_type, _ = extract_type(nested_schema)
            if nested_type not in {"boolean", "enum", "integer", "number", "string"}:
                return False
        return True

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

        # check nested schemas with references to ensure that nested data is of primitive type
        nested_schema: Optional[dict] = self._extract_nested_schema(
            source_type, source_schema.schema
        )

        if not nested_schema:
            return False

        nested_source_schema = JsonSchema(
            schema_url=f"{source_schema.schema_url}/nested",
            schema=nested_schema,
            root_url=source_schema.root_url,
            root=source_schema.root,
        )

        # check that nested schema is a primitve type schema to avoid possible loops
        resolved_source_schema, _, _ = self.resolve_references(
            nested_source_schema, set()
        )
        resolved_type, _ = extract_type(resolved_source_schema.schema)
        if resolved_type not in {"boolean", "enum", "integer", "number", "string"}:
            return False

        # check nested schema compatibility
        result = DataMigrator.check_schema_changes(
            nested_source_schema,
            target_schema,
            source_visited_set=set(source_visited_set),
            target_visited_set=target_visited_set - {target_schema.schema_url},
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
    ) -> Optional[Union[int, float]]:
        is_nullable = target_schema.is_nullable

        null_default = target_schema.schema.get("default", None)

        nested_schema: Optional[dict] = None
        nested_data = None

        if source_type == "object" and isinstance(data, dict):
            if len(data) == 0:
                nested_data = None
            elif len(data) == 1:
                prop_key, nested_data = next(iter(data.items()))
                nested_schema = self._extract_exact_property_schema(
                    prop_key, source_schema.schema
                )
        elif source_type in ("array", "tuple") and isinstance(data, (list, tuple)):
            if len(data) == 0:
                nested_data = None
            if len(data) >= 1:
                nested_data = data[0]
        else:
            raise ValueError("No transformation to primitive type possible!")

        if nested_data is None:
            if is_nullable:
                return None
            elif null_default is not None:
                nested_data = deepcopy(null_default)  # try out default value
            else:
                raise ValueError(
                    "Transformation from None to primitive type without default value is not possible!"
                )

        if nested_schema is None:
            nested_schema: Optional[dict] = self._extract_nested_schema(
                source_type, source_schema.schema
            )

        if not nested_schema:
            raise ValueError("Could not extract source schema.")

        nested_source_schema = JsonSchema(
            schema_url=f"{source_schema.schema_url}/nested",
            schema=nested_schema,
            root_url=source_schema.root_url,
            root=source_schema.root,
        )

        # check that nested schema is a primitve type schema to avoid possible loops
        resolved_source_schema, _, _ = self.resolve_references(
            nested_source_schema, set()
        )
        resolved_type, _ = extract_type(resolved_source_schema.schema)
        if resolved_type not in {"boolean", "enum", "integer", "number", "string"}:
            raise ValueError(
                "Unable to migrate a complex object nested inside a simple nested object to a primitive type."
            )

        return DataMigrator.migrate_data(
            nested_data, nested_source_schema, target_schema, depth=depth
        )

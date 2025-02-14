import re
from copy import deepcopy
from json import JSONDecodeError, loads
from typing import Optional

from .data_migration import DataMigrator, JsonSchema
from .jsonschema_validator import extract_type


def _get_prop_schema(property: str, schema: dict, base: JsonSchema) -> JsonSchema:
    return JsonSchema(f"{base.schema_url}/{property}", schema, base.root_url, base.root)


def _extract_prop_schema(property: str, schema: JsonSchema) -> Optional[JsonSchema]:
    prop_schema = schema.schema.get("properties", {}).get(property, None)
    if prop_schema:
        return JsonSchema(
            f"{schema.schema_url}/{property}",
            prop_schema,
            schema.root_url,
            schema.root,
        )
    if prop_schema is not None:
        raise ValueError("Empty property schemas are not supported!")
    for pattern, prop_schema in schema.schema.get("patternProperties", {}).items():
        if re.search(pattern, property):
            return JsonSchema(
                f"{schema.schema_url}/{property}",
                prop_schema,
                schema.root_url,
                schema.root,
            )
    additional_properties = schema.schema.get("additionalProperties", None)
    if additional_properties is not None:
        return JsonSchema(
            f"{schema.schema_url}/{property}",
            additional_properties,
            schema.root_url,
            schema.root,
        )
    return None


class ObjectToObject(DataMigrator):

    source_types = {"object"}
    target_types = {"object"}

    def basic_check_concrete_schema_change(
        self, source_type: str, target_type: str, source_schema: dict, target_schema: dict
    ) -> bool:
        # TODO handle allOf
        required = set(target_schema.get("required", []))

        if (
            "maxProperties" in target_schema
            and target_schema.get("minProperties", 0) > target_schema["maxProperties"]
        ):
            return False  # illegal schema

        if (
            "maxProperties" in source_schema
            and source_schema["maxProperties"] < target_schema.get("minProperties", 0)
            and source_schema["maxProperties"] < len(required)
        ):
            return False  # too few properties to update!

        return True

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

        source_props = source_schema.schema.get("properties", {})
        target_props = target_schema.schema.get("properties", {})

        # TODO handle allOf
        required = set(target_schema.schema.get("required", []))

        renamed = {}

        if (
            len(source_props.keys() - target_props.keys())
            == 1
            == len(target_props.keys() - source_props.keys())
        ):
            source_prop_name, *_ = source_props.keys() - target_props.keys()
            target_prop_name, *_ = target_props.keys() - source_props.keys()
            renamed[source_prop_name] = target_prop_name

        for prop in source_props:
            source_prop_schema = _extract_prop_schema(prop, source_schema)
            if not source_prop_schema:
                raise ValueError("Bad input schema!")
            if prop in renamed:
                prop = renamed[prop]
            target_prop_schema = _extract_prop_schema(prop, target_schema)
            if not target_prop_schema:
                continue  # property to remove
            required.discard(prop)
            is_valid = DataMigrator.check_schema_changes(
                source_prop_schema,
                target_prop_schema,
                source_visited_set=set(source_visited_set),
                target_visited_set=set(target_visited_set),
                depth=depth,
            )
            if not is_valid:  # assume recursion = valid
                return False

        for prop in required:
            # check all required properties that are left
            source_prop_schema = _extract_prop_schema(prop, source_schema)
            target_prop_schema = _extract_prop_schema(prop, target_schema)
            if not target_prop_schema:
                return False  # could not find schema for a required property
            if not source_prop_schema:
                resolved, _, _ = self.resolve_references(target_prop_schema, set())
                if resolved.is_nullable:
                    continue  # nullable properties can be added without source schema
                return False  # could not find schema for a required property
            is_valid = DataMigrator.check_schema_changes(
                source_prop_schema,
                target_prop_schema,
                source_visited_set=set(source_visited_set),
                target_visited_set=set(target_visited_set),
                depth=depth,
            )
            if not is_valid:  # assume recursion = valid
                return False

        source_add_props_schema: Optional[JsonSchema] = None
        target_add_props_schema: Optional[JsonSchema] = None
        source_additional_props = source_schema.schema.get("additionalProperties", None)
        if source_additional_props:
            source_add_props_schema = _get_prop_schema(
                "$$additionalProperties$$", source_additional_props, target_schema
            )
        target_additional_props = target_schema.schema.get("additionalProperties", None)
        if target_additional_props:
            target_add_props_schema = _get_prop_schema(
                "$$additionalProperties$$", target_additional_props, target_schema
            )

        for pattern, schema in source_schema.schema.get("patternProperties", {}).items():
            source_pattern_schema = _get_prop_schema(
                f"$$pattern$${pattern}$$", schema, source_schema
            )
            if pattern_prop := target_schema.schema.get("patternProperties", {}).get(
                pattern, None
            ):
                # check pattern schema compatibility if pattern is unchanged
                target_pattern_schema = _get_prop_schema(
                    f"$$pattern$${pattern}$$", pattern_prop, target_schema
                )
                is_valid = DataMigrator.check_schema_changes(
                    source_pattern_schema,
                    target_pattern_schema,
                    source_visited_set=set(source_visited_set),
                    target_visited_set=set(target_visited_set),
                    depth=depth,
                )
                if not is_valid:  # assume recursion = valid
                    return False
                continue
            if (
                "patternProperties" not in target_schema.schema
                and target_add_props_schema
            ):
                is_valid = DataMigrator.check_schema_changes(
                    source_pattern_schema,
                    target_add_props_schema,
                    source_visited_set=set(source_visited_set),
                    target_visited_set=set(target_visited_set),
                    depth=depth,
                )
                if not is_valid:  # assume recursion = valid
                    return False
                continue

        if source_add_props_schema and target_add_props_schema:
            is_valid = DataMigrator.check_schema_changes(
                source_add_props_schema,
                target_add_props_schema,
                source_visited_set=set(source_visited_set),
                target_visited_set=set(target_visited_set),
                depth=depth,
            )
            if not is_valid:  # assume recursion = valid
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
    ) -> Optional[dict]:
        if data is None and target_schema.is_nullable:
            return None

        null_default = target_schema.schema.get("default", None)
        if data is None:
            if isinstance(null_default, dict):
                return deepcopy(null_default)
            raise ValueError(
                "Cannot migrate from null to object without a default value."
            )

        if not isinstance(data, dict):
            raise ValueError("Given data is not of an object type!")

        updated_data = {}

        source_properties = source_schema.schema.get("properties", {})
        target_properties = target_schema.schema.get("properties", {})
        common_properties = target_properties.keys() & source_properties.keys()
        new_properties = target_properties.keys() - source_properties.keys()
        deleted_properties = source_properties.keys() - target_properties.keys()

        # TODO: extend required set in allOf cases
        required = set(target_schema.schema.get("required", []))

        # FIXME: handle additionalProperties if defined!!!
        for prop in common_properties:
            if prop not in data and prop not in required:
                continue  # property may be absent in target object
            prop_source_schema = _get_prop_schema(
                prop, source_properties.get(prop, None), source_schema
            )
            prop_target_schema = _get_prop_schema(
                prop, target_properties.get(prop, None), target_schema
            )
            prop_data = data.get(prop, None)
            try:
                updated_data[prop] = DataMigrator.migrate_data(
                    data=prop_data,
                    source_schema=prop_source_schema,
                    target_schema=prop_target_schema,
                    depth=depth,
                )
            except ValueError:
                if data is None and prop not in required:
                    pass  # property may be absent in target object
                else:
                    raise  # reraise error

        handled_props = set(common_properties)

        # One prop added, one deleted, likely name changes
        if len(new_properties) == 1 and len(deleted_properties) == 1:
            new_property = next(iter(new_properties))
            deleted_property = next(iter(deleted_properties))
            if deleted_property in data:
                prop_source_schema = _get_prop_schema(
                    deleted_property,
                    source_properties.get(deleted_property, None),
                    source_schema,
                )
                prop_target_schema = _get_prop_schema(
                    new_property, target_properties.get(new_property, None), target_schema
                )
                try:
                    prop_data = data.get(deleted_property, None)
                    updated_data[new_property] = DataMigrator.migrate_data(
                        data=prop_data,
                        source_schema=prop_source_schema,
                        target_schema=prop_target_schema,
                        depth=depth,
                    )
                    handled_props.add(new_property)
                except ValueError:
                    if data is None and new_property not in required:
                        pass  # property may be absent in target object
                    else:
                        raise  # reraise error

        # handle patternProperties and additionalProperties
        for prop, value in data.items():
            if prop in handled_props:
                continue  # already handled this prop
            prop_source_schema = _extract_prop_schema(prop, source_schema)
            if not prop_source_schema:
                # source data does not conform to source schema!
                raise ValueError(
                    "Source object cannot be migrated if it does not match with source schema!"
                )
            prop_target_schema = _extract_prop_schema(prop, target_schema)
            if not prop_target_schema:
                continue  # property cannot be migrated
            try:
                updated_data[new_property] = DataMigrator.migrate_data(
                    data=value,
                    source_schema=prop_source_schema,
                    target_schema=prop_target_schema,
                    depth=depth,
                )
            except ValueError:
                if data is None and prop not in required:
                    pass  # property may be absent in target object
                else:
                    raise  # reraise error

        # Add all new and required properties
        for prop in required - updated_data.keys():
            prop_target_schema = _extract_prop_schema(prop, target_schema)
            if not prop_target_schema:
                raise ValueError(
                    "Failed object migration, could not locate schema for a required property."
                )
            prop_target_schema, _, _ = self.resolve_references(prop_target_schema, set())
            if prop_target_schema.is_nullable:
                updated_data[prop] = None
            elif (
                target_null_default := prop_target_schema.schema.get("default", None)
            ) is not None:
                updated_data[prop] = deepcopy(target_null_default)

        if updated_data.keys() < required:
            # not all required keys are present
            raise ValueError(
                "Could not transform to object, some required properties are missing."
            )

        nr_of_properties = len(updated_data)
        if nr_of_properties < target_schema.schema.get("minProperties", 0):
            raise ValueError("Could not migrate object, missing some properties.")
        if nr_of_properties > target_schema.schema.get("maxProperties", nr_of_properties):
            raise ValueError("Could not migrate object, too many properties.")

        return updated_data


class JsonToObject(DataMigrator):

    source_types = {"string"}
    target_types = {"object"}
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
    ) -> Optional[dict]:
        if data in (None, "") and target_schema.is_nullable:
            return None

        null_default = target_schema.schema.get("default", None)

        if data in (None, ""):
            if not isinstance(null_default, dict):
                raise ValueError(
                    "Transformation from None/empty string to object without default value is not possible!"
                )
            return deepcopy(null_default)

        try:
            object_data = loads(data)
            if isinstance(object_data, dict):
                return object_data
        except JSONDecodeError:
            pass

        # pass on migration to other migrator
        raise NotImplementedError(
            "Transformation from basic string to object is not implemented by this migrator."
        )


class PrimitiveToObject(DataMigrator):

    source_types = {"boolean", "enum", "integer", "number", "string"}
    target_types = {"object"}

    def basic_check_concrete_schema_change(
        self, source_type: str, target_type: str, source_schema: dict, target_schema: dict
    ) -> bool:
        if source_type not in self.source_types:
            return False

        required = set(target_schema.get("required", []))

        if len(required) > 1 or target_schema.get("minProperties", 0) > 1:
            return False  # requires too many properties for a simple instance

        if target_schema.get("maxProperties", 1) < 1:
            return False  # allows too few properties for a simple instance

        return len(target_schema.get("properties", {})) == 1

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

        prop_schemas = target_schema.schema.get("properties", {})
        assert len(prop_schemas) == 1, "Already tested in basic tests"

        first, *_ = prop_schemas.items()
        property, schema = first
        prop_schema = _get_prop_schema(property, schema, target_schema)

        resolved_prop_schema, *_ = self.resolve_references(prop_schema, set())

        prop_type, _ = extract_type(resolved_prop_schema.schema)
        if prop_type not in self.source_types:
            return False  # assert that property schema is already a primitive schema

        # check nested schema compatibility
        result = DataMigrator.check_schema_changes(
            source_schema,
            prop_schema,
            source_visited_set=source_visited_set - {source_schema.schema_url},
            target_visited_set=set(target_visited_set),
            depth=depth,
        )
        return False if result == "recursion" else result

    def migrate_data_concrete(
        self,
        data,
        source_type: str,
        target_type: str,
        source_schema: JsonSchema,
        target_schema: JsonSchema,
        *,
        depth: int = 0,
    ) -> Optional[dict]:
        if data is None and target_schema.is_nullable:
            return None

        null_default = target_schema.schema.get("default", None)

        if data in (None, ""):
            if not isinstance(null_default, dict):
                raise ValueError(
                    "Transformation from None to object without default value is not possible!"
                )
            return deepcopy(null_default)

        prop_schemas = target_schema.schema.get("properties", {})
        if len(prop_schemas) != 1:
            raise ValueError(
                "Cannot transform from primitive types to complex objects with multiple properties."
            )

        first, *_ = prop_schemas.items()
        property, schema = first
        prop_schema = _get_prop_schema(property, schema, target_schema)

        resolved_prop_schema, *_ = self.resolve_references(prop_schema, set())

        prop_type, _ = extract_type(resolved_prop_schema.schema)
        if prop_type not in self.source_types:
            raise ValueError(
                "Cannot convert from primitive types to nested complex objects."
            )

        prop_data = DataMigrator.migrate_data(
            data, source_schema, prop_schema, depth=depth
        )

        return {property: prop_data}

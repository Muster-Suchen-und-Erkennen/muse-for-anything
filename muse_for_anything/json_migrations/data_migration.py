# ==============================================================================
# MIT License
#
# Copyright (c) 2024 Jan Weber
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

from typing import ClassVar, Literal, Optional, Sequence, Union

from muse_for_anything.api.v1_api.ontology_object_validation import (
    resolve_type_version_schema_url,
)
from muse_for_anything.json_migrations.util import extract_type


class JsonSchema:

    __slots__ = ("schema_url", "schema", "root_url", "root")

    def __init__(
        self,
        schema_url: str,
        schema: dict,
        root_url: Optional[str] = None,
        root: Optional[dict] = None,
    ) -> None:
        self.schema_url: str = schema_url
        self.schema: dict = schema

        if root is None and root_url is None:
            self.root_url: str = schema_url
            self.root: dict = schema
        elif root is None or root_url is None:
            raise ValueError(
                "If either root or root_url is given, then both values must not be None!"
            )
        else:
            self.root_url = root_url
            self.root = root

        if not isinstance(self.root.get("definitions", None), dict):
            # TODO: maybe use warning instead of hard error
            raise ValueError(
                "Root schema does not contain 'definitions' for local schema resolution!"
            )

    @property
    def is_nullable(self) -> bool:
        if "null" in self.schema.get("type", []):
            return True
        if None in self.schema.get("enum", []):
            return True
        return False

    def resolve_local(self, reference: str) -> "JsonSchema":
        if reference.startswith("#/definitions/"):
            reference = reference.removeprefix("#/definitions/")
        elif reference.startswith("/definitions/"):
            reference = reference.removeprefix("/definitions/")
        elif reference.startswith("definitions/"):
            reference = reference.removeprefix("definitions/")
        else:
            raise ValueError(
                "Local schema references must start with either '#/definitions/', '/definitions/' or 'definitions/'."
            )
        schema = self.root.get("definitions", {}).get(reference)
        schema_url = f"{self.root_url}#/definitions/{reference}"
        if schema is None:
            raise KeyError(
                f"Schema ref '#/definitions/{reference}' not found in schema {self.root_url}."
            )
        return JsonSchema(
            schema_url=schema_url, schema=schema, root_url=self.root_url, root=self.root
        )

    def get_nested(
        self, path: Union[list[Union[str, int]], tuple[Union[str, int], ...]]
    ) -> Optional["JsonSchema"]:
        if not path:
            raise ValueError("Path cannot be empty!")
        fragment_extra = "/".join(str(c) for c in path)
        schema_url = f"{self.schema_url}/{fragment_extra}"
        schema = self.schema
        for component in path:
            if isinstance(component, str) and isinstance(schema, dict):
                schema = schema.get(component, None)
            elif isinstance(component, int) and isinstance(schema, (list, tuple)):
                if 0 <= component < len(schema):
                    schema = schema[component]
                else:
                    return None
            else:
                return None
        if not isinstance(schema, dict):
            return None
        return JsonSchema(
            schema_url=schema_url,
            schema=schema,
            root_url=self.root_url,
            root=self.root,
        )


KNOWN_TYPES: set[str] = {
    "boolean",
    "integer",
    "number",
    "string",
    "enum",
    "array",
    "tuple",
    "object",
    "resourceReference",
}


class DataMigrator:

    __known_migrations: ClassVar[dict[str, list["DataMigrator"]]] = {}

    target_types: set[str] = set()
    source_types: set[str] = set()
    priority: int = 0

    def __init_subclass__(cls) -> None:
        migrator: DataMigrator = cls()
        if not migrator.target_types:
            raise ValueError(
                "Data migrator instances must specify at least one target type!"
            )
        if not migrator.source_types:
            raise ValueError(
                "Data migrator instances must specify at least one source type!"
            )

        unknown_types = (
            set(migrator.target_types) | set(migrator.source_types)
        ) - KNOWN_TYPES
        if unknown_types:
            raise ValueError(
                f"Encountered data migrator for unknown types {unknown_types}."
            )

        for target_type in migrator.target_types:
            migrations = DataMigrator.__known_migrations.setdefault(target_type, [])
            migrations.append(migrator)
            migrations.sort(key=lambda m: m.priority, reverse=True)

    @staticmethod
    def get_migrators(target_type: str) -> Sequence["DataMigrator"]:
        """Get a list of data migrators by target type sorted by descending priority."""
        return DataMigrator.__known_migrations.get(target_type, tuple())

    @staticmethod
    def resolve_references(
        schema: JsonSchema, visited_set: set[str]
    ) -> tuple[JsonSchema, set[str], bool]:
        """Resolve any potential references in the given schema until a
        concrete schema is encountered.

        Args:
            schema (JsonSchema): the json schema that might be a reference
            visited_set (set[str]): the set of already visited schema ids

        Raises:
            RecursionError: If an unresolvable recusiive reference is encountered.

        Returns:
            tuple[JsonSchema, set[str], bool]:
            the updated input args and a boolean if a recursive resource
            reference was encountered
        """
        seen = set()
        seen.add(schema.schema_url)

        had_ref = "$ref" in schema.schema

        while "$ref" in schema.schema:
            reference: str = schema.schema["$ref"]
            if reference.startswith("#/definitions"):
                schema = schema.resolve_local(reference)
            else:
                root_url, fragment = reference.split("#", maxsplit=1)
                assert fragment.startswith("/definitions")
                resolved_ref = resolve_type_version_schema_url(url_string=reference)
                assert resolved_ref is not None
                schema = JsonSchema(root_url, resolved_ref).resolve_local(fragment)

            if schema.schema_url in seen:
                raise RecursionError(
                    "Recursive schema references cannot be resolved to a concrete schema!",
                    seen,
                )
            seen.add(schema.schema_url)

        is_recursive = had_ref and not visited_set.isdisjoint(seen)
        visited_set.update(seen)

        return schema, visited_set, is_recursive

    @classmethod
    def check_schema_changes(  # noqa: C901
        cls,
        source_schema: JsonSchema,
        target_schema: JsonSchema,
        *,
        source_visited_set: Optional[set[str]] = None,
        target_visited_set: Optional[set[str]] = None,
        depth: int = 0,
    ) -> Union[bool, Literal["recursion"]]:
        """
        Recursively check whether the proposed changes in the target schema
        allow for automatic data migrations.

        Args:
            source_schema (JsonSchema): Source JSON Schema
            target_schema (JsonSchema): Target JSON Schema
            source_visited_set (Optional[set[str]]): Stores visited schemas for source
            target_visited_set (Optional[set[str]]): Stores visited schemas for target
            depth (int, optional): Safety counter for recursion, stops at 100.

        Raises:
            Exception: If a schema is nested too deep.

        Returns:
            bool|"recursion": Returns True if schemas could be matched, else False
            if a recursive schema is encountered returns "recursion".
        """
        depth += 1
        if depth > 101:
            raise Exception("Schema nested too deep")

        if source_visited_set is None:
            source_visited_set = set()
        if target_visited_set is None:
            target_visited_set = set()

        try:
            source_schema, source_visited_set, is_recursive = cls.resolve_references(
                source_schema, source_visited_set
            )
            if is_recursive:
                return "recursion"

            target_schema, target_visited_set, is_recursive = cls.resolve_references(
                target_schema, target_visited_set
            )
            if is_recursive:
                return "recursion"
        except RecursionError:
            return False

        source_type, _ = extract_type(schema=source_schema.schema)
        target_type, _ = extract_type(schema=target_schema.schema)

        if source_type not in KNOWN_TYPES or target_type not in KNOWN_TYPES:
            return False

        for migrator in DataMigrator.get_migrators(target_type):
            if source_type not in migrator.source_types:
                continue
            if migrator.check_concrete_schema_change(
                source_type=source_type,
                target_type=target_type,
                source_schema=source_schema,
                target_schema=target_schema,
                source_visited_set=source_visited_set,
                target_visited_set=target_visited_set,
                depth=depth,
            ):
                return True
        return False

    def basic_check_concrete_schema_change(
        self,
        source_type: str,
        target_type: str,
        source_schema: dict,
        target_schema: dict,
    ) -> bool:
        """Fast check if a concrete schema change can be handled by this data
        migrator without checking recursively.

        This method should be implemented by the concrete data migrator.

        Args:
            source_type (str): the source type
            target_type (str): the target type
            source_schema (dict): source schema
            target_schema (dict): target schema

        Returns:
            bool: True if the data migration can be handled by this data migrator.
        """
        return False

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
        """Check if a concrete schema change can be handled by this data migrator.

        This method should be implemented by the concrete data migrator.

        This method must return False if basic_check_concrete_schema_change would return False!

        Args:
            source_type (str): the source type
            target_type (str): the target type
            source_schema (JsonSchema): source schema
            target_schema (JsonSchema): target schema
            source_visited_set (set[str]): set of visited schema ids for source.
            target_visited_set (set[str]): set of visited schema ids for target.
            depth (int): safety depth counter.

        Returns:
            bool: True if the data migration can be handled by this data migrator.
        """
        return self.basic_check_concrete_schema_change(
            source_type, target_type, source_schema.schema, target_schema.schema
        )

    @classmethod
    def migrate_data(  # noqa: C901
        cls,
        data,
        source_schema: JsonSchema,
        target_schema: JsonSchema,
        *,
        depth: int = 0,
        strict_check: bool = False,
    ):
        """Migrate data conforming to the source schema to the target schema
        using the available data migrators.

        Args:
            data (JSON): the json data to migrate.
            source_schema (JsonSchema): the source schema id and schema.
            target_schema (JsonSchema): the target schema id and schema.
            depth (int, optional): safety depth counter. Defaults to 0.
            strict_check (bool, optional): check schemas for compatibility before migrating data.
        """
        depth += 1
        if depth > 101:
            raise ValueError("Data nested too deep")

        if strict_check:
            result = cls.check_schema_changes(source_schema, target_schema)
            if not result or result == "recursion":
                raise ValueError("Schemas are not compatible, cannot migrate data!")

        try:
            source_schema, _, _ = cls.resolve_references(source_schema, set())

            target_schema, _, _ = cls.resolve_references(target_schema, set())
        except RecursionError:
            raise ValueError(
                "Schemas contain infinite reference loop, cannot migrate data!"
            )

        source_type, _ = extract_type(schema=source_schema.schema)
        target_type, _ = extract_type(schema=target_schema.schema)

        if source_type not in KNOWN_TYPES or target_type not in KNOWN_TYPES:
            raise ValueError(
                "Could not extract valid types from source and target schema!"
            )

        for migrator in DataMigrator.get_migrators(target_type):
            if source_type not in migrator.source_types:
                continue
            if migrator.basic_check_concrete_schema_change(
                source_type=source_type,
                target_type=target_type,
                source_schema=source_schema.schema,
                target_schema=target_schema.schema,
            ):
                try:
                    return migrator.migrate_data_concrete(
                        data=data,
                        source_type=source_type,
                        target_type=target_type,
                        source_schema=source_schema,
                        target_schema=target_schema,
                        depth=depth,
                    )
                except NotImplementedError:
                    continue

        raise ValueError("No data migrator found to migrate data!")

    def migrate_data_concrete(
        self,
        data,
        source_type: str,
        target_type: str,
        source_schema: JsonSchema,
        target_schema: JsonSchema,
        *,
        depth: int = 0,
    ):
        """Migrate data conforming to the source schema to the target schema.

        This method should be implemented by the concrete data migrator.

        Args:
            data (JSON): the json data to migrate.
            source_type (str): the source type
            target_type (str): the target type
            source_schema (JsonSchema): the source schema.
            target_schema (JsonSchema): the target schema.
            depth (int, optional): safety depth counter. Defaults to 0.
        """
        raise NotImplementedError()

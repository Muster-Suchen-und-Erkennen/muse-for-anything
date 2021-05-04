"""Collection of classes for working with jsonschema objects."""

from collections import deque
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)
from re import search
from functools import reduce

__all__ = [
    "SchemaWalker",
    "DataWalker",
    "DataWalkerVisitor",
    "DataWalkerException",
    "DataVisitorException",
]


class SchemaWalker:
    __slots__ = (
        "cache",
        "path",
        "schema",
        "resolved_schema",
        "resolve_error",
        "url_resolver",
    )

    def __init__(
        self,
        schema: Union[Dict[str, Any], Sequence[Tuple[str, Dict[str, Any]]]],
        url_resolver: Callable[[str], Optional[Dict[str, Any]]],
        cache: Optional[Dict[str, Dict[str, Any]]] = None,
        path: Optional[Tuple[Union[str, int], ...]] = None,
    ) -> None:
        self.path = path if path else tuple()
        self.url_resolver = url_resolver
        self.cache = cache if cache is not None else {}
        if isinstance(schema, Sequence):
            self.schema = tuple(
                (a, s) for a, s in schema if s and s is not True
            )  # filter out empty schemas
        else:
            if not schema:
                raise ValueError("Schema cannot be None or Empty!")
            self.cache["ROOT"] = schema
            self.schema = [("ROOT", schema)]
        try:
            self.resolved_schema = self._ref_resolve(self.schema)
            self.resolve_error = None
        except KeyError as err:
            self.resolved_schema = None
            self.resolve_error = err

    @property
    def is_resolved(self) -> bool:
        return self.resolve_error is None and self.resolved_schema is not None

    def _get_attributes(self, resolved: bool = False) -> Set[str]:
        attributes = set()
        for _, schema in self.resolved_schema if resolved else self.schema:
            attributes.update(schema.keys())
        return attributes

    @property
    def attributes(self) -> Set[str]:
        return self._get_attributes()

    @property
    def resolved_attributes(self) -> Set[str]:
        return self._get_attributes(resolved=True)

    def _get_attribute(self, attr: str, resolved: bool = False) -> List[Any]:
        attribute_values = []
        for _, schema in self.resolved_schema if resolved else self.schema:
            if attr in schema:
                attribute_values.append(schema[attr])
        return attribute_values

    def get_attribute(self, attr: str) -> List[Any]:
        return self._get_attribute(attr)

    def get_resolved_attribute(self, attr: str) -> List[Any]:
        return self._get_attribute(attr, resolved=True)

    def _get_type(self, resolved: bool = False) -> Set[str]:
        types_set = self._get_attribute("type", resolved=resolved)
        types_sets = (
            set((t,)) if isinstance(t, str) else set(t)
            for t in types_set
            if t is not None
        )

        def type_reducer(a, b):
            if a is None:
                return b
            if b is None:
                return a
            return a & b

        reduced_type_set = reduce(type_reducer, types_sets, None)
        if reduced_type_set is None:
            return set()
        return reduced_type_set

    @property
    def json_type(self) -> Set[str]:
        return self._get_type()

    @property
    def json_type_resolved(self) -> Set[str]:
        return self._get_type(resolved=True)

    @property
    def is_consistent_type(self) -> bool:
        if not self.is_resolved:
            return False
        type_set = self.get_resolved_attribute("type")
        type_set.remove("null")
        return len(type_set) <= 1

    def _get_main_type(self, resolved: bool = False) -> str:
        if "http://json-schema.org/draft-07/schema#" in self._get_attribute(
            "$schema", resolved
        ) and self._get_attribute("definitions", resolved=resolved):
            return "schema-root"
        type_set = self._get_type(resolved=resolved)
        if "object" in type_set:
            return "object"
        if "array" in type_set:
            return "array"
        if "string" in type_set:
            return "string"
        if "number" in type_set:
            return "number"
        if "integer" in type_set:
            return "integer"
        if "boolean" in type_set:
            return "boolean"
        if "null" in type_set:
            return "null"
        return "any"

    @property
    def main_type(self) -> str:
        return self._get_main_type()

    @property
    def main_type_resolved(self) -> str:
        return self._get_main_type(resolved=True)

    def _get_secondary_type(self, resolved: bool = False) -> Optional[str]:
        main_type = self._get_main_type(resolved=resolved)
        schemas = self.resolved_schema if resolved else self.schema
        if main_type == "object":
            for _, schema in reversed(schemas):
                if "customType" in schema:
                    return schema["customType"]
        elif main_type == "array":
            pass  # TODO tuples vs arrays
        return None

    @property
    def secondary_type(self) -> Optional[str]:
        return self._get_secondary_type()

    @property
    def secondary_type_resolved(self) -> Optional[str]:
        return self._get_secondary_type(resolved=True)

    @property
    def properties_resolved(self) -> Set[str]:
        if self.main_type_resolved != "object":
            return set()
        props = set()
        property_dicts = cast(
            Set[Dict[str, Any]], self.get_resolved_attribute("properties")
        )
        for prop_dict in property_dicts:
            props.update(prop_dict.keys())
        return props

    def _get_resolved_object_property(self, prop: str) -> "SchemaWalker":
        schemas = []
        for anchor, schema in self.resolved_schema:
            prop_schema = schema.get("properties", {}).get(prop)
            schemas.append((anchor, prop_schema))

            used_pattern_property = False
            if "patternProperties" in schema:
                for pattern, prop_schema in schema["patternProperties"].items():
                    if search(pattern, prop):
                        schemas.append((anchor, prop_schema))
                        used_pattern_property = True
            if not used_pattern_property and prop_schema is None:
                schemas.append((anchor, schema.get("additionalProperties", None)))
        return SchemaWalker(
            schema=schemas,
            url_resolver=self.url_resolver,
            cache=self.cache,
            path=cast(Tuple[Union[str, int], ...], (*self.path, prop)),
        )

    def _get_resolved_array_item(self, item: int) -> "SchemaWalker":
        schemas = []
        for anchor, schema in self.resolved_schema:
            item_schema = schema.get("items")
            if isinstance(item_schema, Sequence):
                if item < len(item_schema):
                    item_schema = item_schema[item]
                else:
                    item_schema = None
            if item_schema is not None:
                schemas.append((anchor, item_schema))
                continue
            if "additionalItems" in schema:
                schemas.append((anchor, schema["additionalItems"]))
        return SchemaWalker(
            schema=schemas,
            url_resolver=self.url_resolver,
            cache=self.cache,
            path=cast(Tuple[Union[str, int], ...], (*self.path, item)),
        )

    def __getitem__(self, item) -> "SchemaWalker":
        if not self.is_resolved:
            raise IndexError("Schema is not resolved!")
        main_type = self.main_type_resolved
        if main_type == "object":
            if not isinstance(item, str):
                raise TypeError("Item must be of type str for object properties!")
            return self._get_resolved_object_property(item)
        elif main_type == "array":
            if not isinstance(item, int):
                raise TypeError("Item must be of type int for array items!")
            return self._get_resolved_array_item(item)
        raise IndexError("Schema is not indexable!")

    def _fetch_schema(self, anchor: str) -> Dict[str, Any]:
        try:
            return self.cache[anchor]
        except KeyError:
            schema = self.url_resolver(anchor)
            if schema is None:
                raise KeyError(f"No schema found under URL '{anchor}'")
            self.cache[anchor] = schema
            return schema

    def _resolve_single_ref(self, anchor, schema) -> Tuple[str, Dict[str, Any]]:
        ref = cast(str, schema["$ref"])
        if not ref.startswith("#"):
            # split anchor and ref from full url reference
            if "#" in ref:
                anchor, ref_part = ref.split("#", maxsplit=1)
            else:
                anchor, ref_part = ref, ""
            ref = f"#{ref_part}"

        # resolve ref
        if ref.startswith("#/definitions/"):
            ref_schema = self._fetch_schema(anchor)
            try:
                return anchor, ref_schema["definitions"][ref[14:]]  # can raise KeyError
            except KeyError:
                raise KeyError(f"No schema with ref '{ref}' found for anchor '{anchor}'")
        elif ref == "#":
            return anchor, self._fetch_schema(anchor)
        elif ref.startswith("#"):
            ref_schema = self._fetch_schema(anchor)
            defs = ref_schema["definitions"]
            for candidate_schema in defs.values():
                if candidate_schema.get("$id") == ref:
                    return anchor, candidate_schema
            else:
                raise KeyError(f"No schema with ref '{ref}' found for anchor '{anchor}'")
        raise KeyError(f"No schema with ref '{ref}' found for anchor '{anchor}'")

    def _ref_resolve(
        self, schemas: Sequence[Tuple[str, Dict[str, Any]]]
    ) -> Sequence[Tuple[str, Dict[str, Any]]]:
        def schema_generator(schemas: Iterable[Tuple[str, Dict[str, Any]]]):
            stack = deque(schemas)
            while stack:
                anchor, schema = stack.popleft()
                if "$ref" in schema:
                    resolved_schema = self._resolve_single_ref(anchor, schema)
                    stack.appendleft(resolved_schema)
                    continue  # TODO title and description attributes?
                if "allOf" in schema:
                    yield from schema_generator(
                        (anchor, sub_schema) for sub_schema in schema["allOf"]
                    )
                yield (anchor, schema)

        return tuple(
            (a, s) for a, s in schema_generator(schemas) if s and s is not True
        )  # filter out empty schemas


class DataWalkerException(Exception):
    def __init__(
        self,
        *args: object,
        accumulated_errors: List[
            Tuple[SchemaWalker, Exception, Any, Union[str, Any]]
        ] = [],
    ) -> None:
        super().__init__(*args)
        self.accumulated_errors = accumulated_errors


class DataWalker:
    __slots__ = ("data", "schema_walker", "visitors", "errors")

    def __init__(
        self,
        data: Any,
        schema_walker: SchemaWalker,
        visitors: Optional[Sequence[Callable[[Any, SchemaWalker], None]]],
    ) -> None:
        self.data = data
        self.schema_walker = schema_walker
        self.visitors: Sequence[Callable[[Any, SchemaWalker], None]] = (
            visitors if visitors else tuple()
        )
        self.errors: List[Tuple[SchemaWalker, Exception, Any, Union[str, Any]]] = []

    def walk(self, greedy: bool = True):
        stack: Deque[Tuple[Any, SchemaWalker]] = deque()
        stack.append((self.data, self.schema_walker))
        while stack:
            data, walker = stack.pop()
            for visitor in self.visitors:
                try:
                    visitor(data, walker)
                except Exception as err:
                    self.errors.append((walker, err, data, visitor))
            if not greedy and self.errors:
                raise DataWalkerException(accumulated_errors=self.errors)
            if data is None:
                continue
            try:
                self.decend(data, walker, stack)
            except Exception as err:
                self.errors.append((walker, err, data, "decend"))
            if not greedy and self.errors:
                raise DataWalkerException(accumulated_errors=self.errors)
        if self.errors:
            raise DataWalkerException(accumulated_errors=self.errors)

    def decend(
        self,
        data: Any,
        walker: SchemaWalker,
        stack: Deque[Tuple[Any, SchemaWalker]],
        transform_step: Optional[
            Callable[[Tuple[Any, SchemaWalker]], Tuple[Any, SchemaWalker]]
        ] = None,
    ) -> None:
        main_type = walker.main_type_resolved
        if main_type == "object":
            for prop in data.keys():
                try:
                    next_step = (data[prop], walker[prop])
                    if transform_step is not None:
                        next_step = transform_step(next_step)
                    stack.append(next_step)
                except Exception as err:
                    self.errors.append((walker, err, data, f"property-decend {prop}"))
        elif main_type == "array":
            for item in range(len(data)):
                try:
                    next_step = (data[item], walker[item])
                    if transform_step is not None:
                        next_step = transform_step(next_step)
                    stack.append(next_step)
                except Exception as err:
                    self.errors.append((walker, err, data, f"item-decend {item}"))


class DataVisitorException(Exception):
    pass


class DataWalkerVisitor:
    __slots__ = ("always",)

    def __init__(self, always: bool = False) -> None:
        self.always = always

    def test(self, data, walker: SchemaWalker) -> bool:
        return self.always

    def visit(self, data, walker: SchemaWalker) -> None:
        return

    def __call__(self, data, walker: SchemaWalker) -> Any:
        if self.test(data, walker):
            self.visit(data, walker)

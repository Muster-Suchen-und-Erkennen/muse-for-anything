"""Module containing validation functions for object types."""

from flask import current_app, request, url_for
from flask.globals import _request_ctx_stack
from sqlalchemy.orm import query
from werkzeug.urls import url_parse

from http import HTTPStatus

from muse_for_anything.api.json_schema.schema_tools import SchemaWalker
from typing import Any, Callable, Deque, Optional, Sequence, Tuple
from flask_babel import gettext
from jsonschema import Draft7Validator

from flask_smorest import abort

from muse_for_anything.db.models.ontology_objects import OntologyObjectTypeVersion
from .models.schema import TYPE_SCHEMA
from ..json_schema import DataWalker, DataWalkerVisitor, DataWalkerException


SCHEMA_VALIDATOR = Draft7Validator(TYPE_SCHEMA)


def validate_against_type_schema(schema: Any):
    # FIXME add proper error reporting for api client
    validation_errors = []
    for error in sorted(SCHEMA_VALIDATOR.iter_errors(schema), key=str):
        print("VALIDATION ERROR", error.message)
        validation_errors.append(error)
    if validation_errors:
        abort(
            HTTPStatus.BAD_REQUEST,
            message=gettext("The object type does not conform to the json schema!"),
            # errors=validation_errors,
        )


class TypeSchemaDataWalker(DataWalker):
    def __init__(
        self,
        data: Any,
        schema_walker: SchemaWalker,
        visitors: Optional[Sequence[Callable[[Any, SchemaWalker], None]]],
    ) -> None:
        super().__init__(data, schema_walker, visitors)

    def _copy_walker(self, walker: SchemaWalker, extra_schema_ref: str) -> SchemaWalker:
        anchor, _ = walker.schema[-1]
        return SchemaWalker(
            schema=(*walker.schema, (anchor, {"$ref": extra_schema_ref})),
            url_resolver=walker.url_resolver,
            cache=walker.cache,
            path=walker.path,
        )

    def decend(
        self, data: Any, walker: SchemaWalker, stack: Deque[Tuple[Any, SchemaWalker]]
    ) -> None:
        if walker.secondary_type_resolved == "typeDefinition":
            if "type" in data:
                data_type = data["type"]
                if isinstance(data_type, str):
                    data_type = (data_type,)
                if "boolean" in data_type:
                    walker = self._copy_walker(walker, "#/definitions/boolean")
                elif "integer" in data_type:
                    walker = self._copy_walker(walker, "#/definitions/integer")
                elif "number" in data_type:
                    walker = self._copy_walker(walker, "#/definitions/number")
                elif "string" in data_type:
                    walker = self._copy_walker(walker, "#/definitions/string")
                elif "array" in data_type:
                    if data.get("arrayType") == "tuple":
                        walker = self._copy_walker(walker, "#/definitions/tuple")
                    else:
                        walker = self._copy_walker(walker, "#/definitions/array")
                elif "object" in data_type:
                    # print(data)
                    if "resourceReference" == data.get("customType"):
                        walker = self._copy_walker(
                            walker, "#/definitions/resourceReference"
                        )
                    elif "$ref" in data:
                        walker = self._copy_walker(walker, "#/definitions/ref")
                    else:
                        walker = self._copy_walker(walker, "#/definitions/object")
                else:
                    # TODO extend this function for new type definitions
                    print("Unknown type definition!")
            elif "enum" in data:
                walker = self._copy_walker(walker, "#/definitions/enum")
        super().decend(data, walker, stack)


class RefVisitor(DataWalkerVisitor):
    def test(self, data, walker: SchemaWalker) -> bool:
        return "$ref" in walker.properties_resolved and "$ref" in data

    def visit(self, data, walker: SchemaWalker) -> None:
        ref: str = data["$ref"]
        if ref.startswith("#/definitions/"):
            try:
                data["definitions"][ref[14:]]
            except KeyError:
                DataWalkerException(f"Unknown local schema reference '{ref}'!")
        elif ref.startswith("#"):
            for schema in data.get("definitions", {}).values():
                if schema["$id"] == ref:
                    break
            else:
                DataWalkerException(
                    f"Unknown local schema reference '{ref}'! No schema with matching id!"
                )
        else:
            # TODO test external type reference and add it to reference list
            print(data["$ref"], walker)


def validate_object_type(type_version: OntologyObjectTypeVersion):
    # validate_against_type_schema(type_version.data)
    walker = TypeSchemaDataWalker(
        type_version.data,
        SchemaWalker(TYPE_SCHEMA, lambda x: None),
        visitors=[RefVisitor()],
    )

    print("\n\n", "Walking data:")

    ctx = _request_ctx_stack.top
    url = url_parse("http://localhost:5000/api/v1/namespaces/1/types/3/versions/1/")
    print(url.host, url.port, url.path, url.query, url.netloc, type(url))
    print(
        ctx.url_adapter.get_host("test"),
        ctx.url_adapter.get_host("") == url.netloc,
    )
    print(
        ctx.url_adapter.match(path_info=url.path, query_args=url.query)
    )  # current_app.url_map
    walker.walk()
    print(walker.errors)

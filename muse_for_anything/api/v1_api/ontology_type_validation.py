"""Module containing validation functions for object types."""

from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Callable, Deque, Dict, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse

from flask.globals import request_ctx
from flask_babel import gettext
from flask_smorest import abort
from jsonschema import Draft7Validator
from werkzeug.routing import MapAdapter

from muse_for_anything.api.json_schema.schema_tools import SchemaWalker
from muse_for_anything.db.models.ontology_objects import (
    OntologyObjectType,
    OntologyObjectTypeVersion,
)
from muse_for_anything.db.models.taxonomies import Taxonomy

from ..json_schema import DataVisitorException, DataWalker, DataWalkerVisitor
from .models.schema import TYPE_SCHEMA

SCHEMA_VALIDATOR = Draft7Validator(TYPE_SCHEMA)


ALLOWED_SCHEMA_ENDPOINTS = set(["api-v1.TypeVersionView"])


@dataclass
class SchemaMetadata:
    imported_types: Set[OntologyObjectTypeVersion]
    referenced_types: Set[OntologyObjectType]
    referenced_taxonomies: Set[Taxonomy]


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
    """SchemaWalker for decending with the type schema."""

    def __init__(
        self,
        data: Any,
        schema_walker: SchemaWalker,
        visitors: Optional[Sequence[Callable[[Any, SchemaWalker], None]]],
    ) -> None:
        super().__init__(data, schema_walker, visitors)

    def _copy_walker(self, walker: SchemaWalker, inject_schema_ref: str) -> SchemaWalker:
        anchor, _ = walker.schema[-1]
        return SchemaWalker(
            schema=(*walker.schema, (anchor, {"$ref": inject_schema_ref})),
            url_resolver=walker.url_resolver,
            cache=walker.cache,
            path=walker.path,
        )

    def transform_decend_step(
        self, step: Tuple[Any, SchemaWalker]
    ) -> Tuple[Any, SchemaWalker]:
        """Transform the decend step if the next type is a typeDefinition."""
        data, walker = step
        if walker.secondary_type_resolved == "typeDefinition":
            # typeDefinitions use "oneOf" which is not supported by default
            # this transformation manually applies the correct schema
            if "type" in data:
                data_type = data["type"]
                if isinstance(data_type, str):
                    data_type = (data_type,)
                if "boolean" in data_type:
                    return data, self._copy_walker(walker, "#/definitions/boolean")
                elif "integer" in data_type:
                    return data, self._copy_walker(walker, "#/definitions/integer")
                elif "number" in data_type:
                    return data, self._copy_walker(walker, "#/definitions/number")
                elif "string" in data_type:
                    return data, self._copy_walker(walker, "#/definitions/string")
                elif "array" in data_type:
                    if data.get("arrayType") == "tuple":
                        return data, self._copy_walker(walker, "#/definitions/tuple")
                    else:
                        return data, self._copy_walker(walker, "#/definitions/array")
                elif "object" in data_type:
                    # print(data)
                    if "resourceReference" == data.get("customType"):
                        return data, self._copy_walker(
                            walker, "#/definitions/resourceReference"
                        )
                    else:
                        return data, self._copy_walker(walker, "#/definitions/object")
                else:
                    # TODO extend this function for new type definitions
                    print("Unknown type definition!")
            elif "enum" in data:
                return data, self._copy_walker(walker, "#/definitions/enum")
            elif "$ref" in data:
                return data, self._copy_walker(walker, "#/definitions/ref")
        return step

    def decend(
        self, data: Any, walker: SchemaWalker, stack: Deque[Tuple[Any, SchemaWalker]]
    ) -> None:
        super().decend(data, walker, stack, transform_step=self.transform_decend_step)


class RefVisitor(DataWalkerVisitor):
    """SchemaWalker visitor for validating and extracting json schema references ('$ref' attribute)."""

    def __init__(
        self,
        restrict_to_namespace: Optional[int] = None,
        self_ref_type_version_id: Optional[int] = None,
    ) -> None:
        super().__init__(always=False)
        self.references: Set[OntologyObjectTypeVersion] = set()
        self.restrict_to_namespace = restrict_to_namespace
        self.self_ref_type_version_id = self_ref_type_version_id

    def test(self, data, walker: SchemaWalker) -> bool:
        return "$ref" in walker.properties_resolved and "$ref" in data

    def visit(self, data, walker: SchemaWalker) -> None:
        ref: str = data["$ref"]
        if ref.startswith("#/definitions/"):
            try:
                data["definitions"][ref[14:]]
            except KeyError:
                DataVisitorException(f"Unknown local schema reference '{ref}'!")
        elif ref.startswith("#"):
            for schema in data.get("definitions", {}).values():
                if schema["$id"] == ref:
                    break
            else:
                DataVisitorException(
                    f"Unknown local schema reference '{ref}'! No schema with matching id!"
                )
        else:
            url = urlparse(data["$ref"])

            ctx = request_ctx
            if ctx is None:
                raise DataVisitorException(
                    "No request context to check schema url against!"
                )
            url_adapter: Optional[MapAdapter] = ctx.url_adapter
            if url_adapter is None:
                raise DataVisitorException(
                    "No url adapter found in request context! Unable to check URL."
                    f"URL: '{url}'"
                )
            if url.netloc != url_adapter.get_host(None):
                raise DataVisitorException(
                    "Only references to schemas on the same MUSE4Anything instance allowed! "
                    f"Current instance: '{url_adapter.get_host(None)}' ref: '{url}'"
                )
            endpoint, params = url_adapter.match(
                path_info=url.path, query_args=url.query, method="GET"
            )
            if endpoint not in ALLOWED_SCHEMA_ENDPOINTS:
                raise DataVisitorException(
                    "Only references to schemas on the same MUSE4Anything instance allowed! "
                    f"Current instance: '{url_adapter.get_host(None)}' ref: '{url}'"
                )
            self.extract_type_reference(url, endpoint, **params)

    def check_params(
        self, namespace: str, object_type: str, version: str
    ) -> Tuple[int, int, int]:
        if not namespace or not namespace.isdigit():
            raise DataVisitorException(
                f"Invalid schema ref! Namespace id {namespace} is not correctly formatted."
            )
        if not object_type or not object_type.isdigit():
            raise DataVisitorException(
                f"Invalid schema ref! Object type id {object_type} is not correctly formatted."
            )
        if not version or not version.isdigit():
            raise DataVisitorException(
                f"Invalid schema ref! Version {version} is not correctly formatted."
            )

        if self.restrict_to_namespace is not None:
            if namespace != str(self.restrict_to_namespace):
                raise DataVisitorException(
                    f"Invalid schema ref! Only schemas in namespace {self.restrict_to_namespace} are allowed but got namespace {namespace}."
                )

        if self.self_ref_type_version_id is not None:
            if object_type == str(self.self_ref_type_version_id):
                raise DataVisitorException(
                    f"Invalid schema ref! A type cannot reference any version of itself!."
                )

        return int(namespace), int(object_type), int(version)

    def extract_type_reference(
        self, url, endpoint, namespace: str, object_type: str, version: str, **kwargs
    ):
        if endpoint == "api-v1.TypeVersionView":
            namespace_id, object_type_id, version_number = self.check_params(
                namespace=namespace, object_type=object_type, version=version
            )

            found_type_version: Optional[OntologyObjectTypeVersion] = (
                OntologyObjectTypeVersion.query.filter(
                    OntologyObjectTypeVersion.version == version_number,
                    OntologyObjectTypeVersion.object_type_id == object_type_id,
                ).first()
            )

            if (
                found_type_version is None
                or found_type_version.ontology_type.namespace_id != namespace_id
                or found_type_version.deleted_on is not None
                or found_type_version.ontology_type.deleted_on is not None
                or found_type_version.ontology_type.namespace.deleted_on is not None
            ):
                raise DataVisitorException(
                    f"Invalid schema ref! Schema '{url}' not found!"
                )

            self.references.add(found_type_version)


TAXONOMY_ITEM_REFERENCE_TYPE = {"const": "ont-taxonomy-item"}
OBJECT_REFERENCE_TYPE = {"const": "ont-object"}


class ResourceReferenceVisitor(DataWalkerVisitor):
    """SchemaWalker visitor for validating and extracting type and taxonomy resource references."""

    def __init__(self, restrict_to_namespace: Optional[int] = None) -> None:
        super().__init__(always=False)
        self.taxonomy_references: Set[Taxonomy] = set()
        self.object_type_references: Set[OntologyObjectType] = set()
        self.restrict_to_namespace = restrict_to_namespace

    def test(self, data, walker: SchemaWalker) -> bool:
        return (
            "resourceReferenceDefinition" == walker.secondary_type_resolved
            and data.get("customType") == "resourceReference"
        )

    def visit(self, data, walker: SchemaWalker) -> None:
        if data["referenceType"] == "ont-taxonomy":
            if data["properties"]["referenceType"] != TAXONOMY_ITEM_REFERENCE_TYPE:
                raise DataVisitorException(
                    f"Malformed taxonomy reference definition! Expected {TAXONOMY_ITEM_REFERENCE_TYPE} but got {data['properties']['referenceType']}"
                )
            if not data.get("referenceKey"):
                raise DataVisitorException(
                    f"Malformed taxonomy reference definition! Reference definition must contain a resource key of a taxonomy."
                )
            self.check_taxonomy_key(data["referenceKey"])
        if data["referenceType"] == "ont-type":
            if data["properties"]["referenceType"] != OBJECT_REFERENCE_TYPE:
                raise DataVisitorException(
                    f"Malformed object type reference definition! Expected {OBJECT_REFERENCE_TYPE} but got {data['properties']['referenceType']}"
                )
            if data.get("referenceKey"):
                self.check_object_type_key(data["referenceKey"])

    def check_taxonomy_key(self, key: Dict[str, str]):
        namespace = key.get("namespaceId", "")
        taxonomy = key.get("taxonomyId", "")
        if not namespace or not namespace.isdigit():
            raise DataVisitorException(
                f"Invalid taxonomy key! NamespaceId {namespace} is not correctly formatted."
            )
        if not taxonomy or not taxonomy.isdigit():
            raise DataVisitorException(
                f"Invalid taxonomy key! TaxonomyId {taxonomy} is not correctly formatted."
            )

        if self.restrict_to_namespace is not None:
            if namespace != str(self.restrict_to_namespace):
                raise DataVisitorException(
                    f"Invalid taxonomy key! Only taxonomies in namespace {self.restrict_to_namespace} are allowed but got namespace {namespace}."
                )

        found_taxonomy: Optional[Taxonomy] = Taxonomy.query.filter(
            Taxonomy.id == int(taxonomy),
            Taxonomy.namespace_id == int(namespace),
        ).first()

        if (
            found_taxonomy is None
            or found_taxonomy.deleted_on is not None
            or found_taxonomy.namespace.deleted_on is not None
        ):
            raise DataVisitorException(
                f"Invalid taxonomy key! No taxonomy found for key {key}."
            )
        self.taxonomy_references.add(found_taxonomy)

    def check_object_type_key(self, key: Dict[str, str]):
        namespace = key.get("namespaceId", "")
        object_type = key.get("typeId", "")
        if not namespace or not namespace.isdigit():
            raise DataVisitorException(
                f"Invalid object type key! NamespaceId {namespace} is not correctly formatted."
            )
        if not object_type or not object_type.isdigit():
            raise DataVisitorException(
                f"Invalid object type key! ObjectTypeId {object_type} is not correctly formatted."
            )

        if self.restrict_to_namespace is not None:
            if namespace != str(self.restrict_to_namespace):
                raise DataVisitorException(
                    f"Invalid object type key! Only object types in namespace {self.restrict_to_namespace} are allowed but got namespace {namespace}."
                )

        found_object_type: Optional[OntologyObjectType] = OntologyObjectType.query.filter(
            OntologyObjectType.id == int(object_type),
            OntologyObjectType.namespace_id == int(namespace),
        ).first()

        if (
            found_object_type is None
            or found_object_type.deleted_on is not None
            or found_object_type.namespace.deleted_on is not None
        ):
            raise DataVisitorException(
                f"Invalid object type key! No object type found for key {key}."
            )
        self.object_type_references.add(found_object_type)


def validate_object_type(type_version: OntologyObjectTypeVersion) -> SchemaMetadata:
    # validate schema
    validate_against_type_schema(type_version.data)

    # setup schema walker
    ref_visitor = RefVisitor(
        restrict_to_namespace=type_version.ontology_type.namespace_id,
        self_ref_type_version_id=type_version.object_type_id,
    )
    resource_reference_visitor = ResourceReferenceVisitor(
        restrict_to_namespace=type_version.ontology_type.namespace_id
    )
    walker = TypeSchemaDataWalker(
        type_version.data,
        SchemaWalker(TYPE_SCHEMA, lambda x: None),
        visitors=[ref_visitor, resource_reference_visitor],
    )

    # walk schema to validate and extract references
    walker.walk()  # FIXME add proper error reporting for api client

    # return extracted references
    return SchemaMetadata(
        imported_types=ref_visitor.references,
        referenced_types=resource_reference_visitor.object_type_references,
        referenced_taxonomies=resource_reference_visitor.taxonomy_references,
    )

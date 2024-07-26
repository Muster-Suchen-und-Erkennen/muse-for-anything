"""Module containing validation functions for objects."""

from dataclasses import dataclass

from urllib.parse import urlparse

from muse_for_anything.db.models.taxonomies import TaxonomyItem
from flask.globals import request_ctx
from werkzeug.routing import MapAdapter

from http import HTTPStatus

from muse_for_anything.api.json_schema.schema_tools import SchemaWalker
from typing import Any, Dict, Optional, Set
from flask_babel import gettext
from jsonschema import Draft7Validator

from flask_smorest import abort

from muse_for_anything.db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectTypeVersion,
    OntologyObjectVersion,
)
from ..json_schema import DataWalker, DataWalkerVisitor, DataVisitorException


@dataclass
class ObjectMetadata:
    referenced_objects: Set[OntologyObject]
    referenced_taxonomy_items: Set[TaxonomyItem]


ALLOWED_SCHEMA_ENDPOINTS = set(["api-v1.TypeVersionView"])


def resolve_type_version_schema_url(url_string: str):
    """Resolver url references without creating any http request by directly querying the database."""
    # TODO use url cache
    url = urlparse(url_string)
    # url should already be from a validated type!
    ctx = request_ctx
    # TODO Safety check will probably never trigger
    if ctx is None:
        raise DataVisitorException("No request context to check schema url against!")
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

    # should already be validated!
    namespace: str = params.get("namespace")
    object_type: str = params.get("object_type")
    version: str = params.get("version")
    if endpoint == "api-v1.TypeVersionView":

        found_type_version: Optional[OntologyObjectTypeVersion] = (
            OntologyObjectTypeVersion.query.filter(
                OntologyObjectTypeVersion.version == int(version),
                OntologyObjectTypeVersion.object_type_id == int(object_type),
            ).first()
        )

        if found_type_version is None:
            raise DataVisitorException(f"Invalid schema ref! Schema '{url}' not found!")

        return found_type_version.data


def validate_object_against_schema(
    object_data: Any, type_version: OntologyObjectTypeVersion
):
    validator = Draft7Validator(type_version.data)

    # add internal resolver function
    validator.resolver.handlers["http"] = resolve_type_version_schema_url
    validator.resolver.handlers["https"] = resolve_type_version_schema_url

    # FIXME add proper error reporting for api client
    validation_errors = []
    for error in sorted(validator.iter_errors(object_data), key=str):
        print("VALIDATION ERROR", error.message)
        validation_errors.append(error)
    if validation_errors:
        abort(
            HTTPStatus.BAD_REQUEST,
            message=gettext("The object does not conform to the type json schema!"),
            # errors=validation_errors,
        )


class ResourceReferenceVisitor(DataWalkerVisitor):
    """SchemaWalker visitor for validating and extracting object and taxonomy item resource references."""

    def __init__(self, restrict_to_namespace: Optional[int] = None) -> None:
        super().__init__(always=False)
        self.taxonomy_item_references: Set[TaxonomyItem] = set()
        self.object_references: Set[OntologyObject] = set()
        self.restrict_to_namespace = restrict_to_namespace

    def test(self, data, walker: SchemaWalker) -> bool:
        return "resourceReference" == walker.secondary_type_resolved

    def visit(self, data, walker: SchemaWalker) -> None:
        if "ont-taxonomy" in walker.get_resolved_attribute("referenceType"):
            if data["referenceType"] != "ont-taxonomy-item":
                raise DataVisitorException(
                    f"Malformed taxonomy item reference! Expected 'ont-taxonomy-item' but got {data['referenceType']}"
                )
            if not data.get("referenceKey"):
                raise DataVisitorException(
                    f"Malformed taxonomy item reference! Reference must contain a resource key of a taxonomy item."
                )
            taxonomy_key = walker.get_resolved_attribute("referenceKey")[-1]
            self.check_taxonomy_item_key(data["referenceKey"], taxonomy_key=taxonomy_key)
        if "ont-type" in walker.get_resolved_attribute("referenceType"):
            if data["referenceType"] != "ont-object":
                raise DataVisitorException(
                    f"Malformed object reference! Expected 'ont-object' but got {data['referenceType']}"
                )
            if not data.get("referenceKey"):
                raise DataVisitorException(
                    f"Malformed object reference! Reference must contain a resource key of an object."
                )
            type_keys = walker.get_resolved_attribute("referenceKey")
            type_key = type_keys[-1] if type_keys else None
            self.check_object_key(data["referenceKey"], type_key=type_key)

    def check_taxonomy_item_key(self, key: Dict[str, str], taxonomy_key: Dict[str, str]):
        namespace = key.get("namespaceId", "")
        taxonomy = key.get("taxonomyId", "")
        taxonomy_item = key.get("taxonomyItemId", "")
        if namespace != taxonomy_key.get("namespaceId"):
            raise DataVisitorException(
                f"Invalid taxonomy item key! Expected namespaceId {taxonomy_key.get('namespaceId')} but got {namespace}."
            )
        if taxonomy != taxonomy_key.get("taxonomyId"):
            raise DataVisitorException(
                f"Invalid taxonomy item key! Expected taxonomyId {taxonomy_key.get('taxonomyId')} but got {taxonomy}."
            )
        if not taxonomy_item or not taxonomy_item.isdigit():
            raise DataVisitorException(
                f"Invalid taxonomy item key! TaxonomyItemId {taxonomy_item} is not correctly formatted."
            )

        found_taxonomy_item: Optional[TaxonomyItem] = TaxonomyItem.query.filter(
            TaxonomyItem.id == int(taxonomy_item),
            TaxonomyItem.taxonomy_id == int(taxonomy),
        ).first()

        if found_taxonomy_item is None or found_taxonomy_item.deleted_on is not None:
            raise DataVisitorException(
                f"Invalid taxonomy item key! No taxonomy item found for key {key}."
            )
        self.taxonomy_item_references.add(found_taxonomy_item)

    def check_object_key(self, key: Dict[str, str], type_key: Optional[Dict[str, str]]):
        namespace = key.get("namespaceId", "")
        object_id = key.get("objectId", "")

        if type_key and namespace != type_key.get("namespaceId"):
            raise DataVisitorException(
                f"Invalid object key! Expected namespaceId {type_key.get('namespaceId')} but got {namespace}."
            )
        elif self.restrict_to_namespace is not None:
            if namespace != str(self.restrict_to_namespace):
                raise DataVisitorException(
                    f"Invalid object key! Only objects in namespace {self.restrict_to_namespace} are allowed but got namespace {namespace}."
                )

        if not namespace or not namespace.isdigit():
            raise DataVisitorException(
                f"Invalid object type key! NamespaceId {namespace} is not correctly formatted."
            )
        if not object_id or not object_id.isdigit():
            raise DataVisitorException(
                f"Invalid object type key! ObjectId {object_id} is not correctly formatted."
            )

        found_object: Optional[OntologyObject] = OntologyObject.query.filter(
            OntologyObject.id == int(object_id),
            OntologyObject.namespace_id == int(namespace),
        ).first()

        if (
            found_object is None
            or (type_key and str(found_object.object_type_id) != type_key.get("typeId"))
            or found_object.deleted_on is not None
            or found_object.namespace.deleted_on is not None
        ):
            raise DataVisitorException(
                f"Invalid object key! No object found for key {key}."
            )
        self.object_references.add(found_object)


def validate_object(
    object_version: OntologyObjectVersion, type_version: OntologyObjectTypeVersion
):
    # validate against object type schema
    validate_object_against_schema(object_version.data, type_version)

    # setup schema walker
    resource_reference_visitor = ResourceReferenceVisitor(
        restrict_to_namespace=type_version.ontology_type.namespace_id,
    )
    walker = DataWalker(
        object_version.data,
        SchemaWalker(type_version.data, resolve_type_version_schema_url),
        visitors=[resource_reference_visitor],
    )

    # walk schema to validate and extract references
    walker.walk()  # FIXME add proper error reporting for api client

    # return extracted references
    return ObjectMetadata(
        referenced_objects=resource_reference_visitor.object_references,
        referenced_taxonomy_items=resource_reference_visitor.taxonomy_item_references,
    )

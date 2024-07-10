from jinja2 import Environment, FileSystemLoader

from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectType,
)
from muse_for_anything.db.models.taxonomies import Taxonomy, TaxonomyItem


def map_namespace_to_owl(namespace: Namespace):
    """
    Maps a namespace to an OWL representation.

    Args:
        namespace (Namespace): The namespace to be mapped.

    Returns:
        str: The rendered OWL representation as a string.
    """
    taxonomies = Taxonomy.query.filter(
        Taxonomy.deleted_on is None,
        Taxonomy.namespace_id == namespace.id,
    ).all()

    ontology_object_types = OntologyObjectType.query.filter(
        OntologyObjectType.deleted_on is None,
        OntologyObjectType.namespace_id == namespace.id,
    ).all()

    ontology_objects = OntologyObject.query.filter(
        OntologyObject.deleted_on is None,
        OntologyObject.namespace_id == namespace.id,
    ).all()

    env = Environment(
        loader=FileSystemLoader("muse_for_anything/templates"),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template("owl-export.xml")

    data = {
        "name": namespace.name,
        "description": namespace.description,
        "taxonomy_list": taxonomies,
        "type_list": ontology_object_types,
        "object_list": [
            (object, get_ontology_object_variables(object)) for object in ontology_objects
        ],
    }

    rendered_template = template.render(data)
    return rendered_template


def get_ontology_object_variables(ontology_object: OntologyObject):
    """
    Retrieves the variables of an ontology object.

    Args:
        ontology_object (OntologyObject): The ontology object to retrieve variables from.

    Returns:
        list: A list of dictionaries containing the variables of the ontology object.
                Each dictionary contains the name of the variable and its corresponding value or reference.

    """
    current = ontology_object.current_version
    data = current.data
    type = current.ontology_type_version
    root_schema = type.root_schema
    result = []
    if "referenceType" in root_schema and "referenceKey" in root_schema:
        ref_name = find_reference_name(data["referenceType"], data["referenceKey"])
        result.append({"name": ref_name, "ref": ref_name})
    elif isinstance(data, dict):
        for name, value in data.items():
            property_schema = root_schema["properties"][name]
            if "referenceType" in property_schema and "referenceKey" in property_schema:
                ref_name = find_reference_name(
                    value["referenceType"], value["referenceKey"]
                )
                result.append({"name": name, "ref": ref_name})
            else:
                result.append({"name": name, "value": value})
    return result


def find_reference_name(reference_type, reference_key):
    """
    Finds the name of a reference based on the type.

    Args:
        reference_type (str): The type of the reference.
        reference_key (dict): The key of the reference.

    Returns:
        str: The name of the reference.

    Raises:
        Exception: If the reference type is unknown.
    """
    if reference_type == "ont-object":
        return (
            OntologyObject.query.filter(
                OntologyObject.id == int(reference_key["objectId"]),
            )
            .first()
            .name
        )
    elif reference_type == "ont-taxonomy-item":
        return (
            TaxonomyItem.query.filter(
                TaxonomyItem.id == int(reference_key["taxonomyItemId"]),
            )
            .first()
            .name
        )
    else:
        raise Exception("Unknown reference type")

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

import json
import numbers
import select
from typing import Optional
from muse_for_anything.db.db import DB
from muse_for_anything.db.models.ontology_objects import OntologyObject
from muse_for_anything.json_migrations.jsonschema_validator import (
    extract_type,
    resolve_schema_reference,
)


def migrate_data(
    data,
    source_schema: dict,
    target_schema: dict,
    *,
    source_root: Optional[dict] = None,
    target_root: Optional[dict] = None,
    depth: int = 0,
):
    """Migrate data from source schema to the target schema if possible.

    Args:
        data: Data stored in a MUSE4Anything object
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (Optional[dict], optional): Root source JSON Schema
        target_root (Optional[dict], optional): Root target JSON Schema
        depth (int, optional): Depth counter for recursion
        Defaults to 0.

    Raises:
        Exception: When data is nested too deeply.

    Returns:
        Migrated data conforming to the target schema, if possible
    """
    if depth > 100:
        raise Exception("Data is too nested to migrate!")

    # Initialize root schemas
    if source_root is None:
        source_root = source_schema
        source_schema = source_schema["definitions"]["root"]
    if target_root is None:
        target_root = target_schema
        target_schema = target_schema["definitions"]["root"]

    target_type, target_nullable = extract_type(target_schema)

    # Resolve source schema references
    if target_type == "schemaReference":
        target_schema, target_root = resolve_schema_reference(
            schema=target_schema, root_schema=target_root
        )
        return migrate_data(
            data=data,
            source_schema=source_schema,
            target_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth + 1,
        )

    if data is None and target_nullable:
        return None

    source_type = extract_type(source_schema)[0]

    # Resolve target schema references
    if source_type == "schemaReference":
        source_schema, source_root = resolve_schema_reference(
            schema=source_schema, root_schema=source_root
        )
        return migrate_data(
            data=data,
            source_schema=source_schema,
            target_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth + 1,
        )

    return _execute_migration_function(
        data=data,
        source_type=source_type,
        target_type=target_type,
        source_schema=source_schema,
        target_schema=target_schema,
        source_root=source_root,
        target_root=target_root,
        depth=depth,
    )


def _execute_migration_function(
    data,
    source_type: str,
    target_type: str,
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Selects the appropriate migration function, depending on the target type.

    Args:
        data: Data stored in a MUSE4Anything object
        source_type (str): Type of source schema
        target_type (str): Type of target schema
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter

    Returns:
        Updated data, if successful
    """
    updated_data = None

    if target_type == "boolean":
        updated_data = _migrate_to_boolean(data=data, source_type=source_type)

    elif target_type == "number":
        updated_data = _migrate_to_numeric(data=data, source_type=source_type)

    elif target_type == "integer":
        updated_data = int(_migrate_to_numeric(data=data, source_type=source_type))

    elif target_type == "string":
        updated_data = _migrate_to_string(
            data=data, source_type=source_type, source_schema=source_schema
        )

    elif target_type == "enum":
        updated_data = _migrate_to_enum(data=data, target_schema=target_schema)

    elif target_type == "array":
        updated_data = _migrate_to_array(
            data=data,
            source_type=source_type,
            source_schema=source_schema,
            target_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth,
        )

    elif target_type == "tuple":
        updated_data = _migrate_to_tuple(
            data=data,
            source_type=source_type,
            source_schema=source_schema,
            target_tuple_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth,
        )

    elif target_type == "object":
        updated_data = _migrate_to_object(
            data=data,
            source_type=source_type,
            source_schema=source_schema,
            target_object_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth,
        )

    elif target_type == "resourceReference":
        updated_data = _migrate_to_resource_reference(
            data=data,
            source_type=source_type,
            source_schema=source_schema,
            target_schema=target_schema,
        )

    return updated_data


def _migrate_to_boolean(data, source_type: str):
    """Takes data and transforms it to a boolean instance.

    Args:
        data: Data potentially represented as a non-boolean
        source_type (str): Source type of data

    Raises:
        ValueError: If transformation to boolean was not possible

    Returns:
        bool: data represented as a boolean
    """
    match source_type:

        case "boolean" | "enum" | "integer" | "number" | "string":
            data = bool(data)

        case "object":
            if len(data) == 0:
                data = False

            elif len(data) == 1:
                value = next(iter(data.values()))
                data = bool(value)

            else:
                raise ValueError("No transformation to boolean possible!")

        case "array" | "tuple":
            if len(data) == 0:
                data = False

            else:
                data = bool(data)

    return data


def _migrate_to_numeric(data, source_type: str):
    """Takes data and transforms it to a nnumeric instance.

    Args:
        data: Data potentially represented as a non-float
        source_type (str): Source type of data

    Raises:
        ValueError: If transformation to numeric was not possible

    Returns:
        float: data represented as a float
    """
    match source_type:
        case "boolean" | "enum" | "number" | "integer" | "string":
            data = float(data)

        case "array" | "tuple":
            if len(data) == 0:
                data = 0.0

            elif len(data) == 1:
                data = float(data[0])

            else:
                raise ValueError("No transformation to numeric possible!")

        case "object":
            if len(data) == 0:
                data = 0.0

            elif len(data) == 1:
                value = next(iter(data.values()))
                data = float(value)

            else:
                raise ValueError(
                    "No transformation from this object to numeric possible!"
                )

    return data


def _migrate_to_string(data, source_type: str, source_schema: dict):
    """Takes data and transforms it to a string instance.

    Args:
        data: Data potentially represented as a non-string
        source_type (str): Source type of data
        source_schema (dict): Source JSON Schema

    Raises:
        ValueError: If transformation to string was not possible

    Returns:
        str: data represented as a string
    """
    match source_type:
        case "boolean":
            if not data:
                return ""
            else:
                return str(data)
        case "enum" | "integer" | "number" | "string":
            data = str(data)

        case "array" | "object" | "tuple":
            data = json.dumps(data)

    return data


def _migrate_to_enum(data, target_schema: dict):
    """Takes data and ensures it conforms to the allowed values of the
    defined enum.

    Args:
        data: Data potentially not part of the enum
        target_schema (dict): Target JSON Schema

    Raises:
        ValueError: If data is not part of the defined enum

    Returns:
        _type_: data fitted to the enum
    """
    allowed_values = target_schema.get("enum", [])

    if data in allowed_values:
        return data

    else:
        raise ValueError("No transformation to enum possible!")


def _migrate_to_array(
    data,
    source_type: str,
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Takes data and transforms it to an array instance.

    Args:
        data: Data potentially represented as a non-array
        source_type (str): Source type of data
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter for recursion, stops at 100

    Returns:
        list: data represented as an array
    """
    target_array_schema = target_schema.get("items", {})

    match source_type:
        case "boolean" | "integer" | "number" | "string":
            return [
                migrate_data(
                    data=data,
                    source_schema=source_schema,
                    target_schema=target_array_schema,
                    source_root=source_root,
                    target_root=target_root,
                    depth=depth + 1,
                )
            ]

        case "array":
            return _migrate_array_to_array(
                data,
                source_schema=source_schema,
                target_array_schema=target_array_schema,
                source_root=source_root,
                target_root=target_root,
                depth=depth,
            )

        case "tuple":
            return _migrate_tuple_to_array(
                data,
                source_schema=source_schema,
                target_array_schema=target_array_schema,
                source_root=source_root,
                target_root=target_root,
                depth=depth,
            )


def _migrate_to_tuple(
    data,
    source_type: str,
    source_schema: dict,
    target_tuple_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Takes data and transforms it to a tuple instance.

    Args:
        data: Data potentially represented as a non-tuple
        source_type (str): Source type of data
        source_schema (dict): Source JSON Schema
        target_tuple_schema (list): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter for recursion, stops at 100

    Raises:
        ValueError: If transformation to tuple was not possible

    Returns:
        list: Data represented as a tuple
    """
    target_items = target_tuple_schema.get("items", [])
    target_additional_items = target_tuple_schema.get("additionalItems", None)
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            if len(target_items) == 1:
                return [
                    migrate_data(
                        data=data,
                        source_schema=source_schema,
                        target_schema=target_items[0],
                        source_root=source_root,
                        target_root=target_root,
                        depth=depth + 1,
                    )
                ]
            else:
                raise ValueError("No transformation to enum possible!")
        case "array":
            return _migrate_array_to_tuple(
                data,
                source_schema=source_schema,
                target_items=target_items,
                target_additional_items=target_additional_items,
                source_root=source_root,
                target_root=target_root,
                depth=depth,
            )
        case "tuple":
            return _migrate_tuple_to_tuple(
                data,
                source_schema=source_schema,
                target_items=target_items,
                target_additional_items=target_additional_items,
                source_root=source_root,
                target_root=target_root,
                depth=depth,
            )


def _migrate_to_object(
    data,
    source_type: str,
    source_schema: dict,
    target_object_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Takes data and transforms it to an object instance.

    Args:
        data: Data potentially represented as a non-object
        source_type (str): Source type of data
        source_schema (dict): Source JSON Schema
        target_object_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter for recursion

    Raises:
        ValueError: If transformation to object was not possible

    Returns:
        dict: Data represented as an object
    """
    target_properties = target_object_schema.get("properties", {})
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            return _migrate_primitive_to_object(
                data=data,
                source_schema=source_schema,
                target_properties=target_properties,
                source_root=source_root,
                target_root=target_root,
                depth=depth,
            )
        case "object":
            return _migrate_object_to_object(
                data=data,
                source_schema=source_schema,
                target_properties=target_properties,
                source_root=source_root,
                target_root=target_root,
                depth=depth,
            )
        case _:
            raise ValueError("No transformation to object possible!")


def _migrate_to_resource_reference(
    data,
    source_type: str,
    source_schema: dict,
    target_schema: dict,
):
    """Migration logic for resource references. They can only be migrated from
    resource reference to resource reference. Also, their type of resource is
    fixed, i. e., taxonomy reference cannot be changed to object reference and
    vice versa.

    Args:
        data: Data stored in OntologyObject
        source_type (str): Source type of data
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema

    Raises:
        ValueError: If the schema change was invalid (not )

    Returns:
        _type_: _description_
    """
    if source_type != "resourceReference":
        raise ValueError(
            f"No conversion from {source_type} to resource reference supported"
        )

    source_ref_type = source_schema.get("referenceType", None)
    target_ref_type = target_schema.get("referenceType", None)

    if source_ref_type != target_ref_type:
        raise ValueError(
            f"Conversion {source_ref_type} to {target_ref_type} not supported"
        )

    if source_ref_type == "ont-taxonomy":
        return _migrate_taxonomy_resource_reference(
            data=data,
            source_schema=source_schema,
            target_schema=target_schema,
        )

    if source_ref_type == "ont-type":
        return _migrate_type_resource_reference(
            data=data, source_schema=source_schema, target_schema=target_schema
        )


def _migrate_array_to_array(
    data: list,
    source_schema: dict,
    target_array_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Migration logic from array to array.

    Args:
        data (list): Array data
        source_schema (dict): Source JSON Schema
        target_array_schema (dict): Target Array JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter for recursion

    Returns:
        Updated data in array
    """
    source_array_schema = source_schema.get("items", [])
    for i, element in enumerate(data):
        data[i] = migrate_data(
            data=element,
            source_schema=source_array_schema,
            target_schema=target_array_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth + 1,
        )

    return data


def _migrate_tuple_to_array(
    data: list,
    source_schema: dict,
    target_array_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Migration logic from tuple to array.

    Args:
        data (list): Tuple data
        source_schema (dict): Source JSON Schema
        target_array_schema (dict): Target Array JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter for recursion

    Returns:
        Updated data to array
    """
    source_items_types = source_schema.get("items", [])
    additional_items_schema = source_schema.get("additionalItems", None)
    for i, element in enumerate(data):
        # Check type definition and additionalItems
        if i < len(source_items_types):
            data[i] = migrate_data(
                data=element,
                source_schema=source_items_types[i],
                target_schema=target_array_schema,
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )

        elif additional_items_schema:
            data[i] = migrate_data(
                data=element,
                source_schema=additional_items_schema,
                target_schema=target_array_schema,
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )

        else:
            raise ValueError(f"No schema definition for element at index {i}!")

    return data


def _migrate_array_to_tuple(
    data: list,
    source_schema: dict,
    target_items: list,
    target_additional_items: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Migration logic from array to tuple.

    Args:
        data (list): Tuple data
        source_schema (dict): Source JSON Schema
        target_items (dict): Target Tuple JSON Schema
        target_additional_items (dict): dict
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter for recursion

    Raises:
        ValueError: If transformation to tuple not possible!

    Returns:
        Data updated to tuple structure
    """
    source_array_schema = source_schema.get("items", None)

    for i, element in enumerate(data):
        if i < len(target_items):
            # Elements covered by items definition
            data[i] = migrate_data(
                data=element,
                source_schema=source_array_schema,
                target_schema=target_items[i],
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )

        # Elements covered by additionalItems
        elif target_additional_items:
            data[i] = migrate_data(
                data=element,
                source_schema=source_array_schema,
                target_schema=target_additional_items,
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )

        else:
            raise ValueError(f"No schema definition for element at index {i}!")

    return data


def _migrate_tuple_to_tuple(
    data: list,
    source_schema: dict,
    target_items: list,
    target_additional_items: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Migration logic from tuple to tuple.

    Args:
        data (list): Tuple data
        source_schema (dict): Source JSON Schema
        target_items (dict): Target Tuple JSON Schema
        target_additional_items (dict): dict
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter for recursion

    Raises:
        ValueError: If transformation to tuple not possible!

    Returns:
        Data updated to new tuple structure
    """
    source_items = source_schema.get("items", [])
    source_additional_items = source_schema.get("additionalItems", None)
    for i, data_item in enumerate(data):
        if i < len(source_items) and i < len(target_items):
            data[i] = migrate_data(
                data=data_item,
                source_schema=source_items[i],
                target_schema=target_items[i],
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )
        elif i < len(source_items):
            if target_additional_items:
                data[i] = migrate_data(
                    data=data_item,
                    source_schema=source_items[i],
                    target_schema=target_additional_items,
                    source_root=source_root,
                    target_root=target_root,
                    depth=depth + 1,
                )
            else:
                del data[i]
        elif i < len(target_items):
            if source_additional_items:
                data[i] = migrate_data(
                    data=data_item,
                    source_schema=source_additional_items,
                    target_schema=target_items[i],
                    source_root=source_root,
                    target_root=target_root,
                    depth=depth + 1,
                )
            else:
                raise ValueError("Illegally defined tuple object!")
        else:
            if source_additional_items and target_additional_items:
                data[i] = migrate_data(
                    data=data_item,
                    source_schema=source_additional_items,
                    target_schema=target_additional_items,
                    source_root=source_root,
                    target_root=target_root,
                    depth=depth + 1,
                )
            else:
                del data[i]
    for i in range(len(source_items), len(target_items)):
        data.append(
            migrate_data(
                data=None,
                source_schema=None,
                target_schema=target_items[i],
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )
        )

    return data


def _migrate_primitive_to_object(
    data,
    source_schema: dict,
    target_properties: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Migration logic from primitive type (boolean, numeric, string) to object.

    Args:
        data: Data represented as a non-object
        source_schema (dict): Source JSON Schema
        target_properties (dict): Target Object properties schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter for recursion

    Returns:
        Data transformed to object
    """
    if len(target_properties) != 1:
        raise ValueError("No transformation to complex object possible!")

    prop_name = next(iter(target_properties))
    prop_type = target_properties.get(prop_name, None)

    return {
        prop_name: migrate_data(
            data=data,
            source_schema=source_schema,
            target_schema=prop_type,
            source_root=source_root,
            target_root=target_root,
            depth=depth + 1,
        )
    }


def _migrate_object_to_object(
    data,
    source_schema: dict,
    target_properties: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Migration logic from object to object.

    Args:
        data: Data represented as a non-object
        source_schema (dict): Source JSON Schema
        target_properties (dict): Target Object properties schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter for recursion

    Returns:
        Data transformed to object
    """
    source_properties = source_schema.get("properties", {})
    common_properties = target_properties.keys() & source_properties.keys()
    new_properties = target_properties.keys() - source_properties.keys()
    deleted_properties = source_properties.keys() - target_properties.keys()

    for prop in common_properties:
        data[prop] = migrate_data(
            data=data.get(prop, None),
            source_schema=source_properties.get(prop, None),
            target_schema=target_properties.get(prop, None),
            source_root=source_root,
            target_root=target_root,
            depth=depth + 1,
        )

    # One prop added, one deleted, likely name changes
    if len(new_properties) == 1 and len(deleted_properties) == 1:
        new_property = next(iter(new_properties))
        deleted_property = next(iter(deleted_properties))
        data[new_property] = migrate_data(
            data=data.get(deleted_property, None),
            source_schema=source_properties.get(deleted_property, None),
            target_schema=target_properties.get(new_property, None),
            source_root=source_root,
            target_root=target_root,
            depth=depth + 1,
        )
        del data[deleted_property]

    # More than one added or deleted
    else:
        # Add all new properties
        for prop in new_properties:
            data[prop] = migrate_data(
                data=None,
                source_schema=None,
                target_schema=target_properties.get(prop, None),
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )

        # Delete all old properties
        for prop in deleted_properties:
            del data[prop]

    return data


def _migrate_taxonomy_resource_reference(
    data,
    source_schema: dict,
    target_schema: dict,
):
    """Migration logic from taxonomy resource reference to taxonomy resource
    reference.

    Args:
        data: Data Object
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema

    Returns:
        Data if schema change valid
    """
    source_namespace = source_schema.get("referenceKey")["namespaceId"]
    target_namespace = target_schema.get("referenceKey")["namespaceId"]
    source_taxonomy = source_schema.get("referenceKey")["taxonomyId"]
    target_taxonomy = target_schema.get("referenceKey")["taxonomyId"]
    namespace_equal = source_namespace == target_namespace
    taxonomy_equal = source_taxonomy == target_taxonomy
    if namespace_equal and taxonomy_equal:
        return data


def _migrate_type_resource_reference(
    data,
    source_schema: dict,
    target_schema: dict,
):
    """Migration logic from type resource reference to type resource reference.

    Args:
        data: Data stored in OntologyObject
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema

    Returns:
        Data if schema change valid
    """
    source_ref_key = source_schema.get("referenceKey", None)
    target_ref_key = target_schema.get("referenceKey", None)

    if source_ref_key and target_ref_key:
        return _check_types_equal(
            data=data, source_schema=source_schema, target_schema=target_schema
        )

    elif target_ref_key:
        return _check_type_compatible(data=data, target_schema=target_schema)

    else:
        return data


def _check_types_equal(data, source_schema: dict, target_schema: dict):
    """Check whether referenced types are equal

    Args:
        data: Data stored in resource reference
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema

    Returns:
        bool: Indicates whether referenced types are equal
    """
    source_namespace = source_schema["referenceKey"]["namespaceId"]
    target_namespace = target_schema["referenceKey"]["namespaceId"]
    source_type = source_schema["referenceKey"]["typeId"]
    target_type = target_schema["referenceKey"]["typeId"]

    namespace_equal = source_namespace == target_namespace
    type_equal = source_type == target_type

    if namespace_equal and type_equal:
        return data

    else:
        raise ValueError(
            f"Source type {source_type} not equal target type {target_type}!"
        )


def _check_type_compatible(data, target_schema: dict):
    """Check whether data is compatible to new resource reference.

    Args:
        data: Data stored in resource reference
        target_schema (dict): Target JSON Schema

    Returns:
        bool: Indicates if resource references are compatible
    """
    target_type = target_schema["referenceKey"]["typeId"]
    data_object = data["referenceKey"]["objectId"]

    q = select(OntologyObject).where(OntologyObject.id == data_object)
    ontology_object = DB.session.execute(q).scalars().first()
    object_type = ontology_object.object_type_id

    if target_type == object_type:
        return data

    else:
        raise ValueError(f"ObjectType {object_type} is not equal RefType {target_type}!")

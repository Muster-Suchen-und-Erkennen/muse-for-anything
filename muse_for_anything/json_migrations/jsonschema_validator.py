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

from typing import Optional

from muse_for_anything.api.v1_api.ontology_object_validation import (
    resolve_type_version_schema_url,
)


def extract_type(schema: dict):
    """Extract the type of a given schema and indicates
    whether or not elements are nullable

    Args:
        schema (dict): A JSON Schema saved as python dict

    Raises:
        ValueError: When schema does not include a known type definition

    Returns:
        string: Returns the main type of the schema
        (can be enum, schemaReference, resourceReference, object, array, tuple,
        boolean, integer, number, or string)
    """
    keys = schema.keys()
    nullable = False

    if "$ref" in keys:
        return "schemaReference", nullable

    if "enum" in keys:
        return "enum", nullable

    # Handling of other types
    if "type" in keys:
        type_entry = schema["type"]
        nullable = "null" in type_entry
        data_type = next((t for t in type_entry if t != "null"), None)

        if data_type == "object":
            return _extract_object_type(schema=schema), nullable

        if data_type == "array":
            return _extract_array_type(schema=schema), nullable
        return data_type, nullable

    else:
        raise ValueError("No type definition found!")


def _extract_object_type(schema: dict):
    """Since MUSE4Anything defines resource references and objects as objects
    of JSON Schema, it is necessary to check additional keywords as well.

    Args:
        schema (dict): Schema that defines an object

    Returns:
        str: Returns object type (can be object or resourceReference)
    """
    if "customType" in schema:
        if schema["customType"] == "resourceReference":
            return "resourceReference"
        else:
            raise ValueError("Unknown object type!")
    else:
        return "object"


def _extract_array_type(schema: dict):
    """Since MUSE4Anything defines tuples and arrays as arrays of JSON Schema,
    it is necessary to check additional keywords as well.

    Args:
        schema (dict): Schema that defines an array

    Returns:
        str: Returns array type (can be array or tuple)
    """
    if "arrayType" in schema:
        if schema["arrayType"] == "array":
            return "array"
        elif schema["arrayType"] == "tuple":
            return "tuple"
        else:
            raise ValueError("Unknown array type!")
    else:
        raise ValueError("No array type given!")


def resolve_schema_reference(schema: dict, root_schema: dict):
    """Function to resolve a reference if one exists and returns
    the resolved schema.

    Args:
        schema (dict): A JSON Schema that potentially holds $ref
        root_schema (dict): The root JSON Schema for local references

    Returns:
        dict: Resolved schema if there was a reference, else original schema
    """

    if "$ref" not in schema:
        return schema, root_schema
    reference = schema["$ref"]
    if reference.startswith("#/definitions"):
        schema = root_schema["definitions"]
        type = reference.split("/")[-1]
        return schema[type], root_schema
    else:
        key = reference.split("#")[-1].split("/")[-1]
        res_ref = resolve_type_version_schema_url(url_string=schema["$ref"])
        return res_ref["definitions"][key], res_ref


def validate_schema(
    source_schema: dict,
    target_schema: dict,
    *,
    source_root: Optional[dict] = None,
    target_root: Optional[dict] = None,
    depth: int = 0,
):
    """Going from the source schema, it is checked whether a conversion to
    the target schema is possible. Unsupported conversions are: \n
    array to enum, array to object, enum to array, enum to object, enum to
    tuple, object to array, object to enum, object to tuple, tuple to enum,
    and tuple to object. These might need an intermediate conversion step,
    e. g. via boolean, integer, number, or string.

    Args:
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (Optional[dict], optional): Root source JSON Schema,
        used for reference resolving. Defaults to None.
        target_root (Optional[dict], optional): Root target JSON Schema,
        used for reference resolving. Defaults to None.
        depth (int, optional): Depth counter for recursion, stops at 100.
        Defaults to 0.

    Raises:
        Exception: If a schema is nested too deep.

    Returns:
        bool: Returns True if schemas could be matched, else False
    """
    if depth > 100:
        raise Exception("Schema nested too deep")

    if source_root is None:
        source_root = source_schema
        source_schema = source_schema["definitions"]["root"]

    if target_root is None:
        target_root = target_schema
        target_schema = target_schema["definitions"]["root"]

    source_type = extract_type(schema=source_schema)[0]
    target_type = extract_type(schema=target_schema)[0]

    # Check if both schemas have valid types
    if source_type and target_type:
        return _validate_types(
            source_type=source_type,
            target_type=target_type,
            source_schema=source_schema,
            target_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth,
        )
    return False


def _validate_types(
    source_type: str,
    target_type: str,
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Validate schema based on source and target type.

    Args:
        source_type (str): Type of source schema
        target_type (str): Type of target schema
        source_scheam (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter
    """
    if source_type == "schemaReference" or target_type == "schemaReference":
        return _validate_schema_reference(
            source_schema=source_schema,
            target_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth,
        )

    if target_type == "number" or target_type == "integer":
        return _validate_to_numeric(
            source_type=source_type,
            source_schema=source_schema,
            target_schema=target_schema,
        )

    elif target_type == "boolean":
        return _validate_to_boolean(
            source_type=source_type,
            source_schema=source_schema,
        )

    elif target_type == "string":
        return _validate_to_string(
            source_type=source_type,
            source_schema=source_schema,
            target_schema=target_schema,
        )

    elif target_type == "enum":
        return _validate_to_enum(
            source_type=source_type,
            source_schema=source_schema,
        )

    elif target_type == "array":
        return _validate_to_array(
            source_type=source_type,
            source_schema=source_schema,
            target_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth,
        )

    elif target_type == "tuple":
        return _validate_to_tuple(
            source_type=source_type,
            source_schema=source_schema,
            target_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth,
        )

    elif target_type == "object":
        return _validate_to_object(
            source_type=source_type,
            source_schema=source_schema,
            target_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth,
        )

    elif target_type == "resourceReference":
        return _validate_to_resource_reference(
            source_type=source_type,
            source_schema=source_schema,
            target_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth,
        )

    return False


def _validate_schema_reference(
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Resolve schema references that are either in the source or target schema,
    or both, and continue validation with resolved schema

    Args:
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter

    Returns:
        bool: Indication whether referenced schemas form valid update
    """
    source_schema, source_root = resolve_schema_reference(
        schema=source_schema,
        root_schema=source_root,
    )
    target_schema, target_root = resolve_schema_reference(
        schema=target_schema,
        root_schema=target_root,
    )
    return validate_schema(
        source_schema=source_schema,
        target_schema=target_schema,
        source_root=source_root,
        target_root=target_root,
        depth=depth + 1,
    )


def _validate_to_numeric(source_type: str, source_schema: dict, target_schema: dict):
    """Validation logic when migrating to a numeric type (integer, number).

    Args:
        source_type (str): Type of source schema
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema

    Returns:
        bool: Indicates whether change to numeric is valid
    """
    match source_type:
        case "integer" | "number":
            return _check_numeric_attributes(
                source_schema=source_schema, target_schema=target_schema
            )
        case "boolean" | "enum" | "string":
            return True
        case "array" | "tuple":
            return source_schema.get("minItems", 0) <= 1
        case "object":
            return True
        case _:
            return False


def _validate_to_boolean(source_type: str, source_schema: dict):
    """Validation logic when migrating to boolean.

    Args:
        source_type (str): Type of source schema
        source_schema (dict): Source JSON Schema

    Returns:
        bool: Indicates whether change to boolean is valid
    """
    match source_type:
        case "boolean" | "enum" | "integer" | "number" | "string":
            return True
        case "array" | "tuple":
            return source_schema.get("minItems", 0) <= 1
        case "object":
            return True
        case _:
            return False


def _validate_to_string(source_type: str, source_schema: dict, target_schema: dict):
    """Validation logic when migrating to string.

    Args:
        source_type (str): Type of source schema
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema

    Returns:
        bool: Indicates whether change to string is valid
    """
    match source_type:
        case "array" | "boolean" | "enum" | "integer" | "number" | "tuple":
            return True
        case "string":
            return _check_string_attributes(
                source_schema=source_schema, target_schema=target_schema
            )
        case "object":
            return True
        case _:
            return False


def _validate_to_enum(source_type: str, source_schema: dict):
    """Validation logic when migrating to enum.

    Args:
        source_type (str): Type of source schema
        source_schema (dict): Source JSON Schema

    Returns:
        bool: Indicates whether change to enum is valid
    """
    match source_type:
        case "boolean" | "enum" | "integer" | "number" | "string":
            return True
        case "array" | "tuple":
            return source_schema.get("minItems", 0) <= 1
        case _:
            return False


def _validate_to_array(
    source_type: str,
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Validation logic when migrating to array.

    Args:
        source_type (str): Type of source schema
        source_scheam (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter

    Returns
        bool: Indicates whether change to array is valid
    """
    target_array_schema = target_schema.get("items", {})
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            return target_schema.get("minItems", 0) <= 1 and validate_schema(
                source_schema=source_schema,
                target_schema=target_array_schema,
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )
        case "array":
            return _validate_array_to_array(
                source_schema=source_schema,
                target_schema=target_schema,
                source_root=source_root,
                target_root=target_root,
                depth=depth,
            )
        case "tuple":
            return _validate_tuple_to_array(
                source_schema=source_schema,
                target_schema=target_schema,
                source_root=source_root,
                target_root=target_root,
                depth=depth,
            )
        case _:
            return False


def _validate_to_tuple(
    source_type: str,
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Validation logic when migrating to tuple.

    Args:
        source_type (str): Type of source schema
        source_scheam (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter

    Returns
        bool: Indicates whether change to tuple is valid
    """
    target_items_types = target_schema.get("items", [])
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            if len(target_items_types) == 1:
                return validate_schema(
                    source_schema=source_schema,
                    target_schema=target_items_types[0],
                    source_root=source_root,
                    target_root=target_root,
                    depth=depth + 1,
                )
            else:
                return False
        case "array":
            return _validate_array_to_tuple(
                source_schema=source_schema,
                target_schema=target_schema,
                source_root=source_root,
                target_root=target_root,
                depth=depth,
            )
        case "tuple":
            return _validate_tuple_to_tuple(
                source_schema=source_schema,
                target_schema=target_schema,
                source_root=source_root,
                target_root=target_root,
                depth=depth,
            )
        case _:
            return False


def _validate_to_object(
    source_type: str,
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Validation logic when migrating to object.

    Args:
        source_type (str): Type of source schema
        source_scheam (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter

    Returns
        bool: Indicates whether change to object is valid
    """
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            return True
        case "object":
            return _validate_object_to_object(
                source_schema=source_schema,
                target_schema=target_schema,
                source_root=source_root,
                target_root=target_root,
                depth=depth,
            )
        case _:
            return False


def _validate_to_resource_reference(
    source_type: str,
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Validation logic when migrating to resource reference.

    Args:
        source_type (str): Type of source schema
        source_scheam (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter

    Returns
        bool: Indicates whether change to object is valid
    """
    if source_type == "resourceReference":
        return True
    else:
        return False


def _validate_array_to_array(
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Validation logic when migrating from array to array.

    Args:
        source_scheam (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter

    Return:
        bool: Indicates whether change is valid
    """
    target_array_schema = target_schema.get("items", {})
    valid_limits = _check_array_attributes(
        source_schema=source_schema, target_schema=target_schema
    )
    if valid_limits:
        source_array_schema = source_schema.get("items", {})
        return validate_schema(
            source_schema=source_array_schema,
            target_schema=target_array_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth + 1,
        )
    else:
        return False


def _validate_tuple_to_array(
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Validation logic when migrating from tuple to array.

    Args:
        source_scheam (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter

    Return:
        bool: Indicates whether change is valid
    """
    target_array_schema = target_schema.get("items", {})
    valid_limits = _check_array_attributes(
        source_schema=source_schema, target_schema=target_schema
    )
    if valid_limits:
        source_items_types = source_schema.get("items", [])
        additional_items_schema = source_schema.get("additionalItems", None)
        for item_type in source_items_types:
            valid = validate_schema(
                source_schema=item_type,
                target_schema=target_array_schema,
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )
            if not valid:
                # One of the elements is not matchable
                return False
        # Check if additionalItems match
        if additional_items_schema:
            valid = validate_schema(
                source_schema=additional_items_schema,
                target_schema=target_array_schema,
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )
            if not valid:
                return False
        return True
    else:
        return False


def _validate_array_to_tuple(
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Validation logic when migrating from array to tuple

    Args:
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter

    Returns:
        bool: Indicates whether change is valid
    """
    valid_limits = _check_array_attributes(
        source_schema=source_schema, target_schema=target_schema
    )
    if not valid_limits:
        return False

    target_items_types = target_schema.get("items", [])
    target_additional_items = target_schema.get("additionalItems", None)
    source_array_schema = source_schema.get("items", {})

    for i, item_type in enumerate(target_items_types):
        if i < len(target_items_types):
            valid = validate_schema(
                source_schema=source_array_schema,
                target_schema=item_type,
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )
            if not valid:
                return False
        elif target_additional_items:
            valid = validate_schema(
                source_schema=source_array_schema,
                target_schema=target_additional_items,
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )
            if not valid:
                return False
        else:
            return False
    return True


def _validate_tuple_to_tuple(
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Validation logic when migrating from tuple to tuple

    Args:
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter

    Returns:
        bool: Indicates whether change is valid
    """
    valid_limits = _check_array_attributes(
        source_schema=source_schema, target_schema=target_schema
    )
    if not valid_limits:
        return

    target_items_types = target_schema.get("items", [])
    target_additional_items = target_schema.get("additionalItems", None)
    source_items_types = source_schema.get("items", [])
    source_additional_items = source_schema.get("additionalItems", None)
    max_length = max(len(source_items_types), len(target_items_types))

    for i in range(max_length):
        if i < len(source_items_types) and i < len(target_items_types):
            valid = validate_schema(
                source_schema=source_items_types[i],
                target_schema=target_items_types[i],
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )
            if not valid:
                return False
        elif i < len(source_items_types) and target_additional_items:
            valid = validate_schema(
                source_schema=source_items_types[i],
                target_schema=target_additional_items,
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )
            if not valid:
                return False
        elif i < len(target_items_types) and source_additional_items:
            valid = validate_schema(
                source_schema=source_additional_items,
                target_schema=target_items_types[i],
                source_root=source_root,
                target_root=target_root,
                depth=depth + 1,
            )
            if not valid:
                return False
        else:
            return False
    return True


def _validate_object_to_object(
    source_schema: dict,
    target_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Validation logic when migrating from object to object

    Args:
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema
        source_root (dict): Root source JSON Schema
        target_root (dict): Root target JSON Schema
        depth (int): Depth counter

    Returns:
        bool: Indicates whether change is valid
    """
    target_properties = target_schema.get("properties", {})
    source_properties = source_schema.get("properties", {})

    common_properties = target_properties.keys() & source_properties.keys()
    new_properties = target_properties.keys() - source_properties.keys()
    deleted_properties = source_properties.keys() - target_properties.keys()

    for prop in common_properties:
        valid = validate_schema(
            source_schema=source_properties[prop],
            target_schema=target_properties[prop],
            source_root=source_root,
            target_root=target_root,
            depth=depth + 1,
        )
        if not valid:
            return False

    if len(new_properties) == 1 and len(deleted_properties) == 1:
        new_prop = next(iter(new_properties))
        deleted_prop = next(iter(deleted_properties))
        valid = validate_schema(
            source_schema=source_properties[deleted_prop],
            target_schema=target_properties[new_prop],
            source_root=source_root,
            target_root=target_root,
            depth=depth + 1,
        )
        if not valid:
            return False
    return True


def _check_numeric_attributes(source_schema: dict, target_schema: dict):
    """Used to check if there are contradictions in the integer keywords,
    e. g., min and max, of source and target schema.

    Args:
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema

    Returns:
        boolean: True, if update valid, else false
    """
    min_source = source_schema.get("minimum", None)
    min_target = target_schema.get("minimum", None)
    max_source = source_schema.get("maximum", None)
    max_target = target_schema.get("maximum", None)
    excl_min_source = source_schema.get("exclusiveMinimum", None)
    excl_min_target = target_schema.get("exclusiveMinimum", None)
    excl_max_source = source_schema.get("exclusiveMaximum", None)
    excl_max_target = target_schema.get("exclusiveMaximum", None)

    if min_source is not None and max_target is not None:
        if min_source > max_target:
            return False

    if min_source is not None and excl_max_target is not None:
        if min_source >= excl_max_target:
            return False

    if max_source is not None and min_target is not None:
        if max_source < min_target:
            return False

    if max_source is not None and excl_min_target is not None:
        if max_source <= excl_min_target:
            return False

    if excl_min_source is not None and max_target is not None:
        if excl_min_source >= max_target:
            return False

    if excl_min_source is not None and excl_max_target is not None:
        if excl_min_source >= excl_max_target:
            return False

    if excl_max_source is not None and min_target is not None:
        if excl_max_source <= min_target:
            return False

    if excl_max_source is not None and excl_min_target is not None:
        if excl_max_source <= excl_min_target:
            return False

    return True


def _check_string_attributes(source_schema: dict, target_schema: dict):
    """Used to check if there are contradictions in the string keywords
    min and max length of source and target schema.

    Args:
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema

    Returns:
        boolean: True, if update valid, else false
    """
    min_length_source = source_schema.get("minLength", 0)
    min_length_target = target_schema.get("minLength", 0)
    max_length_source = source_schema.get("maxLength", None)
    max_length_target = target_schema.get("maxLength", None)

    if max_length_source is not None:
        if max_length_source < min_length_target:
            return False

    if max_length_target is not None:
        if min_length_source > max_length_target:
            return False

    return True


def _check_array_attributes(source_schema: dict, target_schema: dict):
    """Used to check if there are contradictions in the array keywords
    min and max items of source and target schema.

    Args:
        source_schema (dict): Source JSON Schema
        target_schema (dict): Target JSON Schema

    Returns:
        boolean: True, if update valid, else false
    """
    min_items_source = source_schema.get("minItems", 0)
    min_items_target = target_schema.get("minItems", 0)
    max_items_source = source_schema.get("maxItems", None)
    max_items_target = target_schema.get("maxItems", None)
    if max_items_source is not None:
        if max_items_source < min_items_target:
            return False

    if max_items_target is not None:
        if min_items_source > max_items_target:
            return False

    return True

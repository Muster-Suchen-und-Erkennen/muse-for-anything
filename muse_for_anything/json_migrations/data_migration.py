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

import numbers
from typing import Optional
from muse_for_anything.json_migrations.jsonschema_matcher import (
    _extract_type,
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
    """Data conforming to the source schema is migrated to the target schema if
    possible.

    Args:
        data: Data stored in a MUSE4Anything object
        source_schema (dict): Source JSONSchema
        target_schema (dict): Target JSONSchema
        source_root (Optional[dict], optional): Root source JSONSchema,
        used for reference resolving. Defaults to None.
        target_root (Optional[dict], optional): Root target JSONSchema,
        used for reference resolving. Defaults to None.
        depth (int, optional): Depth counter for recursion, stops at 100.
        Defaults to 0.

    Returns:
        Updated data, if update was successful
    """
    if depth > 100:
        raise ValueError("Data is too nested to migrate!")
    if source_root is None:
        source_root = source_schema
        source_schema = source_schema["definitions"]["root"]
    if target_root is None:
        target_root = target_schema
        target_schema = target_schema["definitions"]["root"]

    target_type, target_nullable = _extract_type(target_schema)
    if target_type == "schemaReference":
        target_schema = resolve_schema_reference(
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
    source_type, source_nullable = _extract_type(source_schema)
    if source_type == "schemaReference":
        source_schema = resolve_schema_reference(
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
    updated_data = None
    # Call appropriate method depending on target schema main type
    if target_type == "array":
        # Array needs additional information on element type
        target_array_schema = target_schema.get("items", [])
        updated_data = _migrate_to_array(
            data=data,
            source_type=source_type,
            source_schema=source_schema,
            target_array_schema=target_array_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth,
        )
    elif target_type == "boolean":
        updated_data = _migrate_to_boolean(data=data, source_type=source_type)
    elif target_type == "enum":
        # Enum needs the allowed values
        allowed_values = target_schema.get("enum", [])
        updated_data = _migrate_to_enum(data=data, allowed_values=allowed_values)
    elif target_type == "integer":
        updated_data = _migrate_to_integer(data=data, source_type=source_type)
    elif target_type == "number":
        updated_data = _migrate_to_number(data=data, source_type=source_type)
    elif target_type == "string":
        updated_data = _migrate_to_string(
            data=data, source_type=source_type, source_schema=source_schema
        )
    elif target_type == "tuple":
        updated_data = _migrate_to_tuple(
            data=data,
            source_type=source_type,
            source_schema=source_schema,
            target_tuple_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth + 1,
        )
    elif target_type == "object":
        updated_data = _migrate_to_object(
            data=data,
            source_type=source_type,
            source_schema=source_schema,
            target_object_schema=target_schema,
            source_root=source_root,
            target_root=target_root,
            depth=depth + 1,
        )
    return updated_data


def _migrate_to_number(data, source_type: str):
    """Takes data and transforms it to a number/float instance.

    Args:
        data: Data potentially represented as a non-float
        source_type (str): Source type of data

    Raises:
        ValueError: If transformation to number was not possible

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
                raise ValueError("No transformation to number possible!")
        case "object":
            if len(data) == 0:
                data = 0.0
            elif len(data) == 1:
                value = next(iter(data.values()))
                data = float(value)
            else:
                raise ValueError("No transformation from this object to number possible!")
    return data


def _migrate_to_integer(data, source_type: str):
    """Takes data and transforms it to an integer instance.

    Args:
        data: Data potentially represented as a non-integer
        source_type (str): Source type of data

    Raises:
        ValueError: If transformation to integer was not possible

    Returns:
        int: data represented as an integer
    """
    match source_type:
        case "boolean" | "enum" | "number" | "integer" | "string":
            data = int(float(data))
        case "array" | "tuple":
            if len(data) == 0:
                data = 0
            elif len(data) == 1:
                data = int(float(data[0]))
            else:
                raise ValueError("No transformation to integer possible!")
        case "object":
            if len(data) == 0:
                data = 0.0
            elif len(data) == 1:
                value = next(iter(data.values()))
                data = int(float(value))
            else:
                raise ValueError(
                    "No transformation from this object to integer possible!"
                )
    return data


def _migrate_to_string(data, source_type: str, source_schema: dict):
    """Takes data and transforms it to a string instance.

    Args:
        data: Data potentially represented as a non-string
        source_type (str): Source type of data
        source_schema (dict): Source JSONSchema for better conversion

    Raises:
        ValueError: If transformation to string was not possible

    Returns:
        str: data represented as a string
    """
    match source_type:
        case "array" | "boolean" | "enum" | "integer" | "number" | "string" | "tuple":
            try:
                data = str(data)
            except ValueError:
                raise ValueError("No transformation to string possible!")
        case "object":
            data_string = ""
            properties = source_schema.get("properties", {})
            for property in properties.keys():
                data_string += property + ": " + str(data[property]) + ", "
            data = data_string[:-2]
    return data


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
            try:
                data = bool(data)
            except ValueError:
                raise ValueError("No transformation to boolean possible!")
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
            elif len(data) == 1:
                data = bool(data[0])
            else:
                data = bool(data)
    return data


def _migrate_to_enum(data, allowed_values: list):
    """Takes data and ensures it conforms to the allowed values of the
    defined enum.

    Args:
        data: Data potentially not part of the enum
        allowed_values (list): A list of values accepted in the enum

    Raises:
        ValueError: If data is not part of the defined enum

    Returns:
        _type_: data fitted to the enum
    """
    if isinstance(data, numbers.Number):
        temp_data = data
        for value in allowed_values:
            if isinstance(value, numbers.Number) and round(value) == round(temp_data):
                temp_data = value
        data = temp_data
    elif isinstance(data, list) and len(data) == 1:
        data = data[0]
    if data in allowed_values:
        return data
    else:
        raise ValueError("No transformation to enum possible!")


def _migrate_to_array(
    data,
    source_type: str,
    source_schema: dict,
    target_array_schema: dict,
    source_root: dict,
    target_root: dict,
    depth: int,
):
    """Takes data and transforms it to an array instance.

    Args:
        data: Data potentially represented as a non-array
        source_type (str): Source type of data
        source_schema (dict): Source JSONSchema for better conversion
        target_array_schema (dict): Indicates data type of elements in an array
        source_root (dict): Root source JSONSchema, used for reference resolving
        target_root (dict): Root target JSONSchema, used for reference resolving
        depth (int): Depth counter for recursion, stops at 100

    Returns:
        list: data represented as an array
    """
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            data = [
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
        case "tuple":
            source_items_types = source_schema.get("items", [])
            additional_items_schema = source_schema.get("additionalItems", None)
            for i, element in enumerate(data):
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
        source_schema (dict): Source JSONSchema for better conversion
        target_object_schema (dict): Target JSONSchema for better conversion
        source_root (dict): Root source JSONSchema, used for reference resolving
        target_root (dict): Root target JSONSchema, used for reference resolving
        depth (int): Depth counter for recursion, stops at 100

    Raises:
        ValueError: If transformation to object was not possible

    Returns:
        dict: Data represented as an object
    """
    target_properties = target_object_schema.get("properties", {})
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            if len(target_properties) != 1:
                raise ValueError("No transformation to complex object possible!")
            prop_name = next(iter(target_properties))
            prop_type = target_properties.get(prop_name, None)
            data = {
                prop_name: migrate_data(
                    data=data,
                    source_schema=source_schema,
                    target_schema=prop_type,
                    source_root=source_root,
                    target_root=target_root,
                    depth=depth + 1,
                )
            }
        case "object":
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
        source_schema (dict): Source JSONSchema for better conversion
        target_tuple_schema (list): Target JSONSchema for better conversion
        source_root (dict): Root source JSONSchema, used for reference resolving
        target_root (dict): Root target JSONSchema, used for reference resolving
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
                data = [
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
            source_array_schema = source_schema.get("items", None)
            for i, element in enumerate(data):
                if i < len(target_items):
                    data[i] = migrate_data(
                        data=element,
                        source_schema=source_array_schema,
                        target_schema=target_items[i],
                        source_root=source_root,
                        target_root=target_root,
                        depth=depth + 1,
                    )
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
        case "tuple":
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

import copy
from typing import Optional


def extract_type(schema: dict):
    """Extract the type of a given schema and indicates
    whether or not elements are nullable

    Args:
        schema (dict): A JSONSchema saved as python dict

    Raises:
        ValueError: When schema does not include a known type definition

    Returns:
        string: Returns the main type of the schema
        (can be enum, schemaReference, resourceReference, object, array, tuple,
        boolean, integer, number, or string)
    """
    keys = schema.keys()
    nullable = False
    # Enum and $ref are defined separately, not in type
    if "enum" in keys:
        return "enum", nullable
    elif "$ref" in keys:
        return "schemaReference", nullable
    # Handling of other types
    elif "type" in keys:
        # Check if elements nullable
        nullable = "null" in schema["type"]
        data_type = next(t for t in schema["type"] if t != "null")
        if data_type == "object":
            # ResourceReference also defined as object
            if "customType" in keys:
                if schema["customType"] == "resourceReference":
                    return "resourceReference", nullable
                else:
                    raise ValueError("Unknown object type!")
            else:
                return "object", nullable
        elif data_type == "array":
            # Tuple and Array identified by arrayType entry
            if "arrayType" in keys:
                if schema["arrayType"] == "array":
                    return "array", nullable
                elif schema["arrayType"] == "tuple":
                    return "tuple", nullable
                else:
                    raise ValueError("Unknown array type!")
            else:
                raise ValueError("No array type given!")
        elif data_type == "boolean":
            return "boolean", nullable
        elif data_type == "integer":
            return "integer", nullable
        elif data_type == "number":
            return "number", nullable
        elif data_type == "string":
            return "string", nullable
        else:
            raise ValueError("Unknown type!")
    else:
        raise ValueError("No type definition found!")


def match_schema(
    source_schema: dict,
    target_schema: dict,
    source_root: Optional[dict] = None,
    target_root: Optional[dict] = None,
    depth: int = 0,
):
    """Going from the source schema, it is checked whether a conversion to the target schema is possible.
    Unsupported conversions are: \n
    array to enum, array to object, enum to array, enum to object, enum to tuple,
    object to array, object to enum, object to tuple, tuple to enum, and
    tuple to object. These might need an intermediate conversion step, e. g.
    via boolean, integer, number, or string.

    Args:
        source_schema (dict): Source JSONSchema
        target_schema (dict): Target JSONSchema
        source_root (Optional[dict], optional): Root source JSONSchema, used for reference resolving. Defaults to None.
        target_root (Optional[dict], optional): Root target JSONSchema, used for reference resolving. Defaults to None.
        depth (int, optional): Depth counter for recursion, stops at 100. Defaults to 0.

    Raises:
        ValueError: If a schema is nested too deep.

    Returns:
        bool: Returns True if schemas could be matched, else False
    """
    if depth > 100:
        raise ValueError("Schema nested too deep")
    if source_root is None:
        source_root = source_schema
        source_schema = source_schema["definitions"]["root"]
    if target_root is None:
        target_root = target_schema
        target_schema = target_schema["definitions"]["root"]
    source_type, source_nullable = extract_type(source_schema)
    target_type, target_nullable = extract_type(target_schema)
    # Check if both schemas have valid types
    if source_type and target_type:
        # TODO: Implement "sanity checks" for updates on all types
        if target_type == "number":
            match source_type:
                case "boolean" | "enum" | "integer" | "number" | "string":
                    return True
                case "array":
                    return True
                case "tuple":
                    return True
                case "object":
                    return True
                case _:
                    return False
        elif target_type == "integer":
            match source_type:
                case "boolean" | "enum" | "integer" | "number" | "string":
                    return True
                case "array":
                    return True
                case "tuple":
                    return True
                case "object":
                    return True
                case _:
                    return False
        elif target_type == "boolean":
            match source_type:
                case "boolean" | "enum" | "integer" | "number" | "string":
                    return True
                case "array" | "tuple":
                    return True
                case "object":
                    return True
                case _:
                    return False
        elif target_type == "string":
            match source_type:
                case (
                    "array"
                    | "boolean"
                    | "enum"
                    | "integer"
                    | "number"
                    | "string"
                    | "tuple"
                ):
                    return True
                case "object":
                    return True
                case _:
                    return False
        elif target_type == "array":
            target_array_schema = target_schema["items"]
            match source_type:
                case "boolean" | "integer" | "number" | "string":
                    return match_schema(
                        source_schema,
                        target_array_schema,
                        source_root=source_root,
                        target_root=target_root,
                        depth=depth + 1,
                    )
                case "array":
                    source_array_schema = source_schema["items"]
                    return match_schema(
                        source_array_schema,
                        target_array_schema,
                        source_root=source_root,
                        target_root=target_root,
                        depth=depth + 1,
                    )
                case "tuple":
                    source_items_types = source_schema["items"]
                    for item_type in source_items_types:
                        valid = match_schema(
                            item_type,
                            target_array_schema,
                            source_root=source_root,
                            target_root=target_root,
                            depth=depth + 1,
                        )
                        if not valid:
                            # One of the elements is not matchable
                            return False
                    return True
                case _:
                    return False
        elif target_type == "enum":
            match source_type:
                case "array" | "boolean" | "integer" | "number" | "string" | "tuple":
                    return True
                case _:
                    return False
        elif target_type == "tuple":
            target_items_types = target_schema["items"]
            match source_type:
                case "boolean" | "integer" | "number" | "string":
                    if len(target_items_types) == 1:
                        return match_schema(
                            source_schema,
                            target_array_schema,
                            source_root=source_root,
                            target_root=target_root,
                            depth=depth + 1,
                        )
                    else:
                        return False
                case "array":
                    source_array_schema = source_schema["items"]
                    for item_type in target_items_types:
                        valid = match_schema(
                            source_array_schema,
                            item_type,
                            source_root=source_root,
                            target_root=target_root,
                            depth=depth + 1,
                        )
                        if not valid:
                            return False
                    return True
                case "tuple":
                    source_items_types = source_schema["items"]
                    for source_type, target_type in zip(
                        source_items_types, target_items_types
                    ):
                        valid = match_schema(
                            source_type,
                            target_type,
                            source_root=source_root,
                            target_root=target_root,
                            depth=depth + 1,
                        )
                        if not valid:
                            return False
                    return True
                case _:
                    return False
        elif target_type == "object":
            target_properties = target_schema["properties"]
            match source_type:
                case "boolean" | "integer" | "number" | "string":
                    return True
                case "object":
                    source_properties = source_schema["properties"]
                    common_properties = (
                        target_properties.keys() & source_properties.keys()
                    )
                    new_properties = target_properties.keys() - source_properties.keys()
                    deleted_properties = (
                        source_properties.keys() - target_properties.keys()
                    )
                    for prop in common_properties:
                        valid = match_schema(
                            source_properties[prop],
                            target_properties[prop],
                            source_root=source_root,
                            target_root=target_root,
                            depth=depth + 1,
                        )
                        if not valid:
                            return False
                    if len(new_properties) == 1 and len(deleted_properties) == 1:
                        new_prop = next(iter(new_properties))
                        deleted_prop = next(iter(deleted_properties))
                        valid = match_schema(
                            source_properties[deleted_prop],
                            target_properties[new_prop],
                            source_root=source_root,
                            target_root=target_root,
                            depth=depth + 1,
                        )
                        if not valid:
                            return False
                    return True
                case _:
                    return False
    else:
        return False
    return False

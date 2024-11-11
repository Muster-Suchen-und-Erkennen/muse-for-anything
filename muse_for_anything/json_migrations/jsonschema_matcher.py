import copy


def extract_type(schema):
    """Extract the type of a given schema and indicates
    whether or not elements are nullable

    Args:
        schema (dict): A JSONSchema saved in a python dict

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


def match_schema(root_schemas, source, target, depth=0):
    """Going from the source schema, it is checked whether a conversion to
    the target schema is possible.
    Unsupported conversions are: \n
    array to enum, array to object, enum to array, enum to object, enum to tuple,
    object to array, object to enum, object to tuple, tuple to enum, and
    tuple to object. These might need an intermediate conversion step, e. g.
    via boolean, integer, number, or string.

    Args:
        root_schemas (tuple): A tuple of the root source schema and root target schema
        source (dict): The source JSONSchema
        target (dict): The target JSONSchema

    Returns:
        bool: Returns True if schemas could be matched, else False
    """
    if "definitions" in source:
        source = source["definitions"]["root"]
    if "definitions" in target:
        target = target["definitions"]["root"]
    if depth > 100:
        raise ValueError("Schema nested too deep")
    source_type, source_nullable = extract_type(source)
    target_type, target_nullable = extract_type(target)
    # Check if both schemas have valid types
    # TODO: Implement "sanity checks" for updates
    if source_type and target_type:
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
            target_array_schema = target["items"]
            match source_type:
                case "boolean" | "integer" | "number" | "string":
                    return match_schema(
                        root_schemas, source, target_array_schema, depth + 1
                    )
                case "array":
                    source_array_schema = source["items"]
                    return match_schema(
                        root_schemas, source_array_schema, target_array_schema, depth + 1
                    )
                case "tuple":
                    source_items_types = source["items"]
                    for item_type in source_items_types:
                        valid = match_schema(
                            root_schemas, item_type, target_array_schema, depth + 1
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
            target_items_types = target["items"]
            match source_type:
                case "boolean" | "integer" | "number" | "string":
                    if len(target_items_types) == 1:
                        return match_schema(
                            root_schemas, source, target_array_schema, depth + 1
                        )
                    else:
                        return False
                case "array":
                    source_array_schema = source["items"]
                    for item_type in target_items_types:
                        valid = match_schema(
                            root_schemas, source_array_schema, item_type, depth + 1
                        )
                        if not valid:
                            return False
                    return True
                case "tuple":
                    source_items_types = source["items"]
                    for source_type, target_type in zip(
                        source_items_types, target_items_types
                    ):
                        valid = match_schema(
                            root_schemas, source_type, target_type, depth + 1
                        )
                        if not valid:
                            return False
                    return True
                case _:
                    return False
        elif target_type == "object":
            target_properties = target["properties"]
            match source_type:
                case "boolean" | "integer" | "number" | "string":
                    return True
                case "object":
                    source_properties = source["properties"]
                    common_properties = (
                        target_properties.keys() & source_properties.keys()
                    )
                    new_properties = target_properties.keys() - source_properties.keys()
                    deleted_properties = (
                        source_properties.keys() - target_properties.keys()
                    )
                    for prop in common_properties:
                        valid = match_schema(
                            root_schemas,
                            source_properties[prop],
                            target_properties[prop],
                            depth + 1,
                        )
                        if not valid:
                            return False
                    if len(new_properties) == 1 and len(deleted_properties) == 1:
                        new_prop = next(iter(new_properties))
                        deleted_prop = next(iter(deleted_properties))
                        valid = match_schema(
                            root_schemas,
                            source_properties[deleted_prop],
                            target_properties[new_prop],
                            depth + 1,
                        )
                        if not valid:
                            return False
                    return True
                case _:
                    return False
    else:
        return False
    return False

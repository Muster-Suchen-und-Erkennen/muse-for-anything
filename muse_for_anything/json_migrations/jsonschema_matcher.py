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
    temp_schema = copy.deepcopy(schema)
    definitions = temp_schema["definitions"]["root"]
    keys = definitions.keys()
    nullable = False
    # Enum and $ref are defined separately, not in type
    if "enum" in keys:
        return "enum", nullable
    elif "$ref" in keys:
        return "schemaReference", nullable
    # Handling of other types
    elif "type" in keys:
        # Check if elements nullable
        if "null" in definitions["type"]:
            nullable = True
            definitions["type"].remove("null")
        match definitions["type"]:
            case ["object"]:
                # ResourceReference also defined as object
                if "customType" in keys:
                    if definitions["customType"] == "resourceReference":
                        return "resourceReference", nullable
                    else:
                        raise ValueError("Unknown object type!")
                else:
                    return "object", nullable
            case ["array"]:
                # Tuple and Array identified by arrayType entry
                if "arrayType" in keys:
                    if definitions["arrayType"] == "array":
                        return "array", nullable
                    elif definitions["arrayType"] == "tuple":
                        return "tuple", nullable
                    else:
                        raise ValueError("Unknown array type!")
                else:
                    raise ValueError("No array type given!")
            case ["boolean"]:
                return "boolean", nullable
            case ["integer"]:
                return "integer", nullable
            case ["number"]:
                return "number", nullable
            case ["string"]:
                return "string", nullable
            case _:
                raise ValueError("Unknown type!")
    else:
        raise ValueError("No type definition found!")


def match_schema(source, target):
    """Going from the source schema, it is checked whether a conversion to
    the target schema is possible. That information and also the types of
    the schemas and whether elements are nullable are returned. \n
    Unsupported conversions are: \n
    array to enum, array to object, enum to array, enum object, enum to tuple,
    object to array, object to enum, object to tuple, tuple to enum, and
    tuple to object. These might need an intermediate conversion step, e. g.
    via boolean, integer, number, or string.

    Args:
        source (dict): The source JSONSchema
        target (dict): The target JSONSchema

    Returns:
        dict: A dictionary with five keys \n
        "unsupported_conversion": indicates whether the conversion is possible or not, \n
        "source_type": indicates the source schema's main type, \n
        "source_nullable": indicates whether elements in the source schema are nullable, \n
        "target_type": indicate the target schema's main type, \n
        "target_nullable": indicates whether elements in the target schema are nullable
    """
    unsupported_conversion = False
    source_type, source_nullable = extract_type(source)
    target_type, target_nullable = extract_type(target)
    # Check if both schemas have valid types
    if source_type and target_type:
        match target_type:
            case "array":
                if source_type not in [
                    "array",
                    "boolean",
                    "integer",
                    "number",
                    "string",
                    "tuple",
                ]:
                    unsupported_conversion = True
            case "enum":
                if source_type not in [
                    "array",
                    "boolean",
                    "enum",
                    "integer",
                    "number",
                    "string",
                    "tuple",
                ]:
                    unsupported_conversion = True
            case "number":
                if source_type not in [
                    "array",
                    "boolean",
                    "enum",
                    "integer",
                    "number",
                    "object",
                    "string",
                    "tuple",
                ]:
                    unsupported_conversion = True
            case "integer":
                if source_type not in [
                    "array",
                    "boolean",
                    "enum",
                    "integer",
                    "number",
                    "object",
                    "string",
                    "tuple",
                ]:
                    unsupported_conversion = True
            case "boolean":
                if source_type not in [
                    "array",
                    "boolean",
                    "enum",
                    "integer",
                    "number",
                    "object",
                    "string",
                    "tuple",
                ]:
                    unsupported_conversion = True
            case "string":
                if source_type not in [
                    "array",
                    "boolean",
                    "enum",
                    "integer",
                    "number",
                    "object",
                    "string",
                    "tuple",
                ]:
                    unsupported_conversion = True
            case "tuple":
                if source_type not in [
                    "array",
                    "boolean",
                    "integer",
                    "number",
                    "string",
                    "tuple",
                ]:
                    unsupported_conversion = True
            case "object":
                if source_type not in [
                    "boolean",
                    "integer",
                    "number",
                    "object",
                    "string",
                ]:
                    unsupported_conversion = True
            case _:
                unsupported_conversion = True
    return {
        "unsupported_conversion": unsupported_conversion,
        "source_type": source_type,
        "source_nullable": source_nullable,
        "target_type": target_type,
        "target_nullable": target_nullable,
    }

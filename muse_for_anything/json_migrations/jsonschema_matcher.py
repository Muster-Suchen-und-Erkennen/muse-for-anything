def extract_type(schema):
    definitions = schema["definitions"]["root"]
    keys = definitions.keys()
    nullable = False
    if "enum" in keys:
        return "enum", nullable
    elif "$ref" in keys:
        return "schemaReference", nullable
    elif "type" in keys:
        if "null" in definitions["type"]:
            nullable = True
            definitions["type"].remove("null")
        match definitions["type"]:
            case ["object"]:
                if "customType" in keys:
                    if definitions["customType"] == "resourceReference":
                        return "resourceReference", nullable
                    else:
                        raise ValueError("Unknown object type!")
                else:
                    return "object", nullable
            case ["array"]:
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
    unsupported_conversion = False
    source_type, source_nullable = extract_type(source)
    target_type, target_nullable = extract_type(target)
    if source_type and target_type:
        match target_type:
            case "array":
                if source_type not in ["boolean", "integer", "number", "string"]:
                    unsupported_conversion = True
            case "number":
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
            case "integer":
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
            case "boolean":
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
            case _:
                unsupported_conversion = True
    return {
        "unsupported_conversion": unsupported_conversion,
        "source_type": source_type,
        "source_nullable": source_nullable,
        "target_type": target_type,
        "target_nullable": target_nullable,
    }

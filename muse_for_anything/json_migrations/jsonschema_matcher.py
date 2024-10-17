from muse_for_anything.json_migrations.constants import *


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
    transformations = []
    source_type = extract_type(source)[0]
    target_type = extract_type(target)[0]
    if source_type and target_type:
        if source_type == target_type:
            transformations.append("No type changes!")
        else:
            match target_type:
                case "number":
                    if source_type in ["boolean", "integer", "number", "string"]:
                        transformations.append(CAST_TO_NUMBER)
                    else:
                        transformations.append(CAST_TO_ERROR)
                case "integer":
                    if source_type in ["boolean", "integer", "number", "string"]:
                        transformations.append(CAST_TO_INTEGER)
                    else:
                        transformations.append(CAST_TO_ERROR)
                case "boolean":
                    if source_type in ["boolean", "integer", "number", "string"]:
                        transformations.append(CAST_TO_BOOLEAN)
                    else:
                        transformations.append(CAST_TO_ERROR)
                case "string":
                    transformations.append(CAST_TO_STRING)
                case _:
                    transformations.append(CAST_TO_ERROR)
    return transformations

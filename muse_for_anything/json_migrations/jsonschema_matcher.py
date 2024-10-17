from muse_for_anything.json_migrations.constants import *


def extract_type(schema):
    definitions = schema["definitions"]["root"]
    keys = definitions.keys()
    if "enum" in keys:
        return "enum"
    elif "$ref" in keys:
        return "schemaReference"
    elif "type" in keys:
        match definitions["type"]:
            case ["object"]:
                if "customType" in keys:
                    if definitions["customType"] == "resourceReference":
                        return "resourceReference"
                    else:
                        raise ValueError("Unknown object type!")
                else:
                    return "object"
            case ["array"]:
                if "arrayType" in keys:
                    if definitions["arrayType"] == "array":
                        return "array"
                    elif definitions["arrayType"] == "tuple":
                        return "tuple"
                    else:
                        raise ValueError("Unknown array type!")
                else:
                    raise ValueError("No array type given!")
            case ["boolean"]:
                return "boolean"
            case ["integer"]:
                return "integer"
            case ["number"]:
                return "number"
            case ["string"]:
                return "string"
            case _:
                raise ValueError("Unknown type!")
    else:
        raise ValueError("No type definition found!")


def match_schema(source, target):
    transformations = []
    source_type = extract_type(source)
    target_type = extract_type(target)
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

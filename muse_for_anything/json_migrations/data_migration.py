from jsonschema import Draft7Validator
import muse_for_anything.json_migrations.constants as constants


def migrate_object(data_object, old_type, target_schema, transformations):
    # validator = Draft7Validator(target_schema)
    for transformation in transformations:
        try:
            match transformation:
                case constants.CAST_TO_NUMBER:
                    data_object = migrate_to_number(data_object, old_type)
                case constants.CAST_TO_INTEGER:
                    data_object = migrate_to_integer(data_object, old_type)
                case constants.CAST_TO_STRING:
                    data_object = migrate_to_string(data_object, old_type)
        except ValueError:
            data_object = data_object
    return data_object


def migrate_to_number(data_object, old_type, cap_at_limit: bool = False):
    match old_type:
        case "number" | "integer":
            # TODO Implement potential cut off at limit
            # For now, no adaptations necessary, just check with draftvalidator
            try:
                data_object["data"]["data"] = float(data_object["data"]["data"])
            except ValueError:
                raise ValueError("No transformation to number possible!")
        case "string" | "boolean" | "string":
            try:
                data_object["data"]["data"] = float(data_object["data"]["data"])
            except ValueError:
                raise ValueError("No transformation to number possible!")
    return data_object


def migrate_to_integer(data_object, old_type):
    match old_type:
        case "number" | "integer":
            # TODO Implement potential cut off at limit
            # For now, no adaptations necessary, just check with draftvalidator
            try:
                data_object["data"]["data"] = int(data_object["data"]["data"])
            except ValueError:
                raise ValueError("No transformation to number possible!")
        case "boolean" | "string":
            try:
                data_object["data"]["data"] = int(float(data_object["data"]["data"]))
            except ValueError:
                raise ValueError("No transformation to integer possible!")
    return data_object


def migrate_to_string(data_object, old_type):
    match old_type:
        case (
            "array"
            | "boolean"
            | "enum"
            | "integer"
            | "number"
            | "object"
            | "string"
            | "tuple"
        ):
            try:
                data_object["data"]["data"] = str(data_object["data"]["data"])
            except ValueError:
                raise ValueError("No transformation to string possible!")
        case "$ref":
            # TODO Implement check whether ref to string?
            # Probably unnecessary if refs are resolved beforehand
            raise ValueError("Not implemented yet!")
    return data_object


def migrate_to_bool(data_object, old_type):
    pass


def migrate_to_enum(data_object, old_type):
    pass


def migrate_to_array(data_object, old_type):
    pass


def migrate_to_object(data_object, old_type):
    pass


def migrate_to_tuple(data_object, old_type):
    pass

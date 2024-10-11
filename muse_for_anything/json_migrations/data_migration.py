from jsonschema import Draft7Validator
from muse_for_anything.json_migrations.constants import *


def migrate_object(data_object, target_schema, transformations):
    # validator = Draft7Validator(target_schema)
    for transformation in transformations:
        match transformation:
            case "Cast to number!":
                migrate_to_number(data_object)
            case "Cast to integer!":
                migrate_to_integer(data_object)
            case "Cast to string!":
                migrate_to_string(data_object)
    return data_object


def migrate_to_number(data_object, old_type, cap_at_limit: bool = False):
    match old_type:
        case "number" | "integer":
            # TODO Implement potential cut off at limit
            # For now, no adaptations necessary, just check with draftvalidator
            pass
        case "string" | "boolean" | "string":
            try:
                data_object["data"]["data"] = float(data_object["data"]["data"])
            except ValueError:
                raise ValueError("No transformation to number possible!")


def migrate_to_integer(data_object, old_type):
    match old_type:
        case "number" | "string":
            try:
                data_object["data"]["data"] = int(float(data_object["data"]["data"]))
            except ValueError:
                raise ValueError("No transformation to integer possible!")


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

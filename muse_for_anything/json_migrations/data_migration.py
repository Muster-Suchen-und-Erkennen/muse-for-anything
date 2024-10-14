from jsonschema import Draft7Validator
from muse_for_anything.json_migrations.jsonschema_matcher import match_schema
import muse_for_anything.json_migrations.constants as constants


def migrate_object(data_object, old_type, source_schema, target_schema):
    # TODO Add check with validator whether object satisfies schema
    # validator = Draft7Validator(target_schema)
    transformations = match_schema(source_schema, target_schema)
    data = data_object["data"]["data"]
    updated_data = None
    for transformation in transformations:
        try:
            match transformation:
                case constants.CAST_TO_NUMBER:
                    updated_data = migrate_to_number(data, old_type)
                case constants.CAST_TO_INTEGER:
                    updated_data = migrate_to_integer(data, old_type)
                case constants.CAST_TO_STRING:
                    updated_data = migrate_to_string(data, old_type)
                case constants.CAST_TO_BOOLEAN:
                    updated_data = migrate_to_boolean(data, old_type)
        except ValueError:
            continue
    if updated_data is not None:
        data_object["data"]["data"] = updated_data
    return data_object


def migrate_to_number(data, old_type, cap_at_limit: bool = False):
    match old_type:
        case "number" | "integer":
            # TODO Implement potential cut off at limit
            try:
                data = float(data)
            except ValueError:
                raise ValueError("No transformation to number possible!")
        case "boolean" | "string" | "enum":
            try:
                data = float(data)
            except ValueError:
                raise ValueError("No transformation to number possible!")
        case "array":
            if len(data) == 1:
                try:
                    data = float(data[0])
                except ValueError:
                    raise ValueError("No transformation to number possible!")
            else:
                raise ValueError("No transformation to number possible!")
        case "tuple":
            count_of_numbers = 0
            transformed_data = None
            for entry in data:
                try:
                    transformed_data = float(entry)
                    count_of_numbers += 1
                except ValueError:
                    pass
            if count_of_numbers == 1:
                data = transformed_data
            else:
                raise ValueError("No transformation to number possible!")
    return data


def migrate_to_integer(data, old_type):
    match old_type:
        case "number" | "integer":
            # TODO Implement potential cut off at limit
            try:
                data = int(data)
            except ValueError:
                raise ValueError("No transformation to integer possible!")
        case "boolean" | "string" | "enum":
            try:
                data = int(float(data))
            except ValueError:
                raise ValueError("No transformation to integer possible!")
        case "array":
            if len(data) == 1:
                try:
                    data = int(float(data[0]))
                except ValueError:
                    raise ValueError("No transformation to integer possible!")
            else:
                raise ValueError("No transformation to integer possible!")
        case "tuple":
            count_of_numbers = 0
            transformed_data = None
            for entry in data:
                try:
                    transformed_data = int(float(entry))
                    count_of_numbers += 1
                except ValueError:
                    pass
            if count_of_numbers == 1:
                data = transformed_data
            else:
                raise ValueError("No transformation to integer possible!")
    return data


def migrate_to_string(data, old_type):
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
                data = str(data)
            except ValueError:
                raise ValueError("No transformation to string possible!")
        case "$ref":
            # TODO Implement check whether ref to string?
            # Probably unnecessary if refs are resolved beforehand
            raise ValueError("Not implemented yet!")
    return data


def migrate_to_boolean(data, old_type):
    match old_type:
        case "number" | "integer" | "string" | "enum":
            # TODO Implement potential cut off at limit
            try:
                data = bool(data)
            except ValueError:
                raise ValueError("No transformation to number possible!")
    return data


def migrate_to_enum(data, old_type):
    pass


def migrate_to_array(data, old_type):
    pass


def migrate_to_object(data, old_type):
    pass


def migrate_to_tuple(data, old_type):
    pass

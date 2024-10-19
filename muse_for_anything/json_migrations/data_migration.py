from jsonschema import Draft7Validator
from muse_for_anything.json_migrations.jsonschema_matcher import match_schema


def migrate_object(data_object, source_schema, target_schema):
    # TODO Add check with validator whether object satisfies schema
    # validator = Draft7Validator(target_schema)
    migration_plan = match_schema(source_schema, target_schema)
    if migration_plan["unsupported_conversion"]:
        raise ValueError("Unsupported transformation attempted!")
    source_type = migration_plan["source_type"]
    source_nullable = migration_plan["source_nullable"]
    target_type = migration_plan["target_type"]
    target_nullable = migration_plan["target_nullable"]
    data = data_object["data"]["data"]
    updated_data = None
    try:
        match target_type:
            case "number":
                updated_data = migrate_to_number(data, source_type)
            case "integer":
                updated_data = migrate_to_integer(data, source_type)
            case "string":
                updated_data = migrate_to_string(data, source_type)
            case "boolean":
                updated_data = migrate_to_boolean(data, source_type)
    except ValueError:
        return data_object
    if updated_data is not None:
        data_object["data"]["data"] = updated_data
    return data_object


def migrate_to_number(data, source_type, cap_at_limit: bool = False):
    match source_type:
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


def migrate_to_integer(data, source_type):
    match source_type:
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


def migrate_to_string(data, source_type):
    match source_type:
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


def migrate_to_boolean(data, source_type):
    match source_type:
        case "number" | "integer" | "string" | "enum":
            # TODO Implement potential cut off at limit
            try:
                data = bool(data)
            except ValueError:
                raise ValueError("No transformation to boolean possible!")
    return data


def migrate_to_enum(data, source_type):
    pass


def migrate_to_array(data, source_type):
    pass


def migrate_to_object(data, source_type):
    pass


def migrate_to_tuple(data, source_type):
    pass

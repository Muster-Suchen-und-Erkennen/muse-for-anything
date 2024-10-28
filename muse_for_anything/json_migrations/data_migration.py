import numbers
from jsonschema import Draft7Validator
from muse_for_anything.json_migrations.jsonschema_matcher import match_schema


def migrate_object(data, source_schema, target_schema):
    # TODO Add check with validator whether object satisfies schema
    # validator = Draft7Validator(target_schema)
    migration_plan = match_schema(source_schema, target_schema)
    if migration_plan["unsupported_conversion"]:
        raise ValueError("Unsupported transformation attempted!")
    source_type = migration_plan["source_type"]
    source_nullable = migration_plan["source_nullable"]
    target_type = migration_plan["target_type"]
    target_nullable = migration_plan["target_nullable"]
    updated_data = None
    try:
        if target_type == "array":
            array_data_type = target_schema["definitions"]["root"]["items"]["type"]
            updated_data = migrate_to_array(
                data, source_type, source_schema, array_data_type, target_nullable
            )
        elif target_type == "boolean":
            updated_data = migrate_to_boolean(data, source_type, target_nullable)
        elif target_type == "enum":
            allowed_values = target_schema["definitions"]["root"]["enum"]
            updated_data = migrate_to_enum(data, allowed_values, target_nullable)
        elif target_type == "integer":
            updated_data = migrate_to_integer(data, source_type, target_nullable)
        elif target_type == "number":
            updated_data = migrate_to_number(data, source_type, target_nullable)
        elif target_type == "string":
            updated_data = migrate_to_string(data, source_type, source_schema, target_nullable)
        elif target_type == "tuple":
            updated_data = migrate_to_tuple(data, source_type, source_schema, target_schema, target_nullable)
    except ValueError:
        return data
    if updated_data is not None:
        data = updated_data
    return data


def migrate_to_number(data, source_type, target_nullable):
    match source_type:
        case "boolean" | "enum" | "number" | "integer" | "string":
            # TODO Implement potential cut off at limit
            try:
                data = float(data)
            except ValueError:
                raise ValueError("No transformation to number possible!")
        case "array":
            if len(data) == 1:
                try:
                    data = float(data[0])
                except ValueError:
                    raise ValueError(
                        "No transformation from this array with one entry to number possible!"
                    )
            else:
                raise ValueError(
                    "No transformation from longer arrays to number possible!"
                )
        case "object":
            if len(data) == 0:
                data = 0.0
            elif len(data) == 1:
                for value in data.values():
                    data = float(value)
            else:
                amount_of_numbers = 0
                temporary = None
                for key, value in data.items():
                    try:
                        temporary = float(data[key])
                        amount_of_numbers += 1
                    except:
                        continue
                if amount_of_numbers == 1:
                    data = temporary
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
                raise ValueError("No transformation from this tuple to number possible!")
    return data


def migrate_to_integer(data, source_type, target_nullable):
    match source_type:
        case "boolean" | "enum" | "number" | "integer" | "string":
            # TODO Implement potential cut off at limit
            try:
                data = int(float(data))
            except ValueError:
                raise ValueError("No transformation to integer possible!")
        case "array":
            if len(data) == 1:
                try:
                    data = int(float(data[0]))
                except ValueError:
                    raise ValueError(
                        "No transformation from this array with one entry to integer possible!"
                    )
            else:
                raise ValueError(
                    "No transformation from longer arrays to integer possible!"
                )
        case "object":
            if len(data) == 0:
                data = 0
            elif len(data) == 1:
                for value in data.values():
                    data = int(float(value))
            else:
                amount_of_ints = 0
                temporary = None
                for key, value in data.items():
                    try:
                        temporary = int(float(data[key]))
                        amount_of_ints += 1
                    except:
                        continue
                if amount_of_ints == 1:
                    data = temporary
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
                raise ValueError("No transformation from this tuple to integer possible!")
    return data


def migrate_to_string(data, source_type, source_schema, target_nullable):
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
            try:
                data = str(data)
            except ValueError:
                raise ValueError("No transformation to string possible!")
        case "object":
            data_string = ""
            properties = source_schema["definitions"]["root"]["properties"]
            for property in properties.keys():
                data_string += property + ": " + str(data[property]) + ", "
            data = data_string[:-2]
        case "$ref":
            # TODO Implement check whether ref to string?
            # Probably unnecessary if refs are resolved beforehand
            raise ValueError("Not implemented yet!")
    return data


def migrate_to_boolean(data, source_type, target_nullable):
    match source_type:
        case "boolean" | "enum" | "integer" | "number" | "string":
            try:
                data = bool(data)
            except ValueError:
                raise ValueError("No transformation to boolean possible!")
        case "object":
            if len(data) == 0:
                data = False
            elif len(data) == 1:
                for value in data.values():
                    data = bool(value)
            else:
                amount_of_booleans = 0
                temporary = None
                for key, value in data.items():
                    if value == True or value == False:
                        amount_of_booleans += 1
                        temporary = data[key]
                if amount_of_booleans == 1:
                    data = temporary
        case "array" | "tuple":
            try:
                if False in data or len(data) == 0:
                    data = False
                else:
                    data = bool(data)
            except ValueError:
                raise ValueError("No transformation to boolean possible!")
    return data


def migrate_to_enum(data, allowed_values, target_nullable):
    if isinstance(data, numbers.Number):
        temp_data = data
        for value in allowed_values:
            if isinstance(value, numbers.Number) and round(value) == round(temp_data):
                temp_data = value
        data = temp_data
    elif isinstance(data, list) and len(data) == 1:
        data = data[0]
    if data in allowed_values:
        return data
    else:
        raise ValueError("No transformation to enum possible!")


def migrate_to_array(data, source_type, source_schema, array_data_type, target_nullable):
    elements_nullable = False
    if "null" in array_data_type:
        elements_nullable = True
        array_data_type.remove("null")
    try:
        if array_data_type[0] == "boolean":
            data = [migrate_to_boolean(data, source_type, elements_nullable)]
        elif array_data_type[0] == "integer":
            data = [migrate_to_integer(data, source_type, elements_nullable)]
        elif array_data_type[0] == "number":
            data = [migrate_to_number(data, source_type, elements_nullable)]
        elif array_data_type[0] == "string":
            data = [migrate_to_string(data, source_type, source_schema, elements_nullable)]
    except ValueError:
        raise ValueError("No transformation to array possible!")
    return data


def migrate_to_object(data, source_type, source_schema, target_schema, target_nullable):
    pass


def migrate_to_tuple(data, source_type, source_schema, target_schema, target_nullable):
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            if len(target_schema["definitions"]["root"]["items"]) == 1:
                try:
                    item_nullable = False
                    if "null" in target_schema["definitions"]["root"]["items"][0]["type"]:
                        item_nullable = True
                        target_schema["definitions"]["root"]["items"][0]["type"].remove("null")
                    if target_schema["definitions"]["root"]["items"][0]["type"][0] == "boolean":
                        data = [migrate_to_boolean(data, source_type, item_nullable)]
                    elif target_schema["definitions"]["root"]["items"][0]["type"][0] == "integer":
                        data = [migrate_to_integer(data, source_type, item_nullable)]
                    elif target_schema["definitions"]["root"]["items"][0]["type"][0] == "number":
                        data = [migrate_to_number(data, source_type, item_nullable)]
                    elif target_schema["definitions"]["root"]["items"][0]["type"][0] == "string":
                        data = [migrate_to_string(data, source_type, source_schema, item_nullable)]
                    else:
                        raise ValueError("No transformation to tuple possible!")
                except ValueError:
                    raise ValueError("No transformation to enum possible!")
        case "enum":
            pass
        case "object":
            pass
        case "array":
            pass
        case "tuple":
            pass
    return data
 

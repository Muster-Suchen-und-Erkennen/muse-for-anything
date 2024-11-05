import numbers
from jsonschema import Draft7Validator
from muse_for_anything.json_migrations.jsonschema_matcher import match_schema


def migrate_data(data, source_schema, target_schema):
    """Using a migration plan, data conforming to the source schema is migrated
    to conform to the target schema if possible.

    Args:
        data: Data stored in a MUSE4Anything object
        source_schema (dict): The source JSONSchema
        target_schema (dict): The target JSONSchema

    Raises:
        ValueError: If transformation is not supported or possible to execute.

    Returns:
        If the update was successful, the updated data is returned, otherwise the
        original data is returned.
    """
    # TODO Add check with validator whether object satisfies schema
    # Maybe also outside of this method
    # validator = Draft7Validator(target_schema)

    # Get necessary information from the match_schema method
    migration_plan = match_schema(source_schema, target_schema)
    if migration_plan["unsupported_conversion"]:
        raise ValueError("Unsupported transformation attempted!")
    source_type = migration_plan["source_type"]
    source_nullable = migration_plan["source_nullable"]
    target_type = migration_plan["target_type"]
    target_nullable = migration_plan["target_nullable"]
    updated_data = None
    try:
        # Call appropriate method depending on target schema main type
        if target_type == "array":
            # Array needs additional information on element type
            array_data_type = target_schema["definitions"]["root"]["items"]["type"]
            updated_data = migrate_to_array(
                data, source_type, source_schema, array_data_type, target_nullable
            )
        elif target_type == "boolean":
            updated_data = migrate_to_boolean(data, source_type, target_nullable)
        elif target_type == "enum":
            # Enum needs the allowed values
            allowed_values = target_schema["definitions"]["root"]["enum"]
            updated_data = migrate_to_enum(data, allowed_values, target_nullable)
        elif target_type == "integer":
            updated_data = migrate_to_integer(data, source_type, target_nullable)
        elif target_type == "number":
            updated_data = migrate_to_number(data, source_type, target_nullable)
        elif target_type == "string":
            updated_data = migrate_to_string(
                data, source_type, source_schema, target_nullable
            )
        elif target_type == "tuple":
            updated_data = migrate_to_tuple(
                data, source_type, source_schema, target_schema, target_nullable
            )
        elif target_type == "object":
            updated_data = migrate_to_object(
                data, source_type, source_schema, target_schema, target_nullable
            )
    except ValueError:
        # TODO: Change to raise error further to indicate that update unsuccessful!
        return data
    return updated_data


def migrate_to_number(data, source_type, target_nullable):
    """Takes data and transforms it to a number/float instance.

    Args:
        data: Data potentially represented as a non-float
        source_type (str): Source type of data
        target_nullable (bool): Indicates whether data can be null/None

    Raises:
        ValueError: If transformation to number was not possible

    Returns:
        float: data represented as a float
    """
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
    """Takes data and transforms it to an integer instance.

    Args:
        data: Data potentially represented as a non-integer
        source_type (str): Source type of data
        target_nullable (bool): Indicates whether data can be null/None

    Raises:
        ValueError: If transformation to integer was not possible

    Returns:
        int: data represented as an integer
    """
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
    """Takes data and transforms it to a string instance.

    Args:
        data: Data potentially represented as a non-string
        source_type (str): Source type of data
        source_schema (dict): Source JSONSchema to allow better conversion
        target_nullable (bool): Indicates whether data can be null/None

    Raises:
        ValueError: If transformation to string was not possible

    Returns:
        str: data represented as a string
    """
    match source_type:
        case "array" | "boolean" | "enum" | "integer" | "number" | "string" | "tuple":
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
    """Takes data and transforms it to a boolean instance.

    Args:
        data: Data potentially represented as a non-boolean
        source_type (str): Source type of data
        target_nullable (bool): Indicates whether data can be null/None

    Raises:
        ValueError: If transformation to boolean was not possible

    Returns:
        bool: data represented as a boolean
    """
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
    """Takes data and ensures it conforms to the allowed values of the
    defined enum.

    Args:
        data: Data potentially not part of the enum
        allowed_values (list): A list of values accepted in the enum
        target_nullable (bool): Indicates whether data can be null/None

    Raises:
        ValueError: If data is not part of the defined enum

    Returns:
        _type_: data fitted to the enum
    """
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
    """Takes data and transforms it to an array instance.

    Args:
        data: Data potentially represented as a non-array
        source_type (str): Source type of data
        source_schema (dict): Source JSONSchema to allow better conversion
        array_data_type (str): Indicates the data type of the elements of an array
        target_nullable (bool): Indicates whether data can be null/None

    Raises:
        ValueError: If transformation to array was not possible

    Returns:
        list: data represented as an array
    """
    elements_nullable = "null" in array_data_type
    elements_data_type = next(t for t in array_data_type if t != "null")
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            try:
                if elements_data_type == "boolean":
                    data = [migrate_to_boolean(data, source_type, elements_nullable)]
                elif elements_data_type == "integer":
                    data = [migrate_to_integer(data, source_type, elements_nullable)]
                elif elements_data_type == "number":
                    data = [migrate_to_number(data, source_type, elements_nullable)]
                elif elements_data_type == "string":
                    data = [
                        migrate_to_string(
                            data, source_type, source_schema, elements_nullable
                        )
                    ]
            except ValueError:
                raise ValueError("No transformation to array possible!")

        case "array":
            source_array_def = source_schema["definitions"]["root"]["items"]["type"]
            source_elements_type = next(t for t in source_array_def if t != "null")
            if elements_data_type == "boolean":
                data = [
                    migrate_to_boolean(element, source_elements_type, elements_nullable)
                    for element in data
                ]
            elif elements_data_type == "integer":
                data = [
                    migrate_to_integer(element, source_elements_type, elements_nullable)
                    for element in data
                ]
            elif elements_data_type == "number":
                data = [
                    migrate_to_number(element, source_elements_type, elements_nullable)
                    for element in data
                ]
            elif elements_data_type == "string":
                data = [
                    migrate_to_string(
                        element, source_elements_type, source_schema, elements_nullable
                    )
                    for element in data
                ]
        case "tuple":
            source_items_types = source_schema["definitions"]["root"]["items"]
            for index, (data_element, data_element_def) in enumerate(
                zip(data, source_items_types)
            ):
                data_element_nullable = "null" in data_element_def["type"]
                data_element_type = next(
                    t for t in data_element_def["type"] if t != "null"
                )
                if elements_data_type == "boolean":
                    data[index] = migrate_to_boolean(
                        data_element, data_element_type, data_element_nullable
                    )
                elif elements_data_type == "integer":
                    data[index] = migrate_to_integer(
                        data_element, data_element_type, data_element_nullable
                    )
                elif elements_data_type == "number":
                    data[index] = migrate_to_number(
                        data_element, data_element_type, data_element_nullable
                    )
                elif elements_data_type == "string":
                    data[index] = migrate_to_string(
                        data_element,
                        data_element_type,
                        source_schema,
                        data_element_nullable,
                    )
    return data


def migrate_to_object(data, source_type, source_schema, target_schema, target_nullable):
    """Takes data and transforms it to an object instance.

    Args:
        data: Data potentially represented as a non-object
        source_type (str): Source type of data
        source_schema (dict): Source JSONSchema to allow better conversion
        target_schema (dict): Target JSONSchema to allow better conversion
        target_nullable (bool): Indicates whether data can be null/None

    Raises:
        ValueError: If transformation to object was not possible

    Returns:
        dict: Data represented as an object
    """
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            properties = target_schema["definitions"]["root"]["properties"]
            if len(properties) == 1:
                try:
                    prop_name = next(iter(properties))
                    prop_def = properties[prop_name]["type"]
                    item_nullable = "null" in prop_def
                    prop_type = next(t for t in prop_def if t != "null")
                    if prop_type == "boolean":
                        data = {
                            prop_name: migrate_to_boolean(
                                data, source_type, item_nullable
                            )
                        }
                    elif prop_type == "integer":
                        data = {
                            prop_name: migrate_to_integer(
                                data, source_type, item_nullable
                            )
                        }
                    elif prop_type == "number":
                        data = {
                            prop_name: migrate_to_number(data, source_type, item_nullable)
                        }
                    elif prop_type == "string":
                        data = {
                            prop_name: migrate_to_string(
                                data, source_type, source_schema, item_nullable
                            )
                        }
                    else:
                        raise ValueError("No transformation to tuple possible!")
                except ValueError:
                    raise ValueError("No transformation to enum possible!")
        case "object":
            source_properties = get_object_properties(source_schema)
            target_properties = get_object_properties(target_schema)
            props_to_del = []
            props_to_add = []
            for prop, prop_type in source_properties.items():
                # Matching properties in source and target schema
                if prop in target_properties:
                    if target_properties[prop][0] == "boolean":
                        data[prop] = migrate_to_boolean(
                            data[prop], prop_type, target_properties[prop][1]
                        )
                    if target_properties[prop][0] == "integer":
                        data[prop] = migrate_to_integer(
                            data[prop], prop_type, target_properties[prop][1]
                        )
                    if target_properties[prop][0] == "number":
                        data[prop] = migrate_to_number(
                            data[prop], prop_type, target_properties[prop][1]
                        )
                    if target_properties[prop][0] == "string":
                        # TODO: Need to correct passing of source_schema, should be sub-schema of property (relevant esp for object)
                        data[prop] = migrate_to_string(
                            data[prop],
                            prop_type[0],
                            source_schema,
                            target_properties[prop][1],
                        )
                # Properties that are in source but not in target
                else:
                    props_to_del.append(prop)
            # Find new properties
            for prop, prop_type in target_properties.items():
                if prop not in source_properties:
                    props_to_add.append(prop)
            # One prop added, one deleted, likely name changes
            if len(props_to_add) == 1 and len(props_to_del) == 1:
                source_type = source_properties[props_to_del[0]]
                target_type = target_properties[props_to_add[0]]
                if target_type[0] == "boolean":
                    data[props_to_add[0]] = migrate_to_boolean(
                        data[props_to_del[0]], source_type[0], target_type[1]
                    )
                if target_type[0] == "integer":
                    data[props_to_add[0]] = migrate_to_integer(
                        data[props_to_del[0]], source_type[0], target_type[1]
                    )
                if target_type[0] == "number":
                    data[props_to_add[0]] = migrate_to_number(
                        data[props_to_del[0]], source_type[0], target_type[1]
                    )
                if target_type[0] == "string":
                    # TODO: Pass correct source schema!
                    data[props_to_add[0]] = migrate_to_string(
                        data[props_to_del[0]],
                        source_type[0],
                        source_schema,
                        target_type[1],
                    )
                del data[props_to_del[0]]
            # More than one added or deleted
            else:
                # Add all new properties
                for prop in props_to_add:
                    # TODO: Default data values?
                    if target_properties[prop][1]:
                        data[prop] = None
                # Delete all old properties
                for prop in props_to_del:
                    del data[prop]
    return data


def get_object_properties(schema):
    properties = dict()
    for prop, schema in schema["definitions"]["root"]["properties"].items():
        is_nullable = "null" in schema["type"]
        prop_type = next(t for t in schema["type"] if t != "null")
        properties[prop] = prop_type, is_nullable
    return properties


def migrate_to_tuple(data, source_type, source_schema, target_schema, target_nullable):
    """Takes data and transforms it to a tuple instance.

    Args:
        data: Data potentially represented as a non-tuple
        source_type (str): Source type of data
        source_schema (dict): Source JSONSchema to allow better conversion
        target_schema (dict): Target JSONSchema to allow better conversion
        target_nullable (bool): Indicates whether data can be null/None

    Raises:
        ValueError: If transformation to tuple was not possible

    Returns:
        list: Data represented as a tuple
    """
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            if len(target_schema["definitions"]["root"]["items"]) == 1:
                try:
                    type = target_schema["definitions"]["root"]["items"][0]["type"]
                    item_nullable = "null" in type
                    item_type = next(t for t in type if t != "null")
                    if item_type == "boolean":
                        data = [migrate_to_boolean(data, source_type, item_nullable)]
                    elif item_type == "integer":
                        data = [migrate_to_integer(data, source_type, item_nullable)]
                    elif item_type == "number":
                        data = [migrate_to_number(data, source_type, item_nullable)]
                    elif item_type == "string":
                        data = [
                            migrate_to_string(
                                data, source_type, source_schema, item_nullable
                            )
                        ]
                    else:
                        raise ValueError("No transformation to tuple possible!")
                except ValueError:
                    raise ValueError("No transformation to enum possible!")
        case "array":
            array_type_def = source_schema["definitions"]["root"]["items"]["type"]
            source_item_type = next(t for t in array_type_def if t != "null")
            target_items = target_schema["definitions"]["root"]["items"]
            counter = 0
            for target_item in target_items:
                target_item_nullable = "null" in target_item["type"]
                target_item_type = next(t for t in target_item["type"] if t != "null")
                if target_item_type == "boolean":
                    data[counter] = migrate_to_boolean(
                        data[counter], source_item_type, target_item_nullable
                    )
                elif target_item_type == "integer":
                    data[counter] = migrate_to_integer(
                        data[counter], source_item_type, target_item_nullable
                    )
                elif target_item_type == "number":
                    data[counter] = migrate_to_number(
                        data[counter], source_item_type, target_item_nullable
                    )
                elif target_item_type == "string":
                    # TODO: Correct passing of source schema
                    data[counter] = migrate_to_string(
                        data[counter],
                        source_item_type,
                        source_schema,
                        target_item_nullable,
                    )
                counter += 1
        case "tuple":
            source_items = source_schema["definitions"]["root"]["items"]
            target_items = target_schema["definitions"]["root"]["items"]
            counter = 0
            for source_item, target_item in zip(source_items, target_items):
                source_item_type = next(t for t in source_item["type"] if t != "null")
                target_item_nullable = "null" in target_item["type"]
                target_item_type = next(t for t in target_item["type"] if t != "null")
                if target_item_type == "boolean":
                    data[counter] = migrate_to_boolean(
                        data[counter], source_item_type, target_item_nullable
                    )
                elif target_item_type == "integer":
                    data[counter] = migrate_to_integer(
                        data[counter], source_item_type, target_item_nullable
                    )
                elif target_item_type == "number":
                    data[counter] = migrate_to_number(
                        data[counter], source_item_type, target_item_nullable
                    )
                elif target_item_type == "string":
                    # TODO: Correct passing of source schema
                    data[counter] = migrate_to_string(
                        data[counter],
                        source_item_type,
                        source_schema,
                        target_item_nullable,
                    )
                counter += 1
            for i in range(len(target_items), len(source_items)):
                data.pop(i)
            for i in range(len(source_items), len(target_items)):
                # TODO: Add default values?
                if "null" in target_items[i]["type"]:
                    data.append(None)
    return data

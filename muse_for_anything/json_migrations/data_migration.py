import numbers
from jsonschema import Draft7Validator
from muse_for_anything.json_migrations.jsonschema_matcher import extract_type


def migrate_data(data, source_schema, target_schema):
    """Data conforming to the source schema is migrated to the target schema if possible.

    Args:
        data: Data stored in a MUSE4Anything object, also holds root schemas for ref resolve
        source_schema (dict): The source JSONSchema
        target_schema (dict): The target JSONSchema

    Raises:
        ValueError: If transformation is not supported or possible to execute.

    Returns:
        If the update was successful, the updated data is returned
    """
    # TODO Add check with validator whether object satisfies schema
    # Maybe also outside of this method
    # validator = Draft7Validator(target_schema)
    if not isinstance(data, tuple):
        data = data, source_schema, target_schema
        source_schema = source_schema["definitions"]["root"]
        target_schema = target_schema["definitions"]["root"]

    target_type, target_nullable = extract_type(target_schema)
    if data[0] is None and target_nullable:
        return None
    source_type, source_nullable = extract_type(source_schema)
    updated_data = None
    try:
        # Call appropriate method depending on target schema main type
        if target_type == "array":
            # Array needs additional information on element type
            target_array_schema = target_schema["items"]
            updated_data = migrate_to_array(
                data, source_type, source_schema, target_array_schema
            )
        elif target_type == "boolean":
            updated_data = migrate_to_boolean(data, source_type)
        elif target_type == "enum":
            # Enum needs the allowed values
            allowed_values = target_schema["enum"]
            updated_data = migrate_to_enum(data, allowed_values)
        elif target_type == "integer":
            updated_data = migrate_to_integer(data, source_type)
        elif target_type == "number":
            updated_data = migrate_to_number(data, source_type)
        elif target_type == "string":
            updated_data = migrate_to_string(data, source_type, source_schema)
        elif target_type == "tuple":
            updated_data = migrate_to_tuple(
                data, source_type, source_schema, target_schema
            )
        elif target_type == "object":
            updated_data = migrate_to_object(
                data, source_type, source_schema, target_schema
            )
    except ValueError:
        # TODO: Change to raise error further to indicate that update unsuccessful!
        raise ValueError
    return updated_data


def migrate_to_number(data_object, source_type):
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
    data = data_object[0]
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
                else:
                    raise ValueError(
                        "No transformation from this object to number possible!"
                    )
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


def migrate_to_integer(data_object, source_type):
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
    data = data_object[0]
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
                else:
                    raise ValueError(
                        "No transformation from this object to integer possible!"
                    )
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


def migrate_to_string(data_object, source_type, source_schema):
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
    data = data_object[0]
    match source_type:
        case "array" | "boolean" | "enum" | "integer" | "number" | "string" | "tuple":
            try:
                data = str(data)
            except ValueError:
                raise ValueError("No transformation to string possible!")
        case "object":
            data_string = ""
            properties = source_schema["properties"]
            for property in properties.keys():
                data_string += property + ": " + str(data[property]) + ", "
            data = data_string[:-2]
    return data


def migrate_to_boolean(data_object, source_type):
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
    data = data_object[0]
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


def migrate_to_enum(data_object, allowed_values):
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
    data = data_object[0]
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


def migrate_to_array(data_object, source_type, source_schema, target_array_schema):
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
    data, root_schema, target_schema = data_object
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            data = [migrate_data(data_object, source_schema, target_array_schema)]
        case "array":
            source_array_schema = source_schema["items"]
            for i, element in enumerate(data):
                data_object = (element, root_schema, target_schema)
                data[i] = migrate_data(
                    data_object, source_array_schema, target_array_schema
                )
        case "tuple":
            source_items_types = source_schema["items"]
            for i, element in enumerate(zip(data, source_items_types)):
                data_object = (element[0], root_schema, target_schema)
                data[i] = migrate_data(data_object, element[1], target_array_schema)
    return data


def migrate_to_object(data_object, source_type, source_schema, target_object_schema):
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
    data, root_schema, target_schema = data_object
    target_properties = target_object_schema["properties"]
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            if len(target_properties) != 1:
                raise ValueError("No transformation to complex object possible!")
            prop_name = next(iter(target_properties))
            prop_type = target_properties[prop_name]
            data_object = (data, root_schema, target_schema)
            data = {prop_name: migrate_data(data_object, source_schema, prop_type)}
        case "object":
            source_properties = source_schema["properties"]
            common_properties = target_properties.keys() & source_properties.keys()
            new_properties = target_properties.keys() - source_properties.keys()
            deleted_properties = source_properties.keys() - target_properties.keys()
            for prop in common_properties:
                data_object = (data[prop], root_schema, target_schema)
                data[prop] = migrate_data(
                    data_object, source_properties[prop], target_properties[prop]
                )
            # One prop added, one deleted, likely name changes
            if len(new_properties) == 1 and len(deleted_properties) == 1:
                new_property = next(iter(new_properties))
                deleted_property = next(iter(deleted_properties))
                data_object = (data[deleted_property], root_schema, target_schema)
                data[new_property] = migrate_data(
                    data_object,
                    source_properties[deleted_property],
                    target_properties[new_property],
                )
                del data[deleted_property]
            # More than one added or deleted
            else:
                # Add all new properties
                for prop in new_properties:
                    # TODO: default values?
                    data_object = (None, root_schema, target_schema)
                    data[prop] = migrate_data(data_object, None, target_properties[prop])
                # Delete all old properties
                for prop in deleted_properties:
                    del data[prop]
    return data


def migrate_to_tuple(data_object, source_type, source_schema, target_tuple_schema):
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
    data, root_schema, target_schema = data_object
    target_items = target_tuple_schema["items"]
    match source_type:
        case "boolean" | "integer" | "number" | "string":
            if len(target_items) == 1:
                data = [migrate_data(data_object, source_schema, target_items[0])]
            else:
                raise ValueError("No transformation to enum possible!")
        case "array":
            source_array_schema = source_schema["items"]
            if len(data) != len(target_items):
                raise ValueError("No transformation from array to tuple possible!")
            for i, element in enumerate(data):
                data_object = (element, root_schema, target_schema)
                data[i] = migrate_data(data_object, source_array_schema, target_items[i])
        case "tuple":
            source_items = source_schema["items"]
            for i, (source_item, target_item) in enumerate(
                zip(source_items, target_items)
            ):
                data_object = (data[i], root_schema, target_schema)
                data[i] = migrate_data(data_object, source_item, target_item)
            for i in range(len(target_items), len(source_items)):
                data.pop(i)
            for i in range(len(source_items), len(target_items)):
                # TODO: default values?
                data_object = (None, root_schema, target_schema)
                data.append(migrate_data(data_object, None, target_items[i]))
    return data

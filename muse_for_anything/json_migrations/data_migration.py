from jsonschema import Draft7Validator


def migrate_object(data_object, target_schema, transformations):
    # validator = Draft7Validator(target_schema)
    for transformation in transformations:
        match transformation:
            case "Cast to number!":
                migrate_number(data_object)
            case "Cast to integer!":
                migrate_integer(data_object)
            case "Cast to string!":
                migrate_string(data_object)
    return data_object


def migrate_number(data_object):
    try:
        data_object["data"]["data"] = float(data_object["data"]["data"])
    except ValueError:
        raise ValueError("No transformation to number possible!")


def migrate_integer(data_object):
    try:
        data_object["data"]["data"] = int(float(data_object["data"]["data"]))
    except ValueError:
        raise ValueError("No transformation to integer possible!")


def migrate_string(data_object):
    try:
        data_object["data"]["data"] = str(data_object["data"]["data"])
    except ValueError:
        raise ValueError("No transformation to string possible!")

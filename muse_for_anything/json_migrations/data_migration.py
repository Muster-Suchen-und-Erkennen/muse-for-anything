from datetime import datetime, timezone
import json

from jsonschema import Draft7Validator


def migrate_object(data_object, target_schema, transformations):
    data_object = json.loads(data_object)
    # validator = Draft7Validator(target_schema)
    for transformation in transformations:
        match transformation:
            case "Cast to number!":
                try:
                    data_object["data"]["data"] = float(data_object["data"]["data"])
                except ValueError:
                    # print("Unable to cast \"", data_object['data']['data'], "\" to number!")
                    raise ValueError
            case "Cast to integer!":
                try:
                    data_object["data"]["data"] = int(float(data_object["data"]["data"]))
                except ValueError:
                    # print("Unable to cast \"", data_object['data']['data'], "\" to number!")
                    raise ValueError
            case "Cast to string!":
                try:
                    data_object["data"]["data"] = str(data_object["data"]["data"])
                except ValueError:
                    raise ValueError
    # print(datetime.now(timezone.utc))
    data_object["version"] = data_object["version"] + 1
    return data_object

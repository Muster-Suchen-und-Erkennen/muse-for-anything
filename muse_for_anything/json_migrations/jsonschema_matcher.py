import json
from pathlib import Path
import os


def load_schema(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def match_schema(source, target):
    transformations = []
    source = json.loads(source)
    target = json.loads(target)
    source_def = source["definitions"]["root"]
    target_def = target["definitions"]["root"]
    source_type = source_def["type"]
    target_type = target_def["type"]
    if source_type and target_type:
        if source_type == target_type:
            transformations.append("No type changes!")
        else:
            match target_type:
                case ["number"]:
                    if source_type in [["string"], ["integer"], ["boolean"]]:
                        transformations.append("Cast to number!")
                    else:
                        transformations.append("Unsupported transformation!")
                case ["integer"]:
                    if source_type in [["string"], ["number"], ["boolean"]]:
                        transformations.append("Cast to integer!")
                    else:
                        transformations.append("Unsupported transformation!")
                case ["string"]:
                    transformations.append("Cast to string!")
                case _:
                    transformations.append("Unsupported transformation!")
    return transformations

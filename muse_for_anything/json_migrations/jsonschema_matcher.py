from muse_for_anything.json_migrations.constants import *

def match_schema(source, target):
    transformations = []
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
                    if source_type in [["number"], ["string"], ["integer"], ["boolean"]]:
                        transformations.append(CAST_TO_NUMBER)
                    else:
                        transformations.append(CAST_TO_ERROR)
                case ["integer"]:
                    if source_type in  [["integer"], ["string"], ["number"], ["boolean"]]:
                        transformations.append(CAST_TO_INTEGER)
                    else:
                        transformations.append(CAST_TO_ERROR)
                case ["boolean"]:
                    if source_type in [["string"], ["integer"], ["boolean"]]:
                        transformations.append(CAST_TO_BOOLEAN)
                    else:
                        transformations.append(CAST_TO_ERROR)
                case ["string"]:
                    transformations.append(CAST_TO_STRING)
                case _:
                    transformations.append(CAST_TO_ERROR)
    return transformations

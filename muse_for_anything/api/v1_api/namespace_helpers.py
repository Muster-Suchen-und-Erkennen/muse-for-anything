from typing import Dict, Union


# TODO remove after refactor
def query_params_to_api_key(query_params: Dict[str, Union[str, int]]) -> Dict[str, str]:
    key = {}
    for k, v in query_params.items():
        key[f'?{k.replace("_", "-")}'] = str(v)
    return key

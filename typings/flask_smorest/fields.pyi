"""
This type stub file was generated by pyright.
"""

import marshmallow as ma

"""Custom marshmallow fields"""
class Upload(ma.fields.Field):
    """File upload field

    :param str format: File content encoding (binary, base64).
         Only relevant to OpenAPI 3. Only used for documentation purpose.
    """
    def __init__(self, format=..., **kwargs) -> None:
        ...
    



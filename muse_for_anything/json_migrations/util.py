# ==============================================================================
# MIT License
#
# Copyright (c) 2024 Jan Weber
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================


def extract_type(schema: dict):
    """Extract the type of a given schema and indicates
    whether or not elements are nullable

    Args:
        schema (dict): A JSON Schema saved as python dict

    Raises:
        ValueError: When schema does not include a known type definition

    Returns:
        string: Returns the main type of the schema
        (can be enum, schemaReference, resourceReference, object, array, tuple,
        boolean, integer, number, or string)
    """
    keys = schema.keys()
    nullable = False

    if "$ref" in keys:
        return "schemaReference", nullable

    if "enum" in keys:
        return "enum", nullable

    # Handling of other types
    if "type" in keys:
        type_entry = schema["type"]
        nullable = "null" in type_entry
        data_type = next((t for t in type_entry if t != "null"), None)

        if data_type == "object":
            return _extract_object_type(schema=schema), nullable

        if data_type == "array":
            return _extract_array_type(schema=schema), nullable
        return data_type, nullable

    else:
        raise ValueError("No type definition found!")


def _extract_object_type(schema: dict):
    """Since MUSE4Anything defines resource references and objects as objects
    of JSON Schema, it is necessary to check additional keywords as well.

    Args:
        schema (dict): Schema that defines an object

    Returns:
        str: Returns object type (can be object or resourceReference)
    """
    if "customType" in schema:
        if schema["customType"] == "resourceReference":
            return "resourceReference"
        else:
            raise ValueError("Unknown object type!")
    else:
        return "object"


def _extract_array_type(schema: dict):
    """Since MUSE4Anything defines tuples and arrays as arrays of JSON Schema,
    it is necessary to check additional keywords as well.

    Args:
        schema (dict): Schema that defines an array

    Returns:
        str: Returns array type (can be array or tuple)
    """
    if "arrayType" in schema:
        if schema["arrayType"] == "array":
            return "array"
        elif schema["arrayType"] == "tuple":
            return "tuple"
        else:
            raise ValueError("Unknown array type!")
    else:
        raise ValueError("No array type given!")

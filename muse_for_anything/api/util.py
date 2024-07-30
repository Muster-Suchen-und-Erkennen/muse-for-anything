"""Module containing utilities for flask smorest APIs."""

from typing import Any, Dict
from flask import url_for
from flask_smorest import Blueprint
from marshmallow_jsonschema import JSONSchema

from .jwt import JWTMixin


JSON_MIMETYPE = "application/json"
JSON_SCHEMA_MIMETYPE = "application/schema+json"


JSON_SCHEMA = JSONSchema()


def template_url_for(endpoint: str, key_args: Dict[str, str], **values) -> str:
    for key, key_variable in key_args.items():
        values[key] = f"{{{key_variable}}}"
    url: str = url_for(endpoint, **values)
    for key, key_variable in key_args.items():
        url = url.replace(f"%7B{key_variable}%7D", values[key])
    return url


class SecurityBlueprint(Blueprint, JWTMixin):
    """Blueprint that is aware of jwt tokens and how to document them.

    Use this Blueprint if you want to document security requirements for your api.
    """

    def __init__(self, *args: Any, **kwargs):
        super().__init__(*args, **kwargs)
        self._prepare_doc_cbks.append(self._prepare_security_doc)


def camelcase(s: str) -> str:
    """Turn a string from python snake_case into camelCase."""
    parts = iter(s.split("_"))
    return next(parts) + "".join(i.title() for i in parts)

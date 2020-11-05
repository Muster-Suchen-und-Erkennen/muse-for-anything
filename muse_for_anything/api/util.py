"""Module containing utilities for flask smorest APIs."""
from typing import Any
from .jwt import JWTMixin
from flask_smorest import Blueprint


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


"""Module containing utilities for flask smorest APIs."""

import importlib
import importlib.machinery
from sys import modules as sys_modules
from typing import Any, Dict

from flask import url_for
from flask_smorest import Blueprint

from .jwt import JWTMixin

JSON_MIMETYPE = "application/json"
JSON_SCHEMA_MIMETYPE = "application/schema+json"


# Monkey Patch JSONSchema to avoid Warnings ####################################
_fake_pkg_resources_spec = importlib.machinery.ModuleSpec("pkg_resources", None)
_fake_pkg_resources = importlib.util.module_from_spec(_fake_pkg_resources_spec)


# use a fake module to avoid using the deprecated module just to read the
# version number of the package...
def _fake_get_distribution(module: str):
    class distribution:
        def __init__(self, version: str = "") -> None:
            self.version = version

    if module == "marshmallow_jsonschema":
        return distribution("0.13.0")

    return distribution()


_fake_pkg_resources.get_distribution = _fake_get_distribution
sys_modules["pkg_resources"] = _fake_pkg_resources

from marshmallow_jsonschema import JSONSchema  # noqa:E402

del sys_modules["pkg_resources"]


# Use a proxy for marshmallow fields to avoid reading from deprecated attributes
class FieldProxy:
    def __init__(self, field) -> None:
        self.__field = field

    @property
    def __class__(self):
        return self.__field.__class__

    def __getattr__(self, attr: str) -> Any:
        if attr == "default":
            return self.__field.dump_default
        return getattr(self.__field, attr)

    def __instancecheck__(self, instance: Any) -> bool:
        return isinstance(self.__field, instance)


_old_get_schema_for_field = JSONSchema._get_schema_for_field


def _patched_get_schema_for_field(self, obj, field):
    return _old_get_schema_for_field(self, obj, FieldProxy(field))


JSONSchema._get_schema_for_field = _patched_get_schema_for_field
# End Monkey Patch #############################################################

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

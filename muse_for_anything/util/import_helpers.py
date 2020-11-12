import sys
from inspect import getmembers, getmodule, isclass
from typing import Any, Optional, Sequence, Type


def get_all_classes_of_module(
    module: str,
    base_class: Optional[Type[Any]] = None,
    ignore: Sequence[Type[Any]] = tuple(),
):
    """Get a set of classes defined in the specified module to include into __all__."""
    classes = set()
    resolved_module = sys.modules[module]
    for name, member in getmembers(resolved_module, isclass):
        if member in ignore:
            continue
        if getmodule(member) is not resolved_module:
            continue
        if not base_class or issubclass(member, base_class):
            classes.add(name)
    return classes

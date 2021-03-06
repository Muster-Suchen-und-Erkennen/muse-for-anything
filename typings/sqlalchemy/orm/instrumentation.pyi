"""
This type stub file was generated by pyright.
"""

from . import base
from .. import util

"""Defines SQLAlchemy's system of class instrumentation.

This module is usually not directly visible to user applications, but
defines a large part of the ORM's interactivity.

instrumentation.py deals with registration of end-user classes
for state tracking.   It interacts closely with state.py
and attributes.py which establish per-instance and per-class-attribute
instrumentation, respectively.

The class instrumentation system can be customized on a per-class
or global basis using the :mod:`sqlalchemy.ext.instrumentation`
module, which provides the means to build and specify
alternate instrumentation forms.

.. versionchanged: 0.8
   The instrumentation extension system was moved out of the
   ORM and into the external :mod:`sqlalchemy.ext.instrumentation`
   package.  When that package is imported, it installs
   itself within sqlalchemy.orm so that its more comprehensive
   resolution mechanics take effect.

"""
_memoized_key_collection = util.group_expirable_memoized_property()
class ClassManager(dict):
    """Tracks state information at the class level."""
    MANAGER_ATTR = ...
    STATE_ATTR = ...
    _state_setter = ...
    deferred_scalar_loader = ...
    original_init = ...
    factory = ...
    def __init__(self, class_) -> None:
        ...
    
    def __hash__(self) -> int:
        ...
    
    def __eq__(self, other) -> bool:
        ...
    
    @property
    def is_mapped(self):
        ...
    
    @util.memoized_property
    def mapper(self):
        ...
    
    def manage(self):
        """Mark this instance as the manager for its class."""
        ...
    
    def dispose(self):
        """Disassociate this manager from its class."""
        ...
    
    @util.hybridmethod
    def manager_getter(self):
        ...
    
    @util.hybridmethod
    def state_getter(self):
        """Return a (instance) -> InstanceState callable.

        "state getter" callables should raise either KeyError or
        AttributeError if no InstanceState could be found for the
        instance.
        """
        ...
    
    @util.hybridmethod
    def dict_getter(self):
        ...
    
    def instrument_attribute(self, key, inst, propagated=...):
        ...
    
    def subclass_managers(self, recursive):
        ...
    
    def post_configure_attribute(self, key):
        ...
    
    def uninstrument_attribute(self, key, propagated=...):
        ...
    
    def unregister(self):
        """remove all instrumentation established by this ClassManager."""
        ...
    
    def install_descriptor(self, key, inst):
        ...
    
    def uninstall_descriptor(self, key):
        ...
    
    def install_member(self, key, implementation):
        ...
    
    def uninstall_member(self, key):
        ...
    
    def instrument_collection_class(self, key, collection_class):
        ...
    
    def initialize_collection(self, key, state, factory):
        ...
    
    def is_instrumented(self, key, search=...):
        ...
    
    def get_impl(self, key):
        ...
    
    @property
    def attributes(self):
        ...
    
    def new_instance(self, state=...):
        ...
    
    def setup_instance(self, instance, state=...):
        ...
    
    def teardown_instance(self, instance):
        ...
    
    def has_state(self, instance):
        ...
    
    def has_parent(self, state, key, optimistic=...):
        """TODO"""
        ...
    
    def __bool__(self):
        """All ClassManagers are non-zero regardless of attribute state."""
        ...
    
    __nonzero__ = ...
    def __repr__(self):
        ...
    


class _SerializeManager(object):
    """Provide serialization of a :class:`.ClassManager`.

    The :class:`.InstanceState` uses ``__init__()`` on serialize
    and ``__call__()`` on deserialize.

    """
    def __init__(self, state, d) -> None:
        ...
    
    def __call__(self, state, inst, state_dict):
        ...
    


class InstrumentationFactory(object):
    """Factory for new ClassManager instances."""
    def create_manager_for_cls(self, class_):
        ...
    
    def unregister(self, class_):
        ...
    


_instrumentation_factory = InstrumentationFactory()
instance_state = _default_state_getter = base.instance_state
instance_dict = _default_dict_getter = base.instance_dict
manager_of_class = _default_manager_getter = base.manager_of_class
def register_class(class_):
    """Register class instrumentation.

    Returns the existing or newly created class manager.

    """
    ...

def unregister_class(class_):
    """Unregister class instrumentation."""
    ...

def is_instrumented(instance, key):
    """Return True if the given attribute on the given instance is
    instrumented by the attributes package.

    This function may be used regardless of instrumentation
    applied directly to the class, i.e. no descriptors are required.

    """
    ...


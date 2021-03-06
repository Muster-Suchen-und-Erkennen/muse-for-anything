"""
This type stub file was generated by pyright.
"""

from .. import util

"""private module containing functions used to convert database
rows into object instances and associated state.

the functions here are called primarily by Query, Mapper,
as well as some of the attribute loading strategies.

"""
_new_runid = util.counter()
def instances(query, cursor, context):
    """Return an ORM result as an iterator."""
    ...

@util.dependencies("sqlalchemy.orm.query")
def merge_result(querylib, query, iterator, load=...):
    """Merge a result into this :class:`_query.Query` object's Session."""
    ...

def get_from_identity(session, mapper, key, passive):
    """Look up the given key in the given session's identity map,
    check the object for expired state if found.

    """
    ...

def load_on_ident(query, key, refresh_state=..., with_for_update=..., only_load_props=...):
    """Load the given identity key from the database."""
    ...

def load_on_pk_identity(query, primary_key_identity, refresh_state=..., with_for_update=..., only_load_props=..., identity_token=...):
    """Load the given primary key identity from the database."""
    ...

class PostLoad(object):
    """Track loaders and states for "post load" operations."""
    __slots__ = ...
    def __init__(self) -> None:
        ...
    
    def add_state(self, state, overwrite):
        ...
    
    def invoke(self, context, path):
        ...
    
    @classmethod
    def for_context(cls, context, path, only_load_props):
        ...
    
    @classmethod
    def path_exists(self, context, path, key):
        ...
    
    @classmethod
    def callable_for_path(cls, context, path, limit_to_mapper, token, loader_callable, *arg, **kw):
        ...
    


def load_scalar_attributes(mapper, state, attribute_names):
    """initiate a column-based attribute refresh operation."""
    ...


"""
This type stub file was generated by pyright.
"""

from . import base
from .. import util

"""Provides a thread-local transactional wrapper around the root Engine class.

The ``threadlocal`` module is invoked when using the
``strategy="threadlocal"`` flag with :func:`~sqlalchemy.engine.create_engine`.
This module is semi-private and is invoked automatically when the threadlocal
engine strategy is used.
"""
class TLConnection(base.Connection):
    def __init__(self, *arg, **kw) -> None:
        ...
    
    def close(self):
        ...
    


class TLEngine(base.Engine):
    """An Engine that includes support for thread-local managed
    transactions.

    """
    _tl_connection_cls = ...
    @util.deprecated("1.3", "The 'threadlocal' engine strategy is deprecated, and will be " "removed in a future release.  The strategy is no longer relevant " "to modern usage patterns (including that of the ORM " ":class:`.Session` object) which make use of a " ":class:`_engine.Connection` " "object in order to invoke statements.")
    def __init__(self, *args, **kwargs) -> None:
        ...
    
    def contextual_connect(self, **kw):
        ...
    
    def begin_twophase(self, xid=...):
        ...
    
    def begin_nested(self):
        ...
    
    def begin(self):
        ...
    
    def __enter__(self):
        ...
    
    def __exit__(self, type_, value, traceback):
        ...
    
    def prepare(self):
        ...
    
    def commit(self):
        ...
    
    def rollback(self):
        ...
    
    def dispose(self):
        ...
    
    @property
    def closed(self):
        ...
    
    def close(self):
        ...
    
    def __repr__(self):
        ...
    



"""
This type stub file was generated by pyright.
"""

from .types import _StringType
from ...sql import sqltypes

class _EnumeratedValues(_StringType):
    ...


class ENUM(sqltypes.NativeForEmulated, sqltypes.Enum, _EnumeratedValues):
    """MySQL ENUM type."""
    __visit_name__ = ...
    native_enum = ...
    def __init__(self, *enums, **kw) -> None:
        """Construct an ENUM.

        E.g.::

          Column('myenum', ENUM("foo", "bar", "baz"))

        :param enums: The range of valid values for this ENUM.  Values will be
          quoted when generating the schema according to the quoting flag (see
          below).  This object may also be a PEP-435-compliant enumerated
          type.

          .. versionadded: 1.1 added support for PEP-435-compliant enumerated
             types.

        :param strict: This flag has no effect.

         .. versionchanged:: The MySQL ENUM type as well as the base Enum
            type now validates all Python data values.

        :param charset: Optional, a column-level character set for this string
          value.  Takes precedence to 'ascii' or 'unicode' short-hand.

        :param collation: Optional, a column-level collation for this string
          value.  Takes precedence to 'binary' short-hand.

        :param ascii: Defaults to False: short-hand for the ``latin1``
          character set, generates ASCII in schema.

        :param unicode: Defaults to False: short-hand for the ``ucs2``
          character set, generates UNICODE in schema.

        :param binary: Defaults to False: short-hand, pick the binary
          collation type that matches the column's character set.  Generates
          BINARY in schema.  This does not affect the type of data stored,
          only the collation of character data.

        :param quoting: Defaults to 'auto': automatically determine enum value
          quoting.  If all enum values are surrounded by the same quoting
          character, then use 'quoted' mode.  Otherwise, use 'unquoted' mode.

          'quoted': values in enums are already quoted, they will be used
          directly when generating the schema - this usage is deprecated.

          'unquoted': values in enums are not quoted, they will be escaped and
          surrounded by single quotes when generating the schema.

          Previous versions of this type always required manually quoted
          values to be supplied; future versions will always quote the string
          literals for you.  This is a transitional option.

        """
        ...
    
    @classmethod
    def adapt_emulated_to_native(cls, impl, **kw):
        """Produce a MySQL native :class:`.mysql.ENUM` from plain
        :class:`.Enum`.

        """
        ...
    
    def __repr__(self):
        ...
    


class SET(_EnumeratedValues):
    """MySQL SET type."""
    __visit_name__ = ...
    def __init__(self, *values, **kw) -> None:
        """Construct a SET.

        E.g.::

          Column('myset', SET("foo", "bar", "baz"))


        The list of potential values is required in the case that this
        set will be used to generate DDL for a table, or if the
        :paramref:`.SET.retrieve_as_bitwise` flag is set to True.

        :param values: The range of valid values for this SET.

        :param convert_unicode: Same flag as that of
         :paramref:`.String.convert_unicode`.

        :param collation: same as that of :paramref:`.String.collation`

        :param charset: same as that of :paramref:`.VARCHAR.charset`.

        :param ascii: same as that of :paramref:`.VARCHAR.ascii`.

        :param unicode: same as that of :paramref:`.VARCHAR.unicode`.

        :param binary: same as that of :paramref:`.VARCHAR.binary`.

        :param quoting: Defaults to 'auto': automatically determine set value
          quoting.  If all values are surrounded by the same quoting
          character, then use 'quoted' mode.  Otherwise, use 'unquoted' mode.

          'quoted': values in enums are already quoted, they will be used
          directly when generating the schema - this usage is deprecated.

          'unquoted': values in enums are not quoted, they will be escaped and
          surrounded by single quotes when generating the schema.

          Previous versions of this type always required manually quoted
          values to be supplied; future versions will always quote the string
          literals for you.  This is a transitional option.

          .. versionadded:: 0.9.0

        :param retrieve_as_bitwise: if True, the data for the set type will be
          persisted and selected using an integer value, where a set is coerced
          into a bitwise mask for persistence.  MySQL allows this mode which
          has the advantage of being able to store values unambiguously,
          such as the blank string ``''``.   The datatype will appear
          as the expression ``col + 0`` in a SELECT statement, so that the
          value is coerced into an integer value in result sets.
          This flag is required if one wishes
          to persist a set that can store the blank string ``''`` as a value.

          .. warning::

            When using :paramref:`.mysql.SET.retrieve_as_bitwise`, it is
            essential that the list of set values is expressed in the
            **exact same order** as exists on the MySQL database.

          .. versionadded:: 1.0.0


        """
        ...
    
    def column_expression(self, colexpr):
        ...
    
    def result_processor(self, dialect, coltype):
        ...
    
    def bind_processor(self, dialect):
        ...
    
    def adapt(self, impltype, **kw):
        ...
    



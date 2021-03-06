"""
This type stub file was generated by pyright.
"""

from . import base as oracle
from .base import OracleCompiler, OracleDialect, OracleExecutionContext
from ... import types as sqltypes, util
from ...engine import result as _result

r"""
.. dialect:: oracle+cx_oracle
    :name: cx-Oracle
    :dbapi: cx_oracle
    :connectstring: oracle+cx_oracle://user:pass@host:port/dbname[?key=value&key=value...]
    :url: https://oracle.github.io/python-cx_Oracle/

DSN vs. Hostname connections
-----------------------------

The dialect will connect to a DSN if no database name portion is presented,
such as::

    engine = create_engine("oracle+cx_oracle://scott:tiger@oracle1120/?encoding=UTF-8&nencoding=UTF-8")

Above, ``oracle1120`` is passed to cx_Oracle as an Oracle datasource name.

Alternatively, if a database name is present, the ``cx_Oracle.makedsn()``
function is used to create an ad-hoc "datasource" name assuming host
and port::

    engine = create_engine("oracle+cx_oracle://scott:tiger@hostname:1521/dbname?encoding=UTF-8&nencoding=UTF-8")

Above, the DSN would be created as follows::

    >>> import cx_Oracle
    >>> cx_Oracle.makedsn("hostname", 1521, sid="dbname")
    '(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=hostname)(PORT=1521))(CONNECT_DATA=(SID=dbname)))'

The ``service_name`` parameter, also consumed by ``cx_Oracle.makedsn()``, may
be specified in the URL query string, e.g. ``?service_name=my_service``.


Passing cx_Oracle connect arguments
-----------------------------------

Additional connection arguments can usually be passed via the URL
query string; particular symbols like ``cx_Oracle.SYSDBA`` are intercepted
and converted to the correct symbol::

    e = create_engine(
        "oracle+cx_oracle://user:pass@dsn?encoding=UTF-8&nencoding=UTF-8&mode=SYSDBA&events=true")

.. versionchanged:: 1.3 the cx_oracle dialect now accepts all argument names
   within the URL string itself, to be passed to the cx_Oracle DBAPI.   As
   was the case earlier but not correctly documented, the
   :paramref:`_sa.create_engine.connect_args` parameter also accepts all
   cx_Oracle DBAPI connect arguments.

To pass arguments directly to ``.connect()`` wihtout using the query
string, use the :paramref:`_sa.create_engine.connect_args` dictionary.
Any cx_Oracle parameter value and/or constant may be passed, such as::

    import cx_Oracle
    e = create_engine(
        "oracle+cx_oracle://user:pass@dsn",
        connect_args={
            "encoding": "UTF-8",
            "nencoding": "UTF-8",
            "mode": cx_Oracle.SYSDBA,
            "events": True
        }
    )

Options consumed by the SQLAlchemy cx_Oracle dialect outside of the driver
--------------------------------------------------------------------------

There are also options that are consumed by the SQLAlchemy cx_oracle dialect
itself.  These options are always passed directly to :func:`_sa.create_engine`
, such as::

    e = create_engine(
        "oracle+cx_oracle://user:pass@dsn", coerce_to_unicode=False)

The parameters accepted by the cx_oracle dialect are as follows:

* ``arraysize`` - set the cx_oracle.arraysize value on cursors, defaulted
  to 50.  This setting is significant with cx_Oracle as the contents of LOB
  objects are only readable within a "live" row (e.g. within a batch of
  50 rows).

* ``auto_convert_lobs`` - defaults to True; See :ref:`cx_oracle_lob`.

* ``coerce_to_unicode`` - see :ref:`cx_oracle_unicode` for detail.

* ``coerce_to_decimal`` - see :ref:`cx_oracle_numeric` for detail.

* ``encoding_errors`` - see :ref:`cx_oracle_unicode_encoding_errors` for detail.

.. _cx_oracle_unicode:

Unicode
-------

As is the case for all DBAPIs under Python 3, all strings are inherently
Unicode strings.     Under Python 2, cx_Oracle also supports Python Unicode
objects directly.    In all cases however, the driver requires an explicit
encoding configuration.

Ensuring the Correct Client Encoding
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The long accepted standard for establishing client encoding for nearly all
Oracle related software is via the `NLS_LANG <https://www.oracle.com/database/technologies/faq-nls-lang.html>`_
environment variable.   cx_Oracle like most other Oracle drivers will use
this environment variable as the source of its encoding configuration.  The
format of this variable is idiosyncratic; a typical value would be
``AMERICAN_AMERICA.AL32UTF8``.

The cx_Oracle driver also supports a programmatic alternative which is to
pass the ``encoding`` and ``nencoding`` parameters directly to its
``.connect()`` function.  These can be present in the URL as follows::

    engine = create_engine("oracle+cx_oracle://scott:tiger@oracle1120/?encoding=UTF-8&nencoding=UTF-8")

For the meaning of the ``encoding`` and ``nencoding`` parameters, please
consult
`Characters Sets and National Language Support (NLS) <https://cx-oracle.readthedocs.io/en/latest/user_guide/globalization.html#globalization>`_.

.. seealso::

    `Characters Sets and National Language Support (NLS) <https://cx-oracle.readthedocs.io/en/latest/user_guide/globalization.html#globalization>`_
    - in the cx_Oracle documentation.


Unicode-specific Column datatypes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Core expression language handles unicode data by use of the :class:`.Unicode`
and :class:`.UnicodeText`
datatypes.  These types correspond to the  VARCHAR2 and CLOB Oracle datatypes by
default.   When using these datatypes with Unicode data, it is expected that
the Oracle database is configured with a Unicode-aware character set, as well
as that the ``NLS_LANG`` environment variable is set appropriately, so that
the VARCHAR2 and CLOB datatypes can accommodate the data.

In the case that the Oracle database is not configured with a Unicode character
set, the two options are to use the :class:`_types.NCHAR` and
:class:`_oracle.NCLOB` datatypes explicitly, or to pass the flag
``use_nchar_for_unicode=True`` to :func:`_sa.create_engine`,
which will cause the
SQLAlchemy dialect to use NCHAR/NCLOB for the :class:`.Unicode` /
:class:`.UnicodeText` datatypes instead of VARCHAR/CLOB.

.. versionchanged:: 1.3  The :class:`.Unicode` and :class:`.UnicodeText`
   datatypes now correspond to the ``VARCHAR2`` and ``CLOB`` Oracle datatypes
   unless the ``use_nchar_for_unicode=True`` is passed to the dialect
   when :func:`_sa.create_engine` is called.

Unicode Coercion of result rows under Python 2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When result sets are fetched that include strings, under Python 3 the cx_Oracle
DBAPI returns all strings as Python Unicode objects, since Python 3 only has a
Unicode string type.  This occurs for data fetched from datatypes such as
VARCHAR2, CHAR, CLOB, NCHAR, NCLOB, etc.  In order to provide cross-
compatibility under Python 2, the SQLAlchemy cx_Oracle dialect will add
Unicode-conversion to string data under Python 2 as well.  Historically, this
made use of converters that were supplied by cx_Oracle but were found to be
non-performant; SQLAlchemy's own converters are used for the string to Unicode
conversion under Python 2.  To disable the Python 2 Unicode conversion for
VARCHAR2, CHAR, and CLOB, the flag ``coerce_to_unicode=False`` can be passed to
:func:`_sa.create_engine`.

.. versionchanged:: 1.3 Unicode conversion is applied to all string values
   by default under python 2.  The ``coerce_to_unicode`` now defaults to True
   and can be set to False to disable the Unicode coercion of strings that are
   delivered as VARCHAR2/CHAR/CLOB data.

.. _cx_oracle_unicode_encoding_errors:

Encoding Errors
^^^^^^^^^^^^^^^

For the unusual case that data in the Oracle database is present with a broken
encoding, the dialect accepts a parameter ``encoding_errors`` which will be
passed to Unicode decoding functions in order to affect how decoding errors are
handled.  The value is ultimately consumed by the Python `decode
<https://docs.python.org/3/library/stdtypes.html#bytes.decode>`_ function, and
is passed both via cx_Oracle's ``encodingErrors`` parameter consumed by
``Cursor.var()``, as well as SQLAlchemy's own decoding function, as the
cx_Oracle dialect makes use of both under different circumstances.

.. versionadded:: 1.3.11


.. _cx_oracle_setinputsizes:

Fine grained control over cx_Oracle data binding performance with setinputsizes
-------------------------------------------------------------------------------

The cx_Oracle DBAPI has a deep and fundamental reliance upon the usage of the
DBAPI ``setinputsizes()`` call.   The purpose of this call is to establish the
datatypes that are bound to a SQL statement for Python values being passed as
parameters.  While virtually no other DBAPI assigns any use to the
``setinputsizes()`` call, the cx_Oracle DBAPI relies upon it heavily in its
interactions with the Oracle client interface, and in some scenarios it is  not
possible for SQLAlchemy to know exactly how data should be bound, as some
settings can cause profoundly different performance characteristics, while
altering the type coercion behavior at the same time.

Users of the cx_Oracle dialect are **strongly encouraged** to read through
cx_Oracle's list of built-in datatype symbols at
http://cx-oracle.readthedocs.io/en/latest/module.html#types.
Note that in some cases, significant performance degradation can occur when
using these types vs. not, in particular when specifying ``cx_Oracle.CLOB``.

On the SQLAlchemy side, the :meth:`.DialectEvents.do_setinputsizes` event can
be used both for runtime visibility (e.g. logging) of the setinputsizes step as
well as to fully control how ``setinputsizes()`` is used on a per-statement
basis.

.. versionadded:: 1.2.9 Added :meth:`.DialectEvents.setinputsizes`


Example 1 - logging all setinputsizes calls
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following example illustrates how to log the intermediary values from a
SQLAlchemy perspective before they are converted to the raw ``setinputsizes()``
parameter dictionary.  The keys of the dictionary are :class:`.BindParameter`
objects which have a ``.key`` and a ``.type`` attribute::

    from sqlalchemy import create_engine, event

    engine = create_engine("oracle+cx_oracle://scott:tiger@host/xe")

    @event.listens_for(engine, "do_setinputsizes")
    def _log_setinputsizes(inputsizes, cursor, statement, parameters, context):
        for bindparam, dbapitype in inputsizes.items():
                log.info(
                    "Bound parameter name: %s  SQLAlchemy type: %r  "
                    "DBAPI object: %s",
                    bindparam.key, bindparam.type, dbapitype)

Example 2 - remove all bindings to CLOB
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``CLOB`` datatype in cx_Oracle incurs a significant performance overhead,
however is set by default for the ``Text`` type within the SQLAlchemy 1.2
series.   This setting can be modified as follows::

    from sqlalchemy import create_engine, event
    from cx_Oracle import CLOB

    engine = create_engine("oracle+cx_oracle://scott:tiger@host/xe")

    @event.listens_for(engine, "do_setinputsizes")
    def _remove_clob(inputsizes, cursor, statement, parameters, context):
        for bindparam, dbapitype in list(inputsizes.items()):
            if dbapitype is CLOB:
                del inputsizes[bindparam]

.. _cx_oracle_returning:

RETURNING Support
-----------------

The cx_Oracle dialect implements RETURNING using OUT parameters.
The dialect supports RETURNING fully, however cx_Oracle 6 is recommended
for complete support.

.. _cx_oracle_lob:

LOB Objects
-----------

cx_oracle returns oracle LOBs using the cx_oracle.LOB object.  SQLAlchemy
converts these to strings so that the interface of the Binary type is
consistent with that of other backends, which takes place within a cx_Oracle
outputtypehandler.

cx_Oracle prior to version 6 would require that LOB objects be read before
a new batch of rows would be read, as determined by the ``cursor.arraysize``.
As of the 6 series, this limitation has been lifted.  Nevertheless, because
SQLAlchemy pre-reads these LOBs up front, this issue is avoided in any case.

To disable the auto "read()" feature of the dialect, the flag
``auto_convert_lobs=False`` may be passed to :func:`_sa.create_engine`.  Under
the cx_Oracle 5 series, having this flag turned off means there is the chance
of reading from a stale LOB object if not read as it is fetched.   With
cx_Oracle 6, this issue is resolved.

.. versionchanged:: 1.2  the LOB handling system has been greatly simplified
   internally to make use of outputtypehandlers, and no longer makes use
   of alternate "buffered" result set objects.

Two Phase Transactions Not Supported
-------------------------------------

Two phase transactions are **not supported** under cx_Oracle due to poor
driver support.   As of cx_Oracle 6.0b1, the interface for
two phase transactions has been changed to be more of a direct pass-through
to the underlying OCI layer with less automation.  The additional logic
to support this system is not implemented in SQLAlchemy.

.. _cx_oracle_numeric:

Precision Numerics
------------------

SQLAlchemy's numeric types can handle receiving and returning values as Python
``Decimal`` objects or float objects.  When a :class:`.Numeric` object, or a
subclass such as :class:`.Float`, :class:`_oracle.DOUBLE_PRECISION` etc. is in
use, the :paramref:`.Numeric.asdecimal` flag determines if values should be
coerced to ``Decimal`` upon return, or returned as float objects.   To make
matters more complicated under Oracle, Oracle's ``NUMBER`` type can also
represent integer values if the "scale" is zero, so the Oracle-specific
:class:`_oracle.NUMBER` type takes this into account as well.

The cx_Oracle dialect makes extensive use of connection- and cursor-level
"outputtypehandler" callables in order to coerce numeric values as requested.
These callables are specific to the specific flavor of :class:`.Numeric` in
use, as well as if no SQLAlchemy typing objects are present.   There are
observed scenarios where Oracle may sends incomplete or ambiguous information
about the numeric types being returned, such as a query where the numeric types
are buried under multiple levels of subquery.  The type handlers do their best
to make the right decision in all cases, deferring to the underlying cx_Oracle
DBAPI for all those cases where the driver can make the best decision.

When no typing objects are present, as when executing plain SQL strings, a
default "outputtypehandler" is present which will generally return numeric
values which specify precision and scale as Python ``Decimal`` objects.  To
disable this coercion to decimal for performance reasons, pass the flag
``coerce_to_decimal=False`` to :func:`_sa.create_engine`::

    engine = create_engine("oracle+cx_oracle://dsn", coerce_to_decimal=False)

The ``coerce_to_decimal`` flag only impacts the results of plain string
SQL staements that are not otherwise associated with a :class:`.Numeric`
SQLAlchemy type (or a subclass of such).

.. versionchanged:: 1.2  The numeric handling system for cx_Oracle has been
   reworked to take advantage of newer cx_Oracle features as well
   as better integration of outputtypehandlers.

"""
class _OracleInteger(sqltypes.Integer):
    def get_dbapi_type(self, dbapi):
        ...
    


class _OracleNumeric(sqltypes.Numeric):
    is_number = ...
    def bind_processor(self, dialect):
        ...
    
    def result_processor(self, dialect, coltype):
        ...
    


class _OracleBinaryFloat(_OracleNumeric):
    def get_dbapi_type(self, dbapi):
        ...
    


class _OracleBINARY_FLOAT(_OracleBinaryFloat, oracle.BINARY_FLOAT):
    ...


class _OracleBINARY_DOUBLE(_OracleBinaryFloat, oracle.BINARY_DOUBLE):
    ...


class _OracleNUMBER(_OracleNumeric):
    is_number = ...


class _OracleDate(sqltypes.Date):
    def bind_processor(self, dialect):
        ...
    
    def result_processor(self, dialect, coltype):
        ...
    


class _OracleChar(sqltypes.CHAR):
    def get_dbapi_type(self, dbapi):
        ...
    


class _OracleNChar(sqltypes.NCHAR):
    def get_dbapi_type(self, dbapi):
        ...
    


class _OracleUnicodeStringNCHAR(oracle.NVARCHAR2):
    def get_dbapi_type(self, dbapi):
        ...
    


class _OracleUnicodeStringCHAR(sqltypes.Unicode):
    def get_dbapi_type(self, dbapi):
        ...
    


class _OracleUnicodeTextNCLOB(oracle.NCLOB):
    def get_dbapi_type(self, dbapi):
        ...
    


class _OracleUnicodeTextCLOB(sqltypes.UnicodeText):
    def get_dbapi_type(self, dbapi):
        ...
    


class _OracleText(sqltypes.Text):
    def get_dbapi_type(self, dbapi):
        ...
    


class _OracleLong(oracle.LONG):
    def get_dbapi_type(self, dbapi):
        ...
    


class _OracleString(sqltypes.String):
    ...


class _OracleEnum(sqltypes.Enum):
    def bind_processor(self, dialect):
        ...
    


class _OracleBinary(sqltypes.LargeBinary):
    def get_dbapi_type(self, dbapi):
        ...
    
    def bind_processor(self, dialect):
        ...
    
    def result_processor(self, dialect, coltype):
        ...
    


class _OracleInterval(oracle.INTERVAL):
    def get_dbapi_type(self, dbapi):
        ...
    


class _OracleRaw(oracle.RAW):
    ...


class _OracleRowid(oracle.ROWID):
    def get_dbapi_type(self, dbapi):
        ...
    


class OracleCompiler_cx_oracle(OracleCompiler):
    _oracle_cx_sql_compiler = ...
    def bindparam_string(self, name, **kw):
        ...
    


class OracleExecutionContext_cx_oracle(OracleExecutionContext):
    out_parameters = ...
    def pre_exec(self):
        ...
    
    def create_cursor(self):
        ...
    
    def get_result_proxy(self):
        ...
    


class ReturningResultProxy(_result.FullyBufferedResultProxy):
    """Result proxy which stuffs the _returning clause + outparams
    into the fetch."""
    def __init__(self, context, returning_params) -> None:
        ...
    


class OracleDialect_cx_oracle(OracleDialect):
    execution_ctx_cls = ...
    statement_compiler = ...
    supports_sane_rowcount = ...
    supports_sane_multi_rowcount = ...
    supports_unicode_statements = ...
    supports_unicode_binds = ...
    driver = ...
    colspecs = ...
    execute_sequence_format = ...
    _cx_oracle_threaded = ...
    @util.deprecated_params(threaded=("1.3", "The 'threaded' parameter to the cx_oracle dialect " "is deprecated as a dialect-level argument, and will be removed " "in a future release.  As of version 1.3, it defaults to False " "rather than True.  The 'threaded' option can be passed to " "cx_Oracle directly in the URL query string passed to " ":func:`_sa.create_engine`."))
    def __init__(self, auto_convert_lobs=..., coerce_to_unicode=..., coerce_to_decimal=..., arraysize=..., encoding_errors=..., threaded=..., **kwargs) -> None:
        ...
    
    @classmethod
    def dbapi(cls):
        ...
    
    def initialize(self, connection):
        ...
    
    _to_decimal = ...
    def on_connect(self):
        ...
    
    def create_connect_args(self, url):
        ...
    
    def is_disconnect(self, e, connection, cursor):
        ...
    
    @util.deprecated("1.2", "The create_xid() method of the cx_Oracle dialect is deprecated and " "will be removed in a future release.  " "Two-phase transaction support is no longer functional " "in SQLAlchemy's cx_Oracle dialect as of cx_Oracle 6.0b1, which no " "longer supports the API that SQLAlchemy relied upon.")
    def create_xid(self):
        """create a two-phase transaction ID.

        this id will be passed to do_begin_twophase(), do_rollback_twophase(),
        do_commit_twophase().  its format is unspecified.

        """
        ...
    
    def do_executemany(self, cursor, statement, parameters, context=...):
        ...
    
    def do_begin_twophase(self, connection, xid):
        ...
    
    def do_prepare_twophase(self, connection, xid):
        ...
    
    def do_rollback_twophase(self, connection, xid, is_prepared=..., recover=...):
        ...
    
    def do_commit_twophase(self, connection, xid, is_prepared=..., recover=...):
        ...
    
    def do_recover_twophase(self, connection):
        ...
    
    def set_isolation_level(self, connection, level):
        ...
    


dialect = OracleDialect_cx_oracle

"""
This type stub file was generated by pyright.
"""

import logging
from .base import ENUM, PGCompiler, PGDialect, PGExecutionContext, PGIdentifierPreparer, UUID
from .hstore import HSTORE
from .json import JSON, JSONB
from ... import types as sqltypes, util

r"""
.. dialect:: postgresql+psycopg2
    :name: psycopg2
    :dbapi: psycopg2
    :connectstring: postgresql+psycopg2://user:password@host:port/dbname[?key=value&key=value...]
    :url: http://pypi.python.org/pypi/psycopg2/

psycopg2 Connect Arguments
-----------------------------------

psycopg2-specific keyword arguments which are accepted by
:func:`_sa.create_engine()` are:

* ``server_side_cursors``: Enable the usage of "server side cursors" for SQL
  statements which support this feature. What this essentially means from a
  psycopg2 point of view is that the cursor is created using a name, e.g.
  ``connection.cursor('some name')``, which has the effect that result rows
  are not immediately pre-fetched and buffered after statement execution, but
  are instead left on the server and only retrieved as needed. SQLAlchemy's
  :class:`~sqlalchemy.engine.ResultProxy` uses special row-buffering
  behavior when this feature is enabled, such that groups of 100 rows at a
  time are fetched over the wire to reduce conversational overhead.
  Note that the :paramref:`.Connection.execution_options.stream_results`
  execution option is a more targeted
  way of enabling this mode on a per-execution basis.

* ``use_native_unicode``: Enable the usage of Psycopg2 "native unicode" mode
  per connection.  True by default.

  .. seealso::

    :ref:`psycopg2_disable_native_unicode`

* ``isolation_level``: This option, available for all PostgreSQL dialects,
  includes the ``AUTOCOMMIT`` isolation level when using the psycopg2
  dialect.

  .. seealso::

    :ref:`psycopg2_isolation_level`

* ``client_encoding``: sets the client encoding in a libpq-agnostic way,
  using psycopg2's ``set_client_encoding()`` method.

  .. seealso::

    :ref:`psycopg2_unicode`

* ``executemany_mode``, ``executemany_batch_page_size``,
  ``executemany_values_page_size``: Allows use of psycopg2
  extensions for optimizing "executemany"-stye queries.  See the referenced
  section below for details.

  .. seealso::

    :ref:`psycopg2_executemany_mode`

* ``use_batch_mode``: this is the previous setting used to affect "executemany"
  mode and is now deprecated.


Unix Domain Connections
------------------------

psycopg2 supports connecting via Unix domain connections.   When the ``host``
portion of the URL is omitted, SQLAlchemy passes ``None`` to psycopg2,
which specifies Unix-domain communication rather than TCP/IP communication::

    create_engine("postgresql+psycopg2://user:password@/dbname")

By default, the socket file used is to connect to a Unix-domain socket
in ``/tmp``, or whatever socket directory was specified when PostgreSQL
was built.  This value can be overridden by passing a pathname to psycopg2,
using ``host`` as an additional keyword argument::

    create_engine("postgresql+psycopg2://user:password@/dbname?host=/var/lib/postgresql")

.. seealso::

    `PQconnectdbParams \
    <http://www.postgresql.org/docs/9.1/static/libpq-connect.html#LIBPQ-PQCONNECTDBPARAMS>`_

.. _psycopg2_multi_host:

Specfiying multiple fallback hosts
------------------------------------

psycopg2 supports multiple connection points in the connection string.
When the ``host`` parameter is used multiple times in the query section of
the URL, SQLAlchemy will create a single string of the host and port
information provided to make the connections::

    create_engine(
        "postgresql+psycopg2://user:password@/dbname?host=HostA:port1&host=HostB&host=HostC"
    )

A connection to each host is then attempted until either a connection is successful
or all connections are unsuccessful in which case an error is raised.

.. versionadded:: 1.3.20 Support for multiple hosts in PostgreSQL connection
   string.

.. seealso::

    `PQConnString \
    <https://www.postgresql.org/docs/10/libpq-connect.html#LIBPQ-CONNSTRING>`_

Empty DSN Connections / Environment Variable Connections
---------------------------------------------------------

The psycopg2 DBAPI can connect to PostgreSQL by passing an empty DSN to the
libpq client library, which by default indicates to connect to a localhost
PostgreSQL database that is open for "trust" connections.  This behavior can be
further tailored using a particular set of environment variables which are
prefixed with ``PG_...``, which are  consumed by ``libpq`` to take the place of
any or all elements of the connection string.

For this form, the URL can be passed without any elements other than the
initial scheme::

    engine = create_engine('postgresql+psycopg2://')

In the above form, a blank "dsn" string is passed to the ``psycopg2.connect()``
function which in turn represents an empty DSN passed to libpq.

.. versionadded:: 1.3.2 support for parameter-less connections with psycopg2.

.. seealso::

    `Environment Variables\
    <https://www.postgresql.org/docs/current/libpq-envars.html>`_ -
    PostgreSQL documentation on how to use ``PG_...``
    environment variables for connections.

.. _psycopg2_execution_options:

Per-Statement/Connection Execution Options
-------------------------------------------

The following DBAPI-specific options are respected when used with
:meth:`_engine.Connection.execution_options`,
:meth:`.Executable.execution_options`,
:meth:`_query.Query.execution_options`,
in addition to those not specific to DBAPIs:

* ``isolation_level`` - Set the transaction isolation level for the lifespan
  of a :class:`_engine.Connection` (can only be set on a connection,
  not a statement
  or query).   See :ref:`psycopg2_isolation_level`.

* ``stream_results`` - Enable or disable usage of psycopg2 server side
  cursors - this feature makes use of "named" cursors in combination with
  special result handling methods so that result rows are not fully buffered.
  If ``None`` or not set, the ``server_side_cursors`` option of the
  :class:`_engine.Engine` is used.

* ``max_row_buffer`` - when using ``stream_results``, an integer value that
  specifies the maximum number of rows to buffer at a time.  This is
  interpreted by the :class:`.BufferedRowResultProxy`, and if omitted the
  buffer will grow to ultimately store 1000 rows at a time.

  .. versionadded:: 1.0.6

.. _psycopg2_batch_mode:

.. _psycopg2_executemany_mode:

Psycopg2 Fast Execution Helpers
-------------------------------

Modern versions of psycopg2 include a feature known as
`Fast Execution Helpers \
<http://initd.org/psycopg/docs/extras.html#fast-execution-helpers>`_, which
have been shown in benchmarking to improve psycopg2's executemany()
performance, primarily with INSERT statements, by multiple orders of magnitude.
SQLAlchemy allows this extension to be used for all ``executemany()`` style
calls invoked by an :class:`_engine.Engine`
when used with :ref:`multiple parameter
sets <execute_multiple>`, which includes the use of this feature both by the
Core as well as by the ORM for inserts of objects with non-autogenerated
primary key values, by adding the ``executemany_mode`` flag to
:func:`_sa.create_engine`::

    engine = create_engine(
        "postgresql+psycopg2://scott:tiger@host/dbname",
        executemany_mode='batch')


.. versionchanged:: 1.3.7  - the ``use_batch_mode`` flag has been superseded
   by a new parameter ``executemany_mode`` which provides support both for
   psycopg2's ``execute_batch`` helper as well as the ``execute_values``
   helper.

Possible options for ``executemany_mode`` include:

* ``None`` - By default, psycopg2's extensions are not used, and the usual
  ``cursor.executemany()`` method is used when invoking batches of statements.

* ``'batch'`` - Uses ``psycopg2.extras.execute_batch`` so that multiple copies
  of a SQL query, each one corresponding to a parameter set passed to
  ``executemany()``, are joined into a single SQL string separated by a
  semicolon.   This is the same behavior as was provided by the
  ``use_batch_mode=True`` flag.

* ``'values'``- For Core :func:`_expression.insert`
  constructs only (including those
  emitted by the ORM automatically), the ``psycopg2.extras.execute_values``
  extension is used so that multiple parameter sets are grouped into a single
  INSERT statement and joined together with multiple VALUES expressions.   This
  method requires that the string text of the VALUES clause inside the
  INSERT statement is manipulated, so is only supported with a compiled
  :func:`_expression.insert` construct where the format is predictable.
  For all other
  constructs,  including plain textual INSERT statements not rendered  by the
  SQLAlchemy expression language compiler, the
  ``psycopg2.extras.execute_batch``  method is used.   It is therefore important
  to note that **"values" mode implies that "batch" mode is also used for
  all statements for which "values" mode does not apply**.

For both strategies, the ``executemany_batch_page_size`` and
``executemany_values_page_size`` arguments control how many parameter sets
should be represented in each execution.  Because "values" mode implies a
fallback down to "batch" mode for non-INSERT statements, there are two
independent page size arguments.  For each, the default value of ``None`` means
to use psycopg2's defaults, which at the time of this writing are quite low at
100.   For the ``execute_values`` method, a number as high as 10000 may prove
to be performant, whereas for ``execute_batch``, as the number represents
full statements repeated, a number closer to the default of 100 is likely
more appropriate::

    engine = create_engine(
        "postgresql+psycopg2://scott:tiger@host/dbname",
        executemany_mode='values',
        executemany_values_page_size=10000, executemany_batch_page_size=500)


.. seealso::

    :ref:`execute_multiple` - General information on using the
    :class:`_engine.Connection`
    object to execute statements in such a way as to make
    use of the DBAPI ``.executemany()`` method.

.. versionchanged:: 1.3.7 - Added support for
   ``psycopg2.extras.execute_values``.   The ``use_batch_mode`` flag is
   superseded by the ``executemany_mode`` flag.


.. _psycopg2_unicode:

Unicode with Psycopg2
----------------------

By default, the psycopg2 driver uses the ``psycopg2.extensions.UNICODE``
extension, such that the DBAPI receives and returns all strings as Python
Unicode objects directly - SQLAlchemy passes these values through without
change.   Psycopg2 here will encode/decode string values based on the
current "client encoding" setting; by default this is the value in
the ``postgresql.conf`` file, which often defaults to ``SQL_ASCII``.
Typically, this can be changed to ``utf8``, as a more useful default::

    # postgresql.conf file

    # client_encoding = sql_ascii # actually, defaults to database
                                 # encoding
    client_encoding = utf8

A second way to affect the client encoding is to set it within Psycopg2
locally.   SQLAlchemy will call psycopg2's
:meth:`psycopg2:connection.set_client_encoding` method
on all new connections based on the value passed to
:func:`_sa.create_engine` using the ``client_encoding`` parameter::

    # set_client_encoding() setting;
    # works for *all* PostgreSQL versions
    engine = create_engine("postgresql://user:pass@host/dbname",
                           client_encoding='utf8')

This overrides the encoding specified in the PostgreSQL client configuration.
When using the parameter in this way, the psycopg2 driver emits
``SET client_encoding TO 'utf8'`` on the connection explicitly, and works
in all PostgreSQL versions.

Note that the ``client_encoding`` setting as passed to
:func:`_sa.create_engine`
is **not the same** as the more recently added ``client_encoding`` parameter
now supported by libpq directly.   This is enabled when ``client_encoding``
is passed directly to ``psycopg2.connect()``, and from SQLAlchemy is passed
using the :paramref:`_sa.create_engine.connect_args` parameter::

    engine = create_engine(
        "postgresql://user:pass@host/dbname",
        connect_args={'client_encoding': 'utf8'})

    # using the query string is equivalent
    engine = create_engine("postgresql://user:pass@host/dbname?client_encoding=utf8")

The above parameter was only added to libpq as of version 9.1 of PostgreSQL,
so using the previous method is better for cross-version support.

.. _psycopg2_disable_native_unicode:

Disabling Native Unicode
^^^^^^^^^^^^^^^^^^^^^^^^

SQLAlchemy can also be instructed to skip the usage of the psycopg2
``UNICODE`` extension and to instead utilize its own unicode encode/decode
services, which are normally reserved only for those DBAPIs that don't
fully support unicode directly.  Passing ``use_native_unicode=False`` to
:func:`_sa.create_engine` will disable usage of ``psycopg2.extensions.
UNICODE``.
SQLAlchemy will instead encode data itself into Python bytestrings on the way
in and coerce from bytes on the way back,
using the value of the :func:`_sa.create_engine` ``encoding`` parameter, which
defaults to ``utf-8``.
SQLAlchemy's own unicode encode/decode functionality is steadily becoming
obsolete as most DBAPIs now support unicode fully.

Bound Parameter Styles
----------------------

The default parameter style for the psycopg2 dialect is "pyformat", where
SQL is rendered using ``%(paramname)s`` style.   This format has the limitation
that it does not accommodate the unusual case of parameter names that
actually contain percent or parenthesis symbols; as SQLAlchemy in many cases
generates bound parameter names based on the name of a column, the presence
of these characters in a column name can lead to problems.

There are two solutions to the issue of a :class:`_schema.Column`
that contains
one of these characters in its name.  One is to specify the
:paramref:`.schema.Column.key` for columns that have such names::

    measurement = Table('measurement', metadata,
        Column('Size (meters)', Integer, key='size_meters')
    )

Above, an INSERT statement such as ``measurement.insert()`` will use
``size_meters`` as the parameter name, and a SQL expression such as
``measurement.c.size_meters > 10`` will derive the bound parameter name
from the ``size_meters`` key as well.

.. versionchanged:: 1.0.0 - SQL expressions will use
   :attr:`_schema.Column.key`
   as the source of naming when anonymous bound parameters are created
   in SQL expressions; previously, this behavior only applied to
   :meth:`_schema.Table.insert` and :meth:`_schema.Table.update`
   parameter names.

The other solution is to use a positional format; psycopg2 allows use of the
"format" paramstyle, which can be passed to
:paramref:`_sa.create_engine.paramstyle`::

    engine = create_engine(
        'postgresql://scott:tiger@localhost:5432/test', paramstyle='format')

With the above engine, instead of a statement like::

    INSERT INTO measurement ("Size (meters)") VALUES (%(Size (meters))s)
    {'Size (meters)': 1}

we instead see::

    INSERT INTO measurement ("Size (meters)") VALUES (%s)
    (1, )

Where above, the dictionary style is converted into a tuple with positional
style.


Transactions
------------

The psycopg2 dialect fully supports SAVEPOINT and two-phase commit operations.

.. _psycopg2_isolation_level:

Psycopg2 Transaction Isolation Level
-------------------------------------

As discussed in :ref:`postgresql_isolation_level`,
all PostgreSQL dialects support setting of transaction isolation level
both via the ``isolation_level`` parameter passed to :func:`_sa.create_engine`
,
as well as the ``isolation_level`` argument used by
:meth:`_engine.Connection.execution_options`.  When using the psycopg2 dialect
, these
options make use of psycopg2's ``set_isolation_level()`` connection method,
rather than emitting a PostgreSQL directive; this is because psycopg2's
API-level setting is always emitted at the start of each transaction in any
case.

The psycopg2 dialect supports these constants for isolation level:

* ``READ COMMITTED``
* ``READ UNCOMMITTED``
* ``REPEATABLE READ``
* ``SERIALIZABLE``
* ``AUTOCOMMIT``

.. seealso::

    :ref:`postgresql_isolation_level`

    :ref:`pg8000_isolation_level`


NOTICE logging
---------------

The psycopg2 dialect will log PostgreSQL NOTICE messages
via the ``sqlalchemy.dialects.postgresql`` logger.  When this logger
is set to the ``logging.INFO`` level, notice messages will be logged::

    import logging

    logging.getLogger('sqlalchemy.dialects.postgresql').setLevel(logging.INFO)

Above, it is assumed that logging is configured externally.  If this is not
the case, configuration such as ``logging.basicConfig()`` must be utilized::

    import logging

    logging.basicConfig()   # log messages to stdout
    logging.getLogger('sqlalchemy.dialects.postgresql').setLevel(logging.INFO)

.. seealso::

    `Logging HOWTO <https://docs.python.org/3/howto/logging.html>`_ - on the python.org website

.. _psycopg2_hstore:

HSTORE type
------------

The ``psycopg2`` DBAPI includes an extension to natively handle marshalling of
the HSTORE type.   The SQLAlchemy psycopg2 dialect will enable this extension
by default when psycopg2 version 2.4 or greater is used, and
it is detected that the target database has the HSTORE type set up for use.
In other words, when the dialect makes the first
connection, a sequence like the following is performed:

1. Request the available HSTORE oids using
   ``psycopg2.extras.HstoreAdapter.get_oids()``.
   If this function returns a list of HSTORE identifiers, we then determine
   that the ``HSTORE`` extension is present.
   This function is **skipped** if the version of psycopg2 installed is
   less than version 2.4.

2. If the ``use_native_hstore`` flag is at its default of ``True``, and
   we've detected that ``HSTORE`` oids are available, the
   ``psycopg2.extensions.register_hstore()`` extension is invoked for all
   connections.

The ``register_hstore()`` extension has the effect of **all Python
dictionaries being accepted as parameters regardless of the type of target
column in SQL**. The dictionaries are converted by this extension into a
textual HSTORE expression.  If this behavior is not desired, disable the
use of the hstore extension by setting ``use_native_hstore`` to ``False`` as
follows::

    engine = create_engine("postgresql+psycopg2://scott:tiger@localhost/test",
                use_native_hstore=False)

The ``HSTORE`` type is **still supported** when the
``psycopg2.extensions.register_hstore()`` extension is not used.  It merely
means that the coercion between Python dictionaries and the HSTORE
string format, on both the parameter side and the result side, will take
place within SQLAlchemy's own marshalling logic, and not that of ``psycopg2``
which may be more performant.

"""
logger = logging.getLogger("sqlalchemy.dialects.postgresql")
class _PGNumeric(sqltypes.Numeric):
    def bind_processor(self, dialect):
        ...
    
    def result_processor(self, dialect, coltype):
        ...
    


class _PGEnum(ENUM):
    def result_processor(self, dialect, coltype):
        ...
    


class _PGHStore(HSTORE):
    def bind_processor(self, dialect):
        ...
    
    def result_processor(self, dialect, coltype):
        ...
    


class _PGJSON(JSON):
    def result_processor(self, dialect, coltype):
        ...
    


class _PGJSONB(JSONB):
    def result_processor(self, dialect, coltype):
        ...
    


class _PGUUID(UUID):
    def bind_processor(self, dialect):
        ...
    
    def result_processor(self, dialect, coltype):
        ...
    


_server_side_id = util.counter()
class PGExecutionContext_psycopg2(PGExecutionContext):
    def create_server_side_cursor(self):
        ...
    
    def get_result_proxy(self):
        ...
    


class PGCompiler_psycopg2(PGCompiler):
    ...


class PGIdentifierPreparer_psycopg2(PGIdentifierPreparer):
    ...


EXECUTEMANY_DEFAULT = util.symbol("executemany_default")
EXECUTEMANY_BATCH = util.symbol("executemany_batch")
EXECUTEMANY_VALUES = util.symbol("executemany_values")
class PGDialect_psycopg2(PGDialect):
    driver = ...
    if util.py2k:
        supports_unicode_statements = ...
    supports_server_side_cursors = ...
    default_paramstyle = ...
    supports_sane_multi_rowcount = ...
    execution_ctx_cls = ...
    statement_compiler = ...
    preparer = ...
    psycopg2_version = ...
    FEATURE_VERSION_MAP = ...
    _has_native_hstore = ...
    _has_native_json = ...
    _has_native_jsonb = ...
    engine_config_types = ...
    colspecs = ...
    @util.deprecated_params(use_batch_mode=("1.3.7", "The psycopg2 use_batch_mode flag is superseded by " "executemany_mode='batch'"))
    def __init__(self, server_side_cursors=..., use_native_unicode=..., client_encoding=..., use_native_hstore=..., use_native_uuid=..., executemany_mode=..., executemany_batch_page_size=..., executemany_values_page_size=..., use_batch_mode=..., **kwargs) -> None:
        ...
    
    def initialize(self, connection):
        ...
    
    @classmethod
    def dbapi(cls):
        ...
    
    def set_isolation_level(self, connection, level):
        ...
    
    def on_connect(self):
        ...
    
    def do_executemany(self, cursor, statement, parameters, context=...):
        ...
    
    def create_connect_args(self, url):
        ...
    
    def is_disconnect(self, e, connection, cursor):
        ...
    


dialect = PGDialect_psycopg2

"""
This type stub file was generated by pyright.
"""

from .base import BIT
from .mysqldb import MySQLDialect_mysqldb

r"""

.. dialect:: mysql+cymysql
    :name: CyMySQL
    :dbapi: cymysql
    :connectstring: mysql+cymysql://<username>:<password>@<host>/<dbname>[?<options>]
    :url: https://github.com/nakagami/CyMySQL

.. note::

    The CyMySQL dialect is **not tested as part of SQLAlchemy's continuous
    integration** and may have unresolved issues.  The recommended MySQL
    dialects are mysqlclient and PyMySQL.

"""
class _cymysqlBIT(BIT):
    def result_processor(self, dialect, coltype):
        """Convert a MySQL's 64 bit, variable length binary string to a
        long."""
        ...
    


class MySQLDialect_cymysql(MySQLDialect_mysqldb):
    driver = ...
    description_encoding = ...
    supports_sane_rowcount = ...
    supports_sane_multi_rowcount = ...
    supports_unicode_statements = ...
    colspecs = ...
    @classmethod
    def dbapi(cls):
        ...
    
    def is_disconnect(self, e, connection, cursor):
        ...
    


dialect = MySQLDialect_cymysql

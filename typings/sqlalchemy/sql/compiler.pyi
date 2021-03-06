"""
This type stub file was generated by pyright.
"""

import re
from . import functions, operators, selectable, visitors
from .. import util

"""Base SQL and DDL compiler implementations.

Classes provided include:

:class:`.compiler.SQLCompiler` - renders SQL
strings

:class:`.compiler.DDLCompiler` - renders DDL
(data definition language) strings

:class:`.compiler.GenericTypeCompiler` - renders
type specification strings.

To generate user-defined SQL strings, see
:doc:`/ext/compiler`.

"""
RESERVED_WORDS = set(["all", "analyse", "analyze", "and", "any", "array", "as", "asc", "asymmetric", "authorization", "between", "binary", "both", "case", "cast", "check", "collate", "column", "constraint", "create", "cross", "current_date", "current_role", "current_time", "current_timestamp", "current_user", "default", "deferrable", "desc", "distinct", "do", "else", "end", "except", "false", "for", "foreign", "freeze", "from", "full", "grant", "group", "having", "ilike", "in", "initially", "inner", "intersect", "into", "is", "isnull", "join", "leading", "left", "like", "limit", "localtime", "localtimestamp", "natural", "new", "not", "notnull", "null", "off", "offset", "old", "on", "only", "or", "order", "outer", "overlaps", "placing", "primary", "references", "right", "select", "session_user", "set", "similar", "some", "symmetric", "table", "then", "to", "trailing", "true", "union", "unique", "user", "using", "verbose", "when", "where"])
LEGAL_CHARACTERS = re.compile(r"^[A-Z0-9_$]+$", re.I)
LEGAL_CHARACTERS_PLUS_SPACE = re.compile(r"^[A-Z0-9_ $]+$", re.I)
ILLEGAL_INITIAL_CHARACTERS = str(x) for x in range(0, 10).union(["$"])
FK_ON_DELETE = re.compile(r"^(?:RESTRICT|CASCADE|SET NULL|NO ACTION|SET DEFAULT)$", re.I)
FK_ON_UPDATE = re.compile(r"^(?:RESTRICT|CASCADE|SET NULL|NO ACTION|SET DEFAULT)$", re.I)
FK_INITIALLY = re.compile(r"^(?:DEFERRED|IMMEDIATE)$", re.I)
BIND_PARAMS = re.compile(r"(?<![:\w\$\x5c]):([\w\$]+)(?![:\w\$])", re.UNICODE)
BIND_PARAMS_ESC = re.compile(r"\x5c(:[\w\$]*)(?![:\w\$])", re.UNICODE)
BIND_TEMPLATES = { "pyformat": "%%(%(name)s)s","qmark": "?","format": "%%s","numeric": ":[_POSITION]","named": ":%(name)s" }
OPERATORS = { operators.and_: " AND ",operators.or_: " OR ",operators.add: " + ",operators.mul: " * ",operators.sub: " - ",operators.div: " / ",operators.mod: " % ",operators.truediv: " / ",operators.neg: "-",operators.lt: " < ",operators.le: " <= ",operators.ne: " != ",operators.gt: " > ",operators.ge: " >= ",operators.eq: " = ",operators.is_distinct_from: " IS DISTINCT FROM ",operators.isnot_distinct_from: " IS NOT DISTINCT FROM ",operators.concat_op: " || ",operators.match_op: " MATCH ",operators.notmatch_op: " NOT MATCH ",operators.in_op: " IN ",operators.notin_op: " NOT IN ",operators.comma_op: ", ",operators.from_: " FROM ",operators.as_: " AS ",operators.is_: " IS ",operators.isnot: " IS NOT ",operators.collate: " COLLATE ",operators.exists: "EXISTS ",operators.distinct_op: "DISTINCT ",operators.inv: "NOT ",operators.any_op: "ANY ",operators.all_op: "ALL ",operators.desc_op: " DESC",operators.asc_op: " ASC",operators.nullsfirst_op: " NULLS FIRST",operators.nullslast_op: " NULLS LAST" }
FUNCTIONS = { functions.coalesce: "coalesce",functions.current_date: "CURRENT_DATE",functions.current_time: "CURRENT_TIME",functions.current_timestamp: "CURRENT_TIMESTAMP",functions.current_user: "CURRENT_USER",functions.localtime: "LOCALTIME",functions.localtimestamp: "LOCALTIMESTAMP",functions.random: "random",functions.sysdate: "sysdate",functions.session_user: "SESSION_USER",functions.user: "USER",functions.cube: "CUBE",functions.rollup: "ROLLUP",functions.grouping_sets: "GROUPING SETS" }
EXTRACT_MAP = { "month": "month","day": "day","year": "year","second": "second","hour": "hour","doy": "doy","minute": "minute","quarter": "quarter","dow": "dow","week": "week","epoch": "epoch","milliseconds": "milliseconds","microseconds": "microseconds","timezone_hour": "timezone_hour","timezone_minute": "timezone_minute" }
COMPOUND_KEYWORDS = { selectable.CompoundSelect.UNION: "UNION",selectable.CompoundSelect.UNION_ALL: "UNION ALL",selectable.CompoundSelect.EXCEPT: "EXCEPT",selectable.CompoundSelect.EXCEPT_ALL: "EXCEPT ALL",selectable.CompoundSelect.INTERSECT: "INTERSECT",selectable.CompoundSelect.INTERSECT_ALL: "INTERSECT ALL" }
class Compiled(object):
    """Represent a compiled SQL or DDL expression.

    The ``__str__`` method of the ``Compiled`` object should produce
    the actual text of the statement.  ``Compiled`` objects are
    specific to their underlying database dialect, and also may
    or may not be specific to the columns referenced within a
    particular set of bind parameters.  In no case should the
    ``Compiled`` object be dependent on the actual values of those
    bind parameters, even though it may reference those values as
    defaults.
    """
    _cached_metadata = ...
    schema_translate_map = ...
    execution_options = ...
    def __init__(self, dialect, statement, bind=..., schema_translate_map=..., compile_kwargs=...) -> None:
        """Construct a new :class:`.Compiled` object.

        :param dialect: :class:`.Dialect` to compile against.

        :param statement: :class:`_expression.ClauseElement` to be compiled.

        :param bind: Optional Engine or Connection to compile this
          statement against.

        :param schema_translate_map: dictionary of schema names to be
         translated when forming the resultant SQL

         .. versionadded:: 1.1

         .. seealso::

            :ref:`schema_translating`

        :param compile_kwargs: additional kwargs that will be
         passed to the initial call to :meth:`.Compiled.process`.


        """
        ...
    
    @util.deprecated("0.7", "The :meth:`.Compiled.compile` method is deprecated and will be " "removed in a future release.   The :class:`.Compiled` object " "now runs its compilation within the constructor, and this method " "does nothing.")
    def compile(self):
        """Produce the internal string representation of this element."""
        ...
    
    @property
    def sql_compiler(self):
        """Return a Compiled that is capable of processing SQL expressions.

        If this compiler is one, it would likely just return 'self'.

        """
        ...
    
    def process(self, obj, **kwargs):
        ...
    
    def __str__(self) -> str:
        """Return the string text of the generated SQL or DDL."""
        ...
    
    def construct_params(self, params=...):
        """Return the bind params for this compiled object.

        :param params: a dict of string/object pairs whose values will
                       override bind values compiled in to the
                       statement.
        """
        ...
    
    @property
    def params(self):
        """Return the bind params for this compiled object."""
        ...
    
    def execute(self, *multiparams, **params):
        """Execute this compiled object."""
        ...
    
    def scalar(self, *multiparams, **params):
        """Execute this compiled object and return the result's
        scalar value."""
        ...
    


class TypeCompiler(util.with_metaclass(util.EnsureKWArgType, object)):
    """Produces DDL specification for TypeEngine objects."""
    ensure_kwarg = ...
    def __init__(self, dialect) -> None:
        ...
    
    def process(self, type_, **kw):
        ...
    


class _CompileLabel(visitors.Visitable):
    """lightweight label object which acts as an expression.Label."""
    __visit_name__ = ...
    __slots__ = ...
    def __init__(self, col, name, alt_names=...) -> None:
        ...
    
    @property
    def proxy_set(self):
        ...
    
    @property
    def type(self):
        ...
    
    def self_group(self, **kw):
        ...
    


class prefix_anon_map(dict):
    """A map that creates new keys for missing key access.
    Considers keys of the form "<ident> <name>" to produce
    new symbols "<name>_<index>", where "index" is an incrementing integer
    corresponding to <name>.
    Inlines the approach taken by :class:`sqlalchemy.util.PopulateDict` which
    is otherwise usually used for this type of operation.
    """
    def __missing__(self, key):
        ...
    


class SQLCompiler(Compiled):
    """Default implementation of :class:`.Compiled`.

    Compiles :class:`_expression.ClauseElement` objects into SQL strings.

    """
    extract_map = ...
    compound_keywords = ...
    isdelete = ...
    isplaintext = ...
    returning = ...
    returning_precedes_values = ...
    render_table_with_column_in_update_from = ...
    contains_expanding_parameters = ...
    ansi_bind_rules = ...
    _textual_ordered_columns = ...
    _ordered_columns = ...
    _numeric_binds = ...
    insert_single_values_expr = ...
    insert_prefetch = ...
    def __init__(self, dialect, statement, column_keys=..., inline=..., **kwargs) -> None:
        """Construct a new :class:`.SQLCompiler` object.

        :param dialect: :class:`.Dialect` to be used

        :param statement: :class:`_expression.ClauseElement` to be compiled

        :param column_keys:  a list of column names to be compiled into an
         INSERT or UPDATE statement.

        :param inline: whether to generate INSERT statements as "inline", e.g.
         not formatted to return any generated defaults

        :param kwargs: additional keyword arguments to be consumed by the
         superclass.

        """
        ...
    
    @property
    def prefetch(self):
        ...
    
    def is_subquery(self):
        ...
    
    @property
    def sql_compiler(self):
        ...
    
    def construct_params(self, params=..., _group_number=..., _check=...):
        """return a dictionary of bind parameter keys and values"""
        ...
    
    @property
    def params(self):
        """Return the bind param dictionary embedded into this
        compiled object, for those values that are present."""
        ...
    
    def default_from(self):
        """Called when a SELECT statement has no froms, and no FROM clause is
        to be appended.

        Gives Oracle a chance to tack on a ``FROM DUAL`` to the string output.

        """
        ...
    
    def visit_grouping(self, grouping, asfrom=..., **kwargs):
        ...
    
    def visit_label_reference(self, element, within_columns_clause=..., **kwargs):
        ...
    
    def visit_textual_label_reference(self, element, within_columns_clause=..., **kwargs):
        ...
    
    def visit_label(self, label, add_to_result_map=..., within_label_clause=..., within_columns_clause=..., render_label_as_label=..., **kw):
        ...
    
    def visit_column(self, column, add_to_result_map=..., include_table=..., **kwargs):
        ...
    
    def visit_collation(self, element, **kw):
        ...
    
    def visit_fromclause(self, fromclause, **kwargs):
        ...
    
    def visit_index(self, index, **kwargs):
        ...
    
    def visit_typeclause(self, typeclause, **kw):
        ...
    
    def post_process_text(self, text):
        ...
    
    def escape_literal_column(self, text):
        ...
    
    def visit_textclause(self, textclause, **kw):
        ...
    
    def visit_text_as_from(self, taf, compound_index=..., asfrom=..., parens=..., **kw):
        ...
    
    def visit_null(self, expr, **kw):
        ...
    
    def visit_true(self, expr, **kw):
        ...
    
    def visit_false(self, expr, **kw):
        ...
    
    def visit_clauselist(self, clauselist, **kw):
        ...
    
    def visit_case(self, clause, **kwargs):
        ...
    
    def visit_type_coerce(self, type_coerce, **kw):
        ...
    
    def visit_cast(self, cast, **kwargs):
        ...
    
    def visit_over(self, over, **kwargs):
        ...
    
    def visit_withingroup(self, withingroup, **kwargs):
        ...
    
    def visit_funcfilter(self, funcfilter, **kwargs):
        ...
    
    def visit_extract(self, extract, **kwargs):
        ...
    
    def visit_function(self, func, add_to_result_map=..., **kwargs):
        ...
    
    def visit_next_value_func(self, next_value, **kw):
        ...
    
    def visit_sequence(self, sequence, **kw):
        ...
    
    def function_argspec(self, func, **kwargs):
        ...
    
    def visit_compound_select(self, cs, asfrom=..., parens=..., compound_index=..., **kwargs):
        ...
    
    def visit_unary(self, unary, **kw):
        ...
    
    def visit_istrue_unary_operator(self, element, operator, **kw):
        ...
    
    def visit_isfalse_unary_operator(self, element, operator, **kw):
        ...
    
    def visit_notmatch_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_empty_in_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_empty_notin_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_empty_set_expr(self, element_types):
        ...
    
    def visit_binary(self, binary, override_operator=..., eager_grouping=..., **kw):
        ...
    
    def visit_function_as_comparison_op_binary(self, element, operator, **kw):
        ...
    
    def visit_mod_binary(self, binary, operator, **kw):
        ...
    
    def visit_custom_op_binary(self, element, operator, **kw):
        ...
    
    def visit_custom_op_unary_operator(self, element, operator, **kw):
        ...
    
    def visit_custom_op_unary_modifier(self, element, operator, **kw):
        ...
    
    def visit_contains_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_notcontains_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_startswith_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_notstartswith_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_endswith_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_notendswith_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_like_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_notlike_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_ilike_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_notilike_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_between_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_notbetween_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_bindparam(self, bindparam, within_columns_clause=..., literal_binds=..., skip_bind_expression=..., **kwargs):
        ...
    
    def render_literal_bindparam(self, bindparam, **kw):
        ...
    
    def render_literal_value(self, value, type_):
        """Render the value of a bind parameter as a quoted literal.

        This is used for statement sections that do not accept bind parameters
        on the target driver/database.

        This should be implemented by subclasses using the quoting services
        of the DBAPI.

        """
        ...
    
    def bindparam_string(self, name, positional_names=..., expanding=..., **kw):
        ...
    
    def visit_cte(self, cte, asfrom=..., ashint=..., fromhints=..., visiting_cte=..., **kwargs):
        ...
    
    def visit_alias(self, alias, asfrom=..., ashint=..., iscrud=..., fromhints=..., **kwargs):
        ...
    
    def visit_lateral(self, lateral, **kw):
        ...
    
    def visit_tablesample(self, tablesample, asfrom=..., **kw):
        ...
    
    def get_render_as_alias_suffix(self, alias_name_text):
        ...
    
    def format_from_hint_text(self, sqltext, table, hint, iscrud):
        ...
    
    def get_select_hint_text(self, byfroms):
        ...
    
    def get_from_hint_text(self, table, text):
        ...
    
    def get_crud_hint_text(self, table, text):
        ...
    
    def get_statement_hint_text(self, hint_texts):
        ...
    
    _default_stack_entry = ...
    def visit_select(self, select, asfrom=..., parens=..., fromhints=..., compound_index=..., nested_join_translation=..., select_wraps_for=..., lateral=..., **kwargs):
        ...
    
    def get_cte_preamble(self, recursive):
        ...
    
    def get_select_precolumns(self, select, **kw):
        """Called when building a ``SELECT`` statement, position is just
        before column list.

        """
        ...
    
    def group_by_clause(self, select, **kw):
        """allow dialects to customize how GROUP BY is rendered."""
        ...
    
    def order_by_clause(self, select, **kw):
        """allow dialects to customize how ORDER BY is rendered."""
        ...
    
    def for_update_clause(self, select, **kw):
        ...
    
    def returning_clause(self, stmt, returning_cols):
        ...
    
    def limit_clause(self, select, **kw):
        ...
    
    def visit_table(self, table, asfrom=..., iscrud=..., ashint=..., fromhints=..., use_schema=..., **kwargs):
        ...
    
    def visit_join(self, join, asfrom=..., **kwargs):
        ...
    
    def visit_insert(self, insert_stmt, asfrom=..., **kw):
        ...
    
    def update_limit_clause(self, update_stmt):
        """Provide a hook for MySQL to add LIMIT to the UPDATE"""
        ...
    
    def update_tables_clause(self, update_stmt, from_table, extra_froms, **kw):
        """Provide a hook to override the initial table clause
        in an UPDATE statement.

        MySQL overrides this.

        """
        ...
    
    def update_from_clause(self, update_stmt, from_table, extra_froms, from_hints, **kw):
        """Provide a hook to override the generation of an
        UPDATE..FROM clause.

        MySQL and MSSQL override this.

        """
        ...
    
    def visit_update(self, update_stmt, asfrom=..., **kw):
        ...
    
    def delete_extra_from_clause(self, update_stmt, from_table, extra_froms, from_hints, **kw):
        """Provide a hook to override the generation of an
        DELETE..FROM clause.

        This can be used to implement DELETE..USING for example.

        MySQL and MSSQL override this.

        """
        ...
    
    def delete_table_clause(self, delete_stmt, from_table, extra_froms):
        ...
    
    def visit_delete(self, delete_stmt, asfrom=..., **kw):
        ...
    
    def visit_savepoint(self, savepoint_stmt):
        ...
    
    def visit_rollback_to_savepoint(self, savepoint_stmt):
        ...
    
    def visit_release_savepoint(self, savepoint_stmt):
        ...
    


class StrSQLCompiler(SQLCompiler):
    """A :class:`.SQLCompiler` subclass which allows a small selection
    of non-standard SQL features to render into a string value.

    The :class:`.StrSQLCompiler` is invoked whenever a Core expression
    element is directly stringified without calling upon the
    :meth:`_expression.ClauseElement.compile` method.
    It can render a limited set
    of non-standard SQL constructs to assist in basic stringification,
    however for more substantial custom or dialect-specific SQL constructs,
    it will be necessary to make use of
    :meth:`_expression.ClauseElement.compile`
    directly.

    .. seealso::

        :ref:`faq_sql_expression_string`

    """
    def visit_getitem_binary(self, binary, operator, **kw):
        ...
    
    def visit_json_getitem_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_json_path_getitem_op_binary(self, binary, operator, **kw):
        ...
    
    def visit_sequence(self, seq, **kw):
        ...
    
    def returning_clause(self, stmt, returning_cols):
        ...
    
    def update_from_clause(self, update_stmt, from_table, extra_froms, from_hints, **kw):
        ...
    
    def delete_extra_from_clause(self, update_stmt, from_table, extra_froms, from_hints, **kw):
        ...
    
    def get_from_hint_text(self, table, text):
        ...
    


class DDLCompiler(Compiled):
    @util.memoized_property
    def sql_compiler(self):
        ...
    
    @util.memoized_property
    def type_compiler(self):
        ...
    
    def construct_params(self, params=...):
        ...
    
    def visit_ddl(self, ddl, **kwargs):
        ...
    
    def visit_create_schema(self, create):
        ...
    
    def visit_drop_schema(self, drop):
        ...
    
    def visit_create_table(self, create):
        ...
    
    def visit_create_column(self, create, first_pk=...):
        ...
    
    def create_table_constraints(self, table, _include_foreign_key_constraints=...):
        ...
    
    def visit_drop_table(self, drop):
        ...
    
    def visit_drop_view(self, drop):
        ...
    
    def visit_create_index(self, create, include_schema=..., include_table_schema=...):
        ...
    
    def visit_drop_index(self, drop):
        ...
    
    def visit_add_constraint(self, create):
        ...
    
    def visit_set_table_comment(self, create):
        ...
    
    def visit_drop_table_comment(self, drop):
        ...
    
    def visit_set_column_comment(self, create):
        ...
    
    def visit_drop_column_comment(self, drop):
        ...
    
    def visit_create_sequence(self, create):
        ...
    
    def visit_drop_sequence(self, drop):
        ...
    
    def visit_drop_constraint(self, drop):
        ...
    
    def get_column_specification(self, column, **kwargs):
        ...
    
    def create_table_suffix(self, table):
        ...
    
    def post_create_table(self, table):
        ...
    
    def get_column_default_string(self, column):
        ...
    
    def visit_check_constraint(self, constraint):
        ...
    
    def visit_column_check_constraint(self, constraint):
        ...
    
    def visit_primary_key_constraint(self, constraint):
        ...
    
    def visit_foreign_key_constraint(self, constraint):
        ...
    
    def define_constraint_remote_table(self, constraint, table, preparer):
        """Format the remote table clause of a CREATE CONSTRAINT clause."""
        ...
    
    def visit_unique_constraint(self, constraint):
        ...
    
    def define_constraint_cascades(self, constraint):
        ...
    
    def define_constraint_deferrability(self, constraint):
        ...
    
    def define_constraint_match(self, constraint):
        ...
    
    def visit_computed_column(self, generated):
        ...
    


class GenericTypeCompiler(TypeCompiler):
    def visit_FLOAT(self, type_, **kw):
        ...
    
    def visit_REAL(self, type_, **kw):
        ...
    
    def visit_NUMERIC(self, type_, **kw):
        ...
    
    def visit_DECIMAL(self, type_, **kw):
        ...
    
    def visit_INTEGER(self, type_, **kw):
        ...
    
    def visit_SMALLINT(self, type_, **kw):
        ...
    
    def visit_BIGINT(self, type_, **kw):
        ...
    
    def visit_TIMESTAMP(self, type_, **kw):
        ...
    
    def visit_DATETIME(self, type_, **kw):
        ...
    
    def visit_DATE(self, type_, **kw):
        ...
    
    def visit_TIME(self, type_, **kw):
        ...
    
    def visit_CLOB(self, type_, **kw):
        ...
    
    def visit_NCLOB(self, type_, **kw):
        ...
    
    def visit_CHAR(self, type_, **kw):
        ...
    
    def visit_NCHAR(self, type_, **kw):
        ...
    
    def visit_VARCHAR(self, type_, **kw):
        ...
    
    def visit_NVARCHAR(self, type_, **kw):
        ...
    
    def visit_TEXT(self, type_, **kw):
        ...
    
    def visit_BLOB(self, type_, **kw):
        ...
    
    def visit_BINARY(self, type_, **kw):
        ...
    
    def visit_VARBINARY(self, type_, **kw):
        ...
    
    def visit_BOOLEAN(self, type_, **kw):
        ...
    
    def visit_large_binary(self, type_, **kw):
        ...
    
    def visit_boolean(self, type_, **kw):
        ...
    
    def visit_time(self, type_, **kw):
        ...
    
    def visit_datetime(self, type_, **kw):
        ...
    
    def visit_date(self, type_, **kw):
        ...
    
    def visit_big_integer(self, type_, **kw):
        ...
    
    def visit_small_integer(self, type_, **kw):
        ...
    
    def visit_integer(self, type_, **kw):
        ...
    
    def visit_real(self, type_, **kw):
        ...
    
    def visit_float(self, type_, **kw):
        ...
    
    def visit_numeric(self, type_, **kw):
        ...
    
    def visit_string(self, type_, **kw):
        ...
    
    def visit_unicode(self, type_, **kw):
        ...
    
    def visit_text(self, type_, **kw):
        ...
    
    def visit_unicode_text(self, type_, **kw):
        ...
    
    def visit_enum(self, type_, **kw):
        ...
    
    def visit_null(self, type_, **kw):
        ...
    
    def visit_type_decorator(self, type_, **kw):
        ...
    
    def visit_user_defined(self, type_, **kw):
        ...
    


class StrSQLTypeCompiler(GenericTypeCompiler):
    def __getattr__(self, key):
        ...
    


class IdentifierPreparer(object):
    """Handle quoting and case-folding of identifiers based on options."""
    reserved_words = ...
    legal_characters = ...
    illegal_initial_characters = ...
    schema_for_object = ...
    def __init__(self, dialect, initial_quote=..., final_quote=..., escape_quote=..., quote_case_sensitive_collations=..., omit_schema=...) -> None:
        """Construct a new ``IdentifierPreparer`` object.

        initial_quote
          Character that begins a delimited identifier.

        final_quote
          Character that ends a delimited identifier. Defaults to
          `initial_quote`.

        omit_schema
          Prevent prepending schema name. Useful for databases that do
          not support schemae.
        """
        ...
    
    def validate_sql_phrase(self, element, reg):
        """keyword sequence filter.

        a filter for elements that are intended to represent keyword sequences,
        such as "INITIALLY", "INITIALLY DEFERRED", etc.   no special characters
        should be present.

        .. versionadded:: 1.3

        """
        ...
    
    def quote_identifier(self, value):
        """Quote an identifier.

        Subclasses should override this to provide database-dependent
        quoting behavior.
        """
        ...
    
    def quote_schema(self, schema, force=...):
        """Conditionally quote a schema name.


        The name is quoted if it is a reserved word, contains quote-necessary
        characters, or is an instance of :class:`.quoted_name` which includes
        ``quote`` set to ``True``.

        Subclasses can override this to provide database-dependent
        quoting behavior for schema names.

        :param schema: string schema name
        :param force: unused

            .. deprecated:: 0.9

                The :paramref:`.IdentifierPreparer.quote_schema.force`
                parameter is deprecated and will be removed in a future
                release.  This flag has no effect on the behavior of the
                :meth:`.IdentifierPreparer.quote` method; please refer to
                :class:`.quoted_name`.

        """
        ...
    
    def quote(self, ident, force=...):
        """Conditionally quote an identfier.

        The identifier is quoted if it is a reserved word, contains
        quote-necessary characters, or is an instance of
        :class:`.quoted_name` which includes ``quote`` set to ``True``.

        Subclasses can override this to provide database-dependent
        quoting behavior for identifier names.

        :param ident: string identifier
        :param force: unused

            .. deprecated:: 0.9

                The :paramref:`.IdentifierPreparer.quote.force`
                parameter is deprecated and will be removed in a future
                release.  This flag has no effect on the behavior of the
                :meth:`.IdentifierPreparer.quote` method; please refer to
                :class:`.quoted_name`.

        """
        ...
    
    def format_collation(self, collation_name):
        ...
    
    def format_sequence(self, sequence, use_schema=...):
        ...
    
    def format_label(self, label, name=...):
        ...
    
    def format_alias(self, alias, name=...):
        ...
    
    def format_savepoint(self, savepoint, name=...):
        ...
    
    @util.dependencies("sqlalchemy.sql.naming")
    def format_constraint(self, naming, constraint):
        ...
    
    def format_index(self, index):
        ...
    
    def format_table(self, table, use_schema=..., name=...):
        """Prepare a quoted table and schema name."""
        ...
    
    def format_schema(self, name):
        """Prepare a quoted schema name."""
        ...
    
    def format_column(self, column, use_table=..., name=..., table_name=..., use_schema=...):
        """Prepare a quoted column name."""
        ...
    
    def format_table_seq(self, table, use_schema=...):
        """Format table name and schema as a tuple."""
        ...
    
    def unformat_identifiers(self, identifiers):
        """Unpack 'schema.table.column'-like strings into components."""
        ...
    



"""
This type stub file was generated by pyright.
"""

from typing import Callable
from .base import Executable, Generative
from .dml import Delete, Insert, Update
from .elements import (
    BinaryExpression,
    BindParameter,
    BooleanClauseList,
    Case,
    Cast,
    CollectionAggregate,
    ColumnClause,
    Extract,
    False_,
    FunctionFilter,
    Grouping,
    Label,
    Null,
    Over,
    TextClause,
    True_,
    Tuple,
    TypeClause,
    TypeCoerce,
    UnaryExpression,
    WithinGroup,
)
from .selectable import (
    Alias,
    CTE,
    CompoundSelect,
    Exists,
    FromGrouping,
    Join,
    Lateral,
    ScalarSelect,
    Select,
    SelectBase,
    TableClause,
    TableSample,
)
from ..util.langhelpers import public_factory

"""Defines the public namespace for SQL expression constructs.

Prior to version 0.9, this module contained all of "elements", "dml",
"default_comparator" and "selectable".   The module was broken up
and most "factory" functions were moved to be grouped with their associated
class.

"""
all_ = public_factory(CollectionAggregate._create_all, ".sql.expression.all_")
any_ = public_factory(CollectionAggregate._create_any, ".sql.expression.any_")
and_ = public_factory(BooleanClauseList.and_, ".sql.expression.and_")
alias = public_factory(Alias._factory, ".sql.expression.alias")
tablesample = public_factory(TableSample._factory, ".sql.expression.tablesample")
lateral = public_factory(Lateral._factory, ".sql.expression.lateral")
or_ = public_factory(BooleanClauseList.or_, ".sql.expression.or_")
bindparam: Callable[..., BindParameter] = public_factory(
    BindParameter, ".sql.expression.bindparam"
)
select: Callable[..., Select] = public_factory(Select, ".sql.expression.select")
text = public_factory(TextClause._create_text, ".sql.expression.text")
table: Callable[..., TableClause] = public_factory(TableClause, ".sql.expression.table")
column: Callable[..., ColumnClause] = public_factory(
    ColumnClause, ".sql.expression.column"
)
over: Callable[..., Over] = public_factory(Over, ".sql.expression.over")
within_group: Callable[..., WithinGroup] = public_factory(
    WithinGroup, ".sql.expression.within_group"
)
label: Callable[..., Label] = public_factory(Label, ".sql.expression.label")
case: Callable[..., Case] = public_factory(Case, ".sql.expression.case")
cast: Callable[..., Cast] = public_factory(Cast, ".sql.expression.cast")
cte = public_factory(CTE._factory, ".sql.expression.cte")
extract: Callable[..., Extract] = public_factory(Extract, ".sql.expression.extract")
tuple_: Callable[..., Tuple] = public_factory(Tuple, ".sql.expression.tuple_")
except_ = public_factory(CompoundSelect._create_except, ".sql.expression.except_")
except_all = public_factory(
    CompoundSelect._create_except_all, ".sql.expression.except_all"
)
intersect = public_factory(CompoundSelect._create_intersect, ".sql.expression.intersect")
intersect_all = public_factory(
    CompoundSelect._create_intersect_all, ".sql.expression.intersect_all"
)
union = public_factory(CompoundSelect._create_union, ".sql.expression.union")
union_all = public_factory(CompoundSelect._create_union_all, ".sql.expression.union_all")
exists = public_factory(Exists, ".sql.expression.exists")
nullsfirst = public_factory(
    UnaryExpression._create_nullsfirst, ".sql.expression.nullsfirst"
)
nullslast = public_factory(UnaryExpression._create_nullslast, ".sql.expression.nullslast")
asc = public_factory(UnaryExpression._create_asc, ".sql.expression.asc")
desc = public_factory(UnaryExpression._create_desc, ".sql.expression.desc")
distinct = public_factory(UnaryExpression._create_distinct, ".sql.expression.distinct")
type_coerce: Callable[..., TypeCoerce] = public_factory(
    TypeCoerce, ".sql.expression.type_coerce"
)
true = public_factory(True_._instance, ".sql.expression.true")
false = public_factory(False_._instance, ".sql.expression.false")
null = public_factory(Null._instance, ".sql.expression.null")
join = public_factory(Join._create_join, ".sql.expression.join")
outerjoin = public_factory(Join._create_outerjoin, ".sql.expression.outerjoin")
insert: Callable[..., Insert] = public_factory(Insert, ".sql.expression.insert")
update: Callable[..., Update] = public_factory(Update, ".sql.expression.update")
delete: Callable[..., Delete] = public_factory(Delete, ".sql.expression.delete")
funcfilter: Callable[..., FunctionFilter] = public_factory(
    FunctionFilter, ".sql.expression.funcfilter"
)
_Executable = Executable
_BindParamClause = BindParameter
_Label = Label
_SelectBase = SelectBase
_BinaryExpression = BinaryExpression
_Cast = Cast
_Null = Null
_False = False_
_True = True_
_TextClause = TextClause
_UnaryExpression = UnaryExpression
_Case = Case
_Tuple = Tuple
_Over = Over
_Generative = Generative
_TypeClause = TypeClause
_Extract = Extract
_Exists = Exists
_Grouping = Grouping
_FromGrouping = FromGrouping
_ScalarSelect = ScalarSelect

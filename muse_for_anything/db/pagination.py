from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, TypeVar, Union
from dataclasses import dataclass
from sqlalchemy.sql.expression import asc, desc
from sqlalchemy.sql import func, column
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.selectable import CTE

from .db import DB, MODEL
from .models.model_helpers import IdMixin


M = TypeVar("M", bound=MODEL)


@dataclass
class PageInfo:
    """Dataclass for holding information about a page.

    Cursor: the cursor id of the row directly before the page
    Page: the page number (starting with page 1)
    Row: the first row number of the (first item on the) page
    """

    cursor: Union[str, int]
    page: int
    row: int


@dataclass
class PaginationInfo:
    """Dataclass holding pagination information."""

    collection_size: int
    cursor_row: int
    cursor_page: int
    surrounding_pages: List[PageInfo]
    last_page: Optional[PageInfo]


def get_page_info(
    model: Type[M],
    cursor_column: Column,
    sortables: List[Column],
    cursor: Optional[Union[str, int]],
    sort: str,
    item_count: int = 50,
    surrounding_pages: int = 5,
    filter_criteria: Sequence[Any] = tuple(),
) -> PaginationInfo:
    if item_count is None:
        item_count = 50

    sort_columns: Dict[str, Column] = {c.name: c for c in sortables}

    if issubclass(model, IdMixin):
        sort_columns["id"] = model.id

    sort_column_name = sort.lstrip("+-")
    sort_direction: Any = desc if sort.startswith("-") else asc

    order_by = sort_direction(sort_columns[sort_column_name])
    row_numbers: Any = func.row_number().over(order_by=order_by)

    collection_size: int = (
        model.query.filter(*filter_criteria).enable_eagerloads(False).count()
    )

    if collection_size <= item_count:
        return PaginationInfo(
            collection_size=collection_size,
            cursor_row=0,
            cursor_page=1,
            surrounding_pages=[],
            last_page=PageInfo(0, 1, 0),
        )

    cursor_row: Union[int, Any] = 0

    if cursor is not None:
        cursor_row_cte: CTE = (
            DB.session.query(
                row_numbers.label("row"),
                cursor_column,
            )
            .filter(*filter_criteria)
            .from_self(column("row"))
            .filter(cursor_column == cursor)
            .cte("cursor_row")
        )
        cursor_row = cursor_row_cte.c.row

    page_rows = (
        DB.session.query(
            cursor_column,
            row_numbers.label("row"),
            (row_numbers / item_count).label("page"),
            (row_numbers % item_count).label("modulo"),
        )
        .filter(*filter_criteria)
        .order_by(column("row").asc())
        .cte("pages")
    )

    last_page = (
        DB.session.query(
            row_numbers.label("row"),
            (row_numbers / item_count).label("page"),
        )
        .filter(*filter_criteria)
        .order_by(column("row").desc())
        .limit(1)
        .cte("last-page")
    )

    pages = (
        DB.session.query(*page_rows.c)
        .only_return_tuples(True)
        .order_by(page_rows.c.row.asc())
        .filter(
            (page_rows.c.modulo == (cursor_row % item_count))  # only return page cursors
            & (  # but not for all pages
                (  # only return the +- surrounding pages pages
                    (page_rows.c.page >= ((cursor_row / item_count) - surrounding_pages))
                    & (
                        page_rows.c.page
                        <= ((cursor_row / item_count) + surrounding_pages)
                    )
                )
                | (page_rows.c.page == last_page.c.page)  # also return last page
            )
        )
        .all()
    )

    context_pages, last_page, current_cursor_row, cursor_page = digest_pages(
        pages, cursor, surrounding_pages
    )

    return PaginationInfo(
        collection_size=collection_size,
        cursor_row=current_cursor_row,
        cursor_page=cursor_page,
        surrounding_pages=context_pages,
        last_page=last_page,
    )


def digest_pages(
    pages: List[Tuple[Union[str, int], int, int, int]],
    cursor: Optional[Union[str, int]],
    max_surrounding: int,
) -> Tuple[List[PageInfo], Optional[PageInfo], int, int]:
    """Parse the page list from sql and generate PageInfo objects with the correct numbering.
    Also seperate last page from the list if outside of max_surrounding pages bound."""
    surrounding_pages = []
    last_page = None
    cursor_row = 0
    cursor_page = 1
    if not pages:
        return surrounding_pages, last_page, cursor_row, cursor_page
    current_count = 0
    for page in pages:
        if cursor is not None and str(page[0]) == str(cursor):
            current_count = 0
            cursor_row = page[1]
            cursor_page = page[2] + 1
            continue
        current_count += 1
        if current_count <= max_surrounding:
            surrounding_pages.append(PageInfo(page[0], page[2] + 1, page[1] + 1))
    last_page = pages[-1]
    return (
        surrounding_pages,
        PageInfo(last_page[0], last_page[2] + 1, last_page[1] + 1),
        cursor_row,
        cursor_page,
    )

from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, TypeVar, Union
from dataclasses import dataclass
from sqlalchemy.sql.expression import asc, desc, or_, and_
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
    page_items_query: Query


def get_page_info(
    model: Type[M],
    cursor_column: Column,
    sortables: List[Column],
    cursor: Optional[Union[str, int]],
    sort: str,
    item_count: int = 25,
    surrounding_pages: int = 5,
    filter_criteria: Sequence[Any] = tuple(),
) -> PaginationInfo:
    if item_count is None:
        item_count = 25

    sort_columns: Dict[str, Column] = {c.name: c for c in sortables}

    if issubclass(model, IdMixin):
        sort_columns["id"] = model.id

    sort_column_name = sort.lstrip("+-")
    sort_direction: Any = desc if sort.startswith("-") else asc

    sort_column = sort_columns[sort_column_name]
    if "collate" in sort_column.info:
        order_by = sort_direction(
            sort_columns[sort_column_name].collate(sort_column.info["collate"])
        )
    else:
        order_by = sort_direction(sort_columns[sort_column_name])
    row_numbers: Any = func.row_number().over(order_by=order_by)

    query_filter: Any = and_(*filter_criteria)

    collection_size: int = (
        model.query.filter(query_filter).enable_eagerloads(False).count()
    )

    if cursor is not None:
        # set cursor to none if no cursor is not found
        cursor = (
            # a query with exists is more complex than this
            DB.session.query(
                cursor_column,
            )
            .filter(cursor_column == cursor)
            .scalar()  # none or value of the cursor
        )

    item_query: Query = model.query.filter(query_filter).order_by(order_by)

    if collection_size <= item_count:
        return PaginationInfo(
            collection_size=collection_size,
            cursor_row=0,
            cursor_page=1,
            surrounding_pages=[],
            last_page=PageInfo(0, 1, 0),
            page_items_query=item_query.limit(item_count),
        )

    cursor_row: Union[int, Any] = 0

    if cursor is not None:
        # always include cursor row
        query_filter = or_(cursor_column == cursor, and_(*filter_criteria))
        item_query = model.query.filter(query_filter).order_by(order_by)
        cursor_row_cte: CTE = (
            DB.session.query(
                row_numbers.label("row"),
                cursor_column,
            )
            .filter(query_filter)
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
        .filter(query_filter)
        .order_by(column("row").asc())
        .cte("pages")
    )

    last_page = (
        DB.session.query(
            row_numbers.label("row"),
            (row_numbers / item_count).label("page"),
        )
        .filter(query_filter)
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
                | (
                    page_rows.c.page >= (last_page.c.page - 1)
                )  # also return last 1-2 pages
            )
        )
        .all()
    )

    context_pages, last_page, current_cursor_row, cursor_page = digest_pages(
        pages, cursor, surrounding_pages, collection_size
    )

    return PaginationInfo(
        collection_size=collection_size,
        cursor_row=current_cursor_row,
        cursor_page=cursor_page,
        surrounding_pages=context_pages,
        last_page=last_page,
        page_items_query=item_query.offset(current_cursor_row).limit(item_count),
    )


def digest_pages(
    pages: List[Tuple[Union[str, int], int, int, int]],
    cursor: Optional[Union[str, int]],
    max_surrounding: int,
    collection_size: int,
) -> Tuple[List[PageInfo], Optional[PageInfo], int, int]:
    """Parse the page list from sql and generate PageInfo objects with the correct numbering.
    Also seperate last page from the list if outside of max_surrounding pages bound."""
    CURSOR, ROW, PAGE, MODULO = 0, 1, 2, 3  # row name mapping of tuples in pages

    surrounding_pages: List[PageInfo] = []
    last_page = None
    cursor_row = 0
    cursor_page = 1
    if not pages:
        return surrounding_pages, None, cursor_row, cursor_page

    # offset page numbers from sql query to match correct pages
    # offset by 1 to start with page 1 (0 based in sql)
    # extra offset if first page contains < item_count items (then modulo col in sql is != 0)
    page_offset = 1 if pages and pages[0][MODULO] == 0 else 2

    # collect surrounding pages
    current_count = 0
    for page in pages:
        # test with >= because collection size may not inlcude the cursor item!
        if page[ROW] >= collection_size:
            break  # do not include an empty last page
        if cursor is not None and str(page[CURSOR]) == str(cursor):
            # half way point
            current_count = 0  # reset counter for pages on other side of cursor
            cursor_row = page[ROW]
            cursor_page = page[PAGE] + page_offset
            continue  # exclude the page of the cursor from surrounding pages
        current_count += 1
        if current_count <= max_surrounding:
            surrounding_pages.append(
                PageInfo(
                    cursor=page[CURSOR], page=page[PAGE] + page_offset, row=page[ROW] + 1
                )
            )

    # find last page
    last_page = pages[-1]
    # test with >= because collection size may not inlcude the cursor item!
    if last_page[ROW] >= collection_size:
        if len(pages) > 1:
            last_page = pages[-2]
    return (
        surrounding_pages,
        PageInfo(
            cursor=last_page[CURSOR],
            page=last_page[PAGE] + page_offset,
            row=last_page[ROW] + 1,
        ),
        cursor_row,
        cursor_page,
    )

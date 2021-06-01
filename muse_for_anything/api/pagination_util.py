"""Module containing helpers for pagination that are better suited for the view functions."""

from dataclasses import dataclass
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from flask_sqlalchemy.model import Model
from sqlalchemy.sql.schema import Column

from muse_for_anything.api.base_models import ApiLink, ApiObjectSchema, ApiResponse
from muse_for_anything.api.v1_api.request_helpers import (
    ApiResponseGenerator,
    LinkGenerator,
    PageResource,
    skip_slow_policy_checks_for_links_in_embedded_responses,
)
from muse_for_anything.db.models.model_helpers import IdMixin
from muse_for_anything.db.pagination import PaginationInfo, get_page_info


@dataclass
class PaginationOptions:
    """Class holding pagination options parsed from query args."""

    item_count: int = 25
    cursor: Optional[Union[str, int]] = None
    sort_order: str = "asc"
    sort_column: Optional[str] = None

    @property
    def sort(self) -> Optional[str]:
        """The sort query argument."""
        if self.sort_column:
            if self.sort_order == "asc":
                return self.sort_column
            elif self.sort_order == "desc":
                return f"-{self.sort_column}"

    def to_query_params(self, cursor: Optional[Union[str, int]] = "") -> Dict[str, str]:
        """Generate a dict containing the pagination options as query arguments.

        Args:
            cursor (Optional[Union[str, int]], optional): the cursor to overwrite the current cursor. Defaults to "".

        Returns:
            Dict[str, str]: the query arguments dict
        """
        params = {
            "item-count": str(self.item_count),
        }

        if cursor is None:
            pass  # no cursor
        elif cursor:
            params["cursor"] = str(cursor)
        elif self.cursor:
            params["cursor"] = str(self.cursor)

        sort = self.sort
        if sort:
            params["sort"] = sort

        return params


def prepare_pagination_query_args(
    *,
    cursor: Optional[Union[str, int]] = None,
    item_count: int = 25,
    sort: Optional[str] = None,
    _sort_default: str,
) -> PaginationOptions:
    """Prepare pagination query arguments into a PaginationOptions object.

    Args:
        _sort_default (str): a default sort string to apply if sort is None
        cursor (Optional[Union[str, int]], optional): the cursor of the current page. Defaults to None.
        item_count (int, optional): the current item count. Defaults to 25.
        sort (Optional[str], optional): the current sort argument. Defaults to None.

    Returns:
        PaginationOptions: the prepared PaginationOptions object
    """
    if sort is None and _sort_default is not None:
        sort = _sort_default
    sort_order = "asc"
    if sort and sort.startswith("-"):
        sort_order = "desc"
    sort_column = sort.lstrip("+-") if sort else None

    return PaginationOptions(
        sort_column=sort_column,
        sort_order=sort_order,
        item_count=item_count,
        cursor=cursor,
    )


T = TypeVar("T", bound=Model)


def default_get_page_info(
    model: Type[T],
    filter_criteria: Sequence[Any],
    pagination_options: PaginationOptions,
    sort_columns: Optional[Sequence[Column]] = None,
) -> PaginationInfo:
    """Get the pagination info from a model that extends IdMixin.

    Args:
        model (Type[T]): the db model; must also extend IdMixin!
        filter_criteria (Sequence[Any]): the filter criteria
        pagination_options (PaginationOptions): the pagination options object containing the page size, sort string and cursor
        sort_columns (Optional[Sequence[Column]], optional): a list of columns of the model that can be used to sort the items. Defaults to None.

    Raises:
        TypeError: if model is not an IdMixin
        KeyError: if the sort column could not be found in the model
        ValueError: if no sort column could be identified

    Returns:
        PaginationInfo: the pagination info
    """
    if not issubclass(model, IdMixin):
        raise TypeError(
            "Directly use get_page_info() for models that do not inherit from IdMixin!"
        )
    id_column = cast(IdMixin, model).id

    sort: str

    if not sort_columns:
        sort_col_name = pagination_options.sort_column
        if not sort_col_name:
            sort = "id"
        else:
            sort_column = getattr(model, sort_col_name, None)
            if sort_column is None:
                raise KeyError(f"No column with name '{sort_col_name}' found!", model)
            sort = pagination_options.sort
            assert sort is not None
            sort_columns = (sort_column,)

    if not sort_columns:
        raise ValueError("Could not identify sort columns!", model, pagination_options)

    return get_page_info(
        model,
        id_column,
        sort_columns,
        pagination_options.cursor,
        pagination_options.sort,
        pagination_options.item_count,
        filter_criteria=filter_criteria,
    )


def dump_embedded_page_items(
    items: Sequence[Any],
    schema: ApiObjectSchema,
    link_to_relations: Optional[Iterable[str]],
) -> Tuple[List[ApiResponse], List[ApiLink]]:
    """Dump the embedded page items as ApiResources with the given schema.

    Args:
        items (Sequence[Any]): the list of items to process
        schema (ApiObjectSchema): the schema to dump the items with
        link_to_relations (Optional[Iterable[str]]): the extra link to relations to pass to the api response generator

    Returns:
        Tuple[List[ApiResponse], List[ApiLink]]: the embedded resource list, the self links of the embedded resources
    """

    embedded_items: List[ApiResponse] = []
    links: List[ApiLink] = []

    with skip_slow_policy_checks_for_links_in_embedded_responses():
        for item in items:
            response = ApiResponseGenerator.get_api_response(
                item, link_to_relations=link_to_relations
            )
            if response:
                links.append(response.data.self)
                response.data = schema.dump(response.data)
                embedded_items.append(response)

    return embedded_items, links


def generate_page_links(
    resource: PageResource,
    pagination_info: PaginationInfo,
    pagination_options: PaginationOptions,
) -> List[ApiLink]:
    """Generate page links from pagination info and options for the given page resource.

    Args:
        resource (PageResource): the base page resource
        pagination_info (PaginationInfo): the pagination info containing first last and surrounding pages
        pagination_options (PaginationOptions): the pagination options that were used to generate the pagination info

    Returns:
        List[ApiLink]: a list of api links to the last page and the surrounding pages
    """
    extra_links: List[ApiLink] = []
    if pagination_info.last_page is not None:
        if pagination_info.cursor_page != pagination_info.last_page.page:
            # only if current page is not last page

            extra_links.append(
                LinkGenerator.get_link_of(
                    resource.get_page(pagination_info.last_page.page),
                    query_params=pagination_options.to_query_params(
                        cursor=pagination_info.last_page.cursor
                    ),
                )
            )

    for page in pagination_info.surrounding_pages:
        if page == pagination_info.last_page:
            continue  # link already included

        extra_links.append(
            LinkGenerator.get_link_of(
                resource.get_page(page.page),
                query_params=pagination_options.to_query_params(cursor=page.cursor),
            )
        )
    return extra_links

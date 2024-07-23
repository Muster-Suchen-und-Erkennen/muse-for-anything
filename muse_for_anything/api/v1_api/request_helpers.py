"""Utilities for creating resource keys, links, data and full api responses."""

from dataclasses import dataclass, field
from muse_for_anything.oso_helpers import FLASK_OSO, OsoResource, get_oso_resource_type
from typing import Any, Dict, Iterable, List, Optional, Type, Union, Tuple, Sequence
from itertools import chain
from contextlib import contextmanager

from sqlalchemy.exc import ArgumentError
from muse_for_anything.api.base_models import (
    ApiLink,
    ApiResponse,
    BaseApiObject,
    CollectionResource as CollectionResponse,
    CursorPage,
    CollectionFilter,
)


@dataclass()
class CollectionResource:
    resource_type: Type
    resource: Optional[Any] = None
    collection_size: int = 0
    item_links: Optional[Sequence[ApiLink]] = None
    filters: Sequence[CollectionFilter] = tuple()


@dataclass()
class PageResource:
    resource_type: Type
    resource: Optional[Any] = None
    page_number: int = 1
    active_page: int = 1
    last_page: Optional[int] = None
    collection_size: int = 0
    item_links: Optional[Sequence[ApiLink]] = None
    extra_arguments: Dict[str, Any] = field(default_factory=dict)
    filters: Sequence[CollectionFilter] = tuple()

    @property
    def is_first(self) -> bool:
        return self.page_number == 1

    @property
    def is_last(self) -> bool:
        return self.last_page is not None and self.page_number == self.last_page

    @property
    def is_prev(self) -> bool:
        return self.page_number + 1 == self.active_page

    @property
    def is_next(self) -> bool:
        return self.page_number - 1 == self.active_page

    def get_page(self, page_number: int):
        return PageResource(
            page_number=page_number,
            resource_type=self.resource_type,
            resource=self.resource,
            active_page=self.active_page,
            last_page=self.last_page,
            collection_size=self.collection_size,
            extra_arguments=self.extra_arguments,
        )


def query_params_to_api_key(query_params: Dict[str, str]) -> Dict[str, str]:
    key = {}
    for k, v in query_params.items():
        key[f"?{k}"] = str(v)
    return key


class KeyGenerator:

    __generators: Dict[Type, "KeyGenerator"] = {}

    __generators_for_page_resources: Dict[Type, "KeyGenerator"] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        resource_type = kwargs.pop("resource_type", None)
        if resource_type is None:
            raise ArgumentError(
                "A key generator class must provide a valid resource type!"
            )
        is_page = kwargs.pop("page", False)
        generators = (
            KeyGenerator.__generators_for_page_resources
            if is_page
            else KeyGenerator.__generators
        )
        if resource_type in generators:
            raise ArgumentError(
                f"The resource type '{resource_type}' already has a key generator!"
                f"\t(registered: {generators[resource_type]}, offending class: {cls})"
            )
        generators[resource_type] = cls()

    @staticmethod
    def generate_key(resource, query_params: Optional[Dict[str, str]] = None):
        key: Dict[str, str]
        if query_params:
            key = query_params_to_api_key(query_params=query_params)
        else:
            key = {}
        if isinstance(resource, (PageResource, CollectionResource)):
            generator = KeyGenerator.__generators_for_page_resources.get(
                resource.resource_type
            )
        else:
            generator = KeyGenerator.__generators.get(type(resource))
        if generator:
            return generator.update_key(key, resource)
        return key

    def update_key(self, key: Dict[str, str], resource) -> Dict[str, str]:
        raise NotImplementedError()


LINK_ACTIONS = {"create", "update", "delete", "restore", "export"}


@contextmanager
def skip_slow_policy_checks_for_links_in_embedded_responses():
    """Context generator to temporarily disable slow policy checks for links in embedded resources.

    USE SPARINGLY and ONLY for EMBEDDED resources! NEVER use this for the main resource!
    """
    LinkGenerator.skip_slow_policy_checks = True
    try:
        yield
    finally:
        LinkGenerator.skip_slow_policy_checks = False


class LinkGenerator:

    __generators: Dict[Union[None, Type, Tuple[Type, str]], "LinkGenerator"] = {}

    __generators_for_page_resources: Dict[
        Union[None, Type, Tuple[Type, str]], "LinkGenerator"
    ] = {}

    # only ever change this to True with the contextmanager above!!!!!!!
    skip_slow_policy_checks: bool = False

    def __init_subclass__(cls, **kwargs) -> None:
        resource_type: Type = kwargs.pop("resource_type", None)
        relation: str = kwargs.pop("relation", None)
        key = resource_type if relation is None else (resource_type, relation)
        is_page = kwargs.pop("page", False)
        generators = (
            LinkGenerator.__generators_for_page_resources
            if is_page
            else LinkGenerator.__generators
        )
        if key in generators:
            raise ArgumentError(
                f"The resource type '{resource_type}' with action '{relation}' already has a link generator!"
                f"\t(registered: {generators[key]}, offending class: {cls})"
            )
        generators[key] = cls()

    @staticmethod
    def _get_generators_and_resource_type(resource):
        is_page = isinstance(resource, (PageResource, CollectionResource))

        generators = (
            LinkGenerator.__generators_for_page_resources
            if is_page
            else LinkGenerator.__generators
        )
        resource_type: Type = resource.resource_type if is_page else type(resource)
        return generators, resource_type

    @staticmethod
    def get_links_for(
        resource,
        relations: Optional[Iterable[str]] = None,
        include_default_relations: bool = True,
    ):
        links: List[ApiLink] = []

        generators, resource_type = LinkGenerator._get_generators_and_resource_type(
            resource
        )
        link_relations: Iterable[str] = relations if relations is not None else []
        if include_default_relations:
            link_relations = chain(link_relations, ("up", *LINK_ACTIONS))
        for rel in link_relations:
            generator = generators.get((resource_type, rel))
            if generator is not None:
                link = generator.generate_link(resource)
                if link is not None:
                    links.append(link)

        return links

    @staticmethod
    def get_link_of(
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        extra_relations: Optional[Sequence[str]] = None,
        for_relation: Optional[str] = None,
        ignore_deleted: bool = False,
    ) -> ApiLink:
        is_page = isinstance(resource, PageResource)

        generators, resource_type = LinkGenerator._get_generators_and_resource_type(
            resource
        )
        generator = (
            generators.get(resource_type)
            if for_relation is None
            else generators.get((resource_type, for_relation))
        )
        if generator is not None:
            link = generator.generate_link(
                resource, query_params=query_params, ignore_deleted=ignore_deleted
            )
            if link is None:
                return None
            extra_rels: List[str] = []
            if is_page and for_relation is None:
                if resource.is_first:
                    extra_rels.append("first")
                if resource.is_last:
                    extra_rels.append("last")
                if resource.is_prev:
                    extra_rels.append("prev")
                if resource.is_next:
                    extra_rels.append("next")
                extra_rels.append(f"page-{resource.page_number}")
            if extra_relations:
                link.rel = (*link.rel, *extra_rels, *extra_relations)
            else:
                link.rel = (*link.rel, *extra_rels)
            return link
        raise KeyError(
            f"No link generator found for resource type '{resource_type}' (for rel '{'self' if for_relation is None else for_relation}')."
        )

    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        raise NotImplementedError()


class ApiObjectGenerator:

    __generators: Dict[Type, "ApiObjectGenerator"] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        resource_type: Type = kwargs.pop("resource_type", None)

        generators = ApiObjectGenerator.__generators
        if resource_type in generators:
            raise ArgumentError(
                f"The resource type '{resource_type}' already has an api object dataclass generator!"
                f"\t(registered: {generators[resource_type]}, offending class: {cls})"
            )
        generators[resource_type] = cls()

    @staticmethod
    def get_api_object(
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[BaseApiObject]:
        resource_type = type(resource)

        generators = ApiObjectGenerator.__generators

        generator = generators.get(resource_type)
        if generator is None:
            return ApiObjectGenerator.default_generate_api_object(
                resource, query_params=query_params
            )

        return generator.generate_api_object(resource, query_params=query_params)

    @staticmethod
    def default_generate_api_object(
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[BaseApiObject]:
        return BaseApiObject(
            self=LinkGenerator.get_link_of(
                resource, query_params=query_params, ignore_deleted=True
            )
        )

    def generate_api_object(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[BaseApiObject]:
        raise NotImplementedError()


class CollectionResourceApiObjectGenerator(
    ApiObjectGenerator, resource_type=CollectionResource
):
    def generate_api_object(
        self,
        resource: CollectionResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[BaseApiObject]:
        assert isinstance(resource, CollectionResource)

        if not FLASK_OSO.is_allowed(
            OsoResource(
                get_oso_resource_type(resource.resource_type),
                is_collection=True,
                parent_resource=resource.resource,
            ),
            action="GET",
        ):
            return

        return CollectionResponse(
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
            collection_size=resource.collection_size,
            items=(resource.item_links if resource.item_links else []),
            filters=resource.filters,
        )


class CursorPageApiObjectGenerator(ApiObjectGenerator, resource_type=PageResource):
    def generate_api_object(
        self,
        resource: PageResource,
        *,
        query_params: Optional[Dict[str, str]] = None,
    ) -> Optional[BaseApiObject]:
        assert isinstance(resource, PageResource)

        if not FLASK_OSO.is_allowed(
            OsoResource(
                get_oso_resource_type(resource.resource_type),
                is_collection=True,
                parent_resource=resource.resource,
            ),
            action="GET",
        ):
            return

        return CursorPage(
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
            collection_size=resource.collection_size,
            page=resource.page_number,
            items=(resource.item_links if resource.item_links else []),
            filters=resource.filters,
        )


class ApiResponseGenerator:

    __generators: Dict[Type, "ApiResponseGenerator"] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        resource_type: Type = kwargs.pop("resource_type", None)
        generators = ApiResponseGenerator.__generators
        if resource_type in generators:
            raise ArgumentError(
                f"The resource type '{resource_type}' already has an api response dataclass generator!"
                f"\t(registered: {generators[resource_type]}, offending class: {cls})"
            )
        generators[resource_type] = cls()

    @staticmethod
    def get_api_response(
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        link_to_relations: Optional[Iterable[str]] = None,
        include_default_relations: bool = True,
        extra_links: Optional[Sequence[ApiLink]] = None,
        extra_embedded: Optional[Sequence[ApiResponse]] = None,
    ) -> Optional[ApiResponse]:
        resource_type = type(resource)

        generators = ApiResponseGenerator.__generators
        generator = generators.get(resource_type)

        response: Optional[ApiResponse]

        if generator is None:
            response = ApiResponseGenerator.default_generate_api_response(
                resource,
                query_params=query_params,
                link_to_relations=link_to_relations,
                include_default_relations=include_default_relations,
            )
        else:
            response = generator.generate_api_response(
                resource,
                query_params=query_params,
                link_to_relations=link_to_relations,
                include_default_relations=include_default_relations,
            )

        if response is None:
            return

        if extra_links:
            response.links = (*response.links, *extra_links)
        if extra_embedded:
            if response.embedded:
                response.embedded = (*response.embedded, *extra_embedded)
            else:
                response.embedded = extra_embedded
        return response

    @staticmethod
    def default_generate_api_response(
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        link_to_relations: Optional[Iterable[str]] = None,
        include_default_relations: bool = True,
    ) -> Optional[ApiResponse]:
        return ApiResponse(
            links=LinkGenerator.get_links_for(
                resource,
                relations=link_to_relations,
                include_default_relations=include_default_relations,
            ),
            data=ApiObjectGenerator.get_api_object(resource, query_params=query_params),
        )

    def generate_api_response(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, str]] = None,
        link_to_relations: Optional[Iterable[str]] = None,
        include_default_relations: bool = True,
    ) -> Optional[ApiResponse]:
        raise NotImplementedError()

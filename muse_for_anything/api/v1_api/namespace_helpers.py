from flask_oso.flask_oso import FlaskOso
from muse_for_anything.db.models.taxonomies import Taxonomy
from muse_for_anything.db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectType,
)
from typing import Any, Dict, List, Optional, Union
from flask import url_for

from muse_for_anything.api.base_models import ApiLink, ApiResponse
from muse_for_anything.api.v1_api.models.ontology import NamespaceData, NamespaceSchema
from muse_for_anything.db.models.namespace import Namespace


from .request_helpers import ApiObjectGenerator, KeyGenerator, LinkGenerator, PageResource

from ...oso_helpers import FLASK_OSO, OsoResource

NAMESPACE_EXTRA_LINK_RELATIONS = ("ont-object", "ont-type", "ont-taxonomy")


class NamespacePageKeyGenerator(KeyGenerator, resource_type=Namespace, page=True):
    def update_key(self, key: Dict[str, str], resource: PageResource) -> Dict[str, str]:
        assert isinstance(resource, PageResource)
        assert resource.resource_type == Namespace
        return key


class NamespacePageLinkGenerator(LinkGenerator, resource_type=Namespace, page=True):
    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]],
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if query_params is None:
            query_params = {"item-count": 50}
        return ApiLink(
            href=url_for("api-v1.NamespacesView", **query_params, _external=True),
            rel=("collection", "page"),
            resource_type="ont-namespace",
            resource_key=KeyGenerator.generate_key(resource, query_params=query_params),
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
        )


class NamespacePageCreateNamespaceLinkGenerator(
    LinkGenerator, resource_type=Namespace, page=True, relation="create"
):
    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(OsoResource("ont-namespace"), action="CREATE"):
            return
        link = LinkGenerator.get_link_of(resource, query_params=query_params)
        link.rel = ("create", "post")
        return link


class NamespaceKeyGenerator(KeyGenerator, resource_type=Namespace):
    def update_key(self, key: Dict[str, str], resource: Namespace) -> Dict[str, str]:
        assert isinstance(resource, Namespace)
        key["namespaceId"] = str(resource.id)
        return key


class NamespaceSelfLinkGenerator(LinkGenerator, resource_type=Namespace):
    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return ApiLink(
            href=url_for(
                "api-v1.NamespaceView", namespace=str(resource.id), _external=True
            ),
            rel=tuple(),
            resource_type="ont-namespace",
            resource_key=KeyGenerator.generate_key(resource),
            schema=url_for("api-v1.ApiSchemaView", schema_id="Namespace", _external=True),
            name=resource.name,
        )


class NamespaceApiObjectGenerator(ApiObjectGenerator, resource_type=Namespace):
    def generate_api_object(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
    ) -> Optional[NamespaceData]:
        assert isinstance(resource, Namespace)

        if not FLASK_OSO.is_allowed(resource, action="GET"):
            return

        return NamespaceData(
            self=LinkGenerator.get_link_of(resource, query_params=query_params),
            name=resource.name,
            description=resource.description,
            created_on=resource.created_on,
            updated_on=resource.updated_on,
            deleted_on=resource.deleted_on,
        )


class NamespaceUpLinkGenerator(LinkGenerator, resource_type=Namespace, relation="up"):
    def generate_link(
        self,
        resource,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            PageResource(Namespace, page_number=1),
            extra_relations=("up",),
        )


class NamespaceObjectsNavLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation="ont-object"
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            PageResource(OntologyObject, resource=resource, page_number=1),
            extra_relations=("nav",),
        )


class NamespaceTypesNavLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation="ont-type"
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            PageResource(OntologyObjectType, resource=resource, page_number=1),
            extra_relations=("nav",),
        )


class NamespaceTaxonomiesNavLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation="ont-taxonomy"
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        return LinkGenerator.get_link_of(
            PageResource(Taxonomy, resource=resource, page_number=1),
            extra_relations=("nav",),
        )


class CreateNamespaceLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation="create"
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Namespace)
        if not FLASK_OSO.is_allowed(OsoResource("ont-namespace"), action="CREATE"):
            return
        link = LinkGenerator.get_link_of(
            PageResource(Namespace, page_number=1),
            query_params={},
            ignore_deleted=ignore_deleted,
        )
        link.rel = ("create", "post")
        return link


class UpdateNamespaceLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation="update"
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        assert isinstance(resource, Namespace)
        if not FLASK_OSO.is_allowed(resource, action="EDIT"):
            return  # not allowed
        if not ignore_deleted:
            if resource.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = ("update", "put")
        return link


class DeleteNamespaceLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation="delete"
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(resource, action="DELETE"):
            return  # not allowed
        if not ignore_deleted:
            if resource.is_deleted:
                return  # deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = ("delete",)
        return link


class RestoreNamespaceLinkGenerator(
    LinkGenerator, resource_type=Namespace, relation="restore"
):
    def generate_link(
        self,
        resource: Namespace,
        *,
        query_params: Optional[Dict[str, Union[str, int, float]]] = None,
        ignore_deleted: bool = False,
    ) -> Optional[ApiLink]:
        if not FLASK_OSO.is_allowed(resource, action="RESTORE"):
            return  # not allowed
        if not ignore_deleted:
            if not resource.is_deleted:
                return  # not deleted
        link = LinkGenerator.get_link_of(resource, ignore_deleted=ignore_deleted)
        link.rel = ("restore", "post")
        return link


def query_params_to_api_key(query_params: Dict[str, Union[str, int]]) -> Dict[str, str]:
    key = {}
    for k, v in query_params.items():
        key[f'?{k.replace("_", "-")}'] = str(v)
    return key

"""Module containing the taxonomy items API endpoints of the v1 API."""

from datetime import datetime

from sqlalchemy.sql.schema import Sequence
from muse_for_anything.db.models.taxonomies import (
    Taxonomy,
    TaxonomyItem,
    TaxonomyItemRelation,
    TaxonomyItemVersion,
)

from marshmallow.utils import INCLUDE
from flask_babel import gettext
from muse_for_anything.api.util import template_url_for
from typing import Any, Callable, Dict, List, Optional, Union, cast
from flask.helpers import url_for
from flask.views import MethodView
from sqlalchemy.sql.expression import asc, desc, literal
from sqlalchemy.orm.query import Query
from sqlalchemy.orm import selectinload
from flask_smorest import abort
from http import HTTPStatus

from .root import API_V1
from ..base_models import (
    ApiLink,
    ApiResponse,
    ChangedApiObject,
    ChangedApiObjectSchema,
    CursorPage,
    CursorPageArgumentsSchema,
    CursorPageSchema,
    DynamicApiResponseSchema,
    NewApiObject,
    NewApiObjectSchema,
)
from ...db.db import DB
from ...db.pagination import get_page_info
from ...db.models.namespace import Namespace
from ...db.models.ontology_objects import OntologyObjectType, OntologyObjectTypeVersion

from .models.ontology import (
    TaxonomyItemRelationPostSchema,
    TaxonomyItemRelationSchema,
    TaxonomyItemSchema,
    TaxonomySchema,
)

from .namespace_helpers import (
    query_params_to_api_key,
)

from .taxonomy_helpers import (
    action_links_for_taxonomy_item,
    action_links_for_taxonomy_item_relation,
    create_action_link_for_taxonomy_item_page,
    create_action_link_for_taxonomy_item_relation_page,
    nav_links_for_taxonomy_item,
    taxonomy_item_relation_to_api_link,
    taxonomy_item_relation_to_api_response,
    taxonomy_item_relation_to_taxonomy_item_relation_data,
    taxonomy_item_to_api_link,
    taxonomy_item_to_api_response,
    taxonomy_item_to_taxonomy_item_data,
    taxonomy_to_api_response,
    taxonomy_to_items_links,
    taxonomy_to_taxonomy_data,
)


@API_V1.route(
    "/namespaces/<string:namespace>/taxonomies/<string:taxonomy>/items/<string:taxonomy_item>/"
)
class TaxonomyItemView(MethodView):
    """Endpoint for a single taxonomy item."""

    def _check_path_params(self, namespace: str, taxonomy: str, taxonomy_item: str):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not taxonomy or not taxonomy.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy id has the wrong format!"),
            )
        if not taxonomy_item or not taxonomy_item.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy item id has the wrong format!"),
            )

    def _get_taxonomy_item(
        self, namespace: str, taxonomy: str, taxonomy_item: str
    ) -> TaxonomyItem:
        namespace_id = int(namespace)
        taxonomy_id = int(taxonomy)
        taxonomy_item_id = int(taxonomy_item)
        found_taxonomy_item: Optional[TaxonomyItem] = (
            TaxonomyItem.query.options(selectinload(TaxonomyItem.current_ancestors))
            .filter(
                TaxonomyItem.id == taxonomy_item_id,
                TaxonomyItem.taxonomy_id == taxonomy_id,
            )
            .first()
        )

        if (
            found_taxonomy_item is None
            or found_taxonomy_item.taxonomy.namespace_id != namespace_id
        ):
            abort(HTTPStatus.NOT_FOUND, message=gettext("Taxonomy item not found."))
        return found_taxonomy_item  # is not None because abort raises exception

    def _check_if_taxonomy_modifiable(self, taxonomy: Taxonomy):
        if taxonomy.namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )
        if taxonomy.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy is marked as deleted and cannot be modified further."
                ),
            )

    def _check_if_modifiable(self, taxonomy_item: TaxonomyItem):
        self._check_if_taxonomy_modifiable(taxonomy=taxonomy_item.taxonomy)
        if taxonomy_item.deleted_on is not None:
            # cannot modify deleted taxonomy!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy item is marked as deleted and cannot be modified further."
                ),
            )

    @API_V1.response(DynamicApiResponseSchema(TaxonomyItemSchema()))
    def get(self, namespace: str, taxonomy: str, taxonomy_item: str, **kwargs: Any):
        """Get a single taxonomy item."""
        self._check_path_params(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        found_taxonomy_item: TaxonomyItem = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )

        embedded: List[ApiResponse] = []

        for relation in found_taxonomy_item.current_ancestors:
            embedded.append(taxonomy_item_to_api_response(relation.taxonomy_item_source))
        for relation in found_taxonomy_item.current_related:
            embedded.append(taxonomy_item_relation_to_api_response(relation))
            embedded.append(taxonomy_item_to_api_response(relation.taxonomy_item_target))

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for(
                        "api-v1.NamespacesView",
                        _external=True,
                        item_count=50,
                        sort="name",
                    ),
                    rel=("first", "page", "collection", "nav"),
                    resource_type="ont-namespace",
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                *nav_links_for_taxonomy_item(found_taxonomy_item),
                *action_links_for_taxonomy_item(found_taxonomy_item),
            ],
            embedded=embedded,
            data=taxonomy_item_to_taxonomy_item_data(found_taxonomy_item),
        )

    @API_V1.arguments(TaxonomyItemSchema())
    @API_V1.response(DynamicApiResponseSchema(NewApiObjectSchema()))
    def put(self, data, namespace: str, taxonomy: str, taxonomy_item: str):
        """Update a taxonomy item."""
        self._check_path_params(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        found_taxonomy_item: TaxonomyItem = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        self._check_if_modifiable(found_taxonomy_item)

        taxonomy_item_version = TaxonomyItemVersion(
            taxonomy_item=found_taxonomy_item,
            version=found_taxonomy_item.current_version.version + 1,
            name=data["name"],
            description=data.get("description", ""),
            sort_key=data.get("sort_key", 10),
        )
        found_taxonomy_item.current_version = taxonomy_item_version
        DB.session.add(found_taxonomy_item)
        DB.session.add(taxonomy_item_version)
        DB.session.commit()

        taxonomy_item_link = taxonomy_item_to_taxonomy_item_data(found_taxonomy_item).self
        taxonomy_item_data = taxonomy_item_to_api_response(found_taxonomy_item)

        return ApiResponse(
            links=[taxonomy_item_link],
            embedded=[taxonomy_item_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyItemView",
                        namespace=namespace,
                        taxonomy=taxonomy,
                        taxonomy_item=taxonomy_item,
                        _external=True,
                    ),
                    rel=(
                        "update",
                        "put",
                        "ont-taxonomy-item",
                    ),
                    resource_type="changed",
                ),
                changed=taxonomy_item_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def post(self, namespace: str, taxonomy: str, taxonomy_item: str):  # restore action
        """Restore a deleted taxonomy item."""
        self._check_path_params(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        found_taxonomy_item: TaxonomyItem = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        self._check_if_taxonomy_modifiable(found_taxonomy_item.taxonomy)

        changed_links: List[ApiLink] = []
        embedded: List[ApiResponse] = []

        # only actually restore when not already restored
        if found_taxonomy_item.deleted_on is not None:
            # restore taxonomy item
            deleted_timestamp = found_taxonomy_item.deleted_on
            found_taxonomy_item.deleted_on = None
            # also restore relations
            ancestors: Sequence[TaxonomyItemRelation] = TaxonomyItemRelation.query.filter(
                TaxonomyItemRelation.taxonomy_item_target_id == found_taxonomy_item.id,
                TaxonomyItemRelation.deleted_on == deleted_timestamp,
            ).all()
            ancestor_ids = set()
            relation: TaxonomyItemRelation
            for relation in ancestors:
                if relation.taxonomy_item_source.deleted_on is not None:
                    continue  # do not restore relations to deleted items
                ancestor_ids.add(relation.taxonomy_item_source_id)
                relation.deleted_on = None
                DB.session.add(relation)

            def produces_circle(relation: TaxonomyItemRelation) -> bool:
                if relation.taxonomy_item_target_id in ancestor_ids:
                    return True
                for rel in relation.taxonomy_item_target.current_related:
                    if produces_circle(rel):
                        return True
                return False

            children: Sequence[TaxonomyItemRelation] = TaxonomyItemRelation.query.filter(
                TaxonomyItemRelation.taxonomy_item_source_id == found_taxonomy_item.id,
                TaxonomyItemRelation.deleted_on == deleted_timestamp,
            ).all()
            for relation in children:
                if relation.taxonomy_item_target.deleted_on is not None:
                    continue  # do not restore relations to deleted items
                if produces_circle(relation):
                    continue
                relation.deleted_on = None
                DB.session.add(relation)
            DB.session.add(found_taxonomy_item)
            DB.session.commit()

            # add changed items to be embedded into the response
            for relation in found_taxonomy_item.current_ancestors:
                changed_links.append(
                    taxonomy_item_to_api_link(relation.taxonomy_item_source)
                )
                embedded.append(
                    taxonomy_item_to_api_response(relation.taxonomy_item_source)
                )
            for relation in found_taxonomy_item.current_related:
                changed_links.append(taxonomy_item_relation_to_api_link(relation))
                embedded.append(taxonomy_item_relation_to_api_response(relation))
                changed_links.append(
                    taxonomy_item_to_api_link(relation.taxonomy_item_target)
                )
                embedded.append(
                    taxonomy_item_to_api_response(relation.taxonomy_item_target)
                )

        taxonomy_item_link = taxonomy_item_to_taxonomy_item_data(found_taxonomy_item).self
        taxonomy_item_data = taxonomy_item_to_api_response(found_taxonomy_item)

        taxonomy_link = taxonomy_to_taxonomy_data(found_taxonomy_item.taxonomy).self
        taxonomy_data = taxonomy_to_api_response(found_taxonomy_item.taxonomy)

        return ApiResponse(
            links=[taxonomy_item_link, taxonomy_link, *changed_links],
            embedded=[taxonomy_item_data, taxonomy_data, *embedded],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyItemView",
                        namespace=namespace,
                        taxonomy=taxonomy,
                        taxonomy_item=taxonomy_item,
                        _external=True,
                    ),
                    rel=(
                        "restore",
                        "post",
                        "ont-taxonomy-item",
                    ),
                    resource_type="changed",
                ),
                changed=taxonomy_item_link,
            ),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def delete(self, namespace: str, taxonomy: str, taxonomy_item: str):  # restore action
        """Delete a taxonomy item."""
        self._check_path_params(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        found_taxonomy_item: TaxonomyItem = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        self._check_if_taxonomy_modifiable(found_taxonomy_item.taxonomy)

        changed_links: List[ApiLink] = []
        embedded: List[ApiResponse] = []

        # only actually delete when not already deleted
        if found_taxonomy_item.deleted_on is not None:
            # delete taxonomy item
            deleted_timestamp = datetime.utcnow()
            found_taxonomy_item.deleted_on = deleted_timestamp
            # also delete incoming and outgoing relations to remove them
            # from relations of existing items
            ancestors = found_taxonomy_item.current_ancestors
            for relation in found_taxonomy_item.current_ancestors:
                relation.deleted_on = deleted_timestamp
                DB.session.add(relation)
            related = found_taxonomy_item.current_related
            for relation in found_taxonomy_item.current_related:
                relation.deleted_on = deleted_timestamp
                DB.session.add(relation)
            DB.session.add(found_taxonomy_item)
            DB.session.commit()

            # add changed items to be embedded into the response
            for relation in ancestors:
                changed_links.append(
                    taxonomy_item_to_api_link(relation.taxonomy_item_source)
                )
                embedded.append(
                    taxonomy_item_to_api_response(relation.taxonomy_item_source)
                )
            for relation in related:
                changed_links.append(taxonomy_item_relation_to_api_link(relation))
                embedded.append(taxonomy_item_relation_to_api_response(relation))
                changed_links.append(
                    taxonomy_item_to_api_link(relation.taxonomy_item_target)
                )
                embedded.append(
                    taxonomy_item_to_api_response(relation.taxonomy_item_target)
                )

        taxonomy_item_link = taxonomy_item_to_taxonomy_item_data(found_taxonomy_item).self
        taxonomy_item_data = taxonomy_item_to_api_response(found_taxonomy_item)

        taxonomy_link = taxonomy_to_taxonomy_data(found_taxonomy_item.taxonomy).self
        taxonomy_data = taxonomy_to_api_response(found_taxonomy_item.taxonomy)

        return ApiResponse(
            links=[taxonomy_item_link, taxonomy_link, *changed_links],
            embedded=[taxonomy_item_data, taxonomy_data, *embedded],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyItemView",
                        namespace=namespace,
                        taxonomy=taxonomy,
                        taxonomy_item=taxonomy_item,
                        _external=True,
                    ),
                    rel=(
                        "delete",
                        "ont-taxonomy-item",
                    ),
                    resource_type="changed",
                ),
                changed=taxonomy_item_link,
            ),
        )


@API_V1.route(
    "/namespaces/<string:namespace>/taxonomies/<string:taxonomy>/items/<string:taxonomy_item>/relations/"
)
class TaxonomyItemRelationsView(MethodView):
    """Endpoint for manipulating taxonomy item relations."""

    def _check_path_params(self, namespace: str, taxonomy: str, taxonomy_item: str):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not taxonomy or not taxonomy.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy id has the wrong format!"),
            )
        if not taxonomy_item or not taxonomy_item.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy item id has the wrong format!"),
            )

    def _get_taxonomy_item(
        self, namespace: str, taxonomy: str, taxonomy_item: str
    ) -> TaxonomyItem:
        namespace_id = int(namespace)
        taxonomy_id = int(taxonomy)
        taxonomy_item_id = int(taxonomy_item)
        found_taxonomy_item: Optional[TaxonomyItem] = TaxonomyItem.query.filter(
            TaxonomyItem.id == taxonomy_item_id,
            TaxonomyItem.taxonomy_id == taxonomy_id,
        ).first()

        if (
            found_taxonomy_item is None
            or found_taxonomy_item.taxonomy.namespace_id != namespace_id
        ):
            abort(HTTPStatus.NOT_FOUND, message=gettext("Taxonomy item not found."))
        return found_taxonomy_item  # is not None because abort raises exception

    def _check_if_modifiable(self, taxonomy_item: TaxonomyItem):
        taxonomy = taxonomy_item.taxonomy
        if taxonomy.namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )
        if taxonomy.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy is marked as deleted and cannot be modified further."
                ),
            )
        if taxonomy_item.deleted_on is not None:
            # cannot modify deleted taxonomy!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy item is marked as deleted and cannot be modified further."
                ),
            )

    def _check_item_circle(
        self,
        item_target: TaxonomyItem,
        item_source: TaxonomyItem,
        original_target: Optional[TaxonomyItem] = None,
    ):
        """Check for a path from target to source which would form a circular dependency. Abort if such a path is found!"""
        if original_target is None:
            original_target = item_target
        relation: TaxonomyItemRelation
        for relation in item_target.current_related:
            if relation.taxonomy_item_target.deleted_on is not None:
                continue  # exclude deleted items as targets
            if relation.taxonomy_item_target_id == item_source.id:
                abort(
                    HTTPStatus.CONFLICT,
                    message=gettext(
                        "Cannot add a relation from %(target)s to %(source)s as it would create a circle!",
                        target=original_target.name,
                        source=item_source.name,
                    ),
                )
            else:
                self._check_item_circle(
                    item_target=relation.taxonomy_item_target,
                    item_source=item_source,
                    original_target=original_target,
                )

    @API_V1.arguments(TaxonomyItemRelationPostSchema())
    @API_V1.response(DynamicApiResponseSchema(NewApiObjectSchema()))
    def post(
        self,
        data: Dict[str, str],
        namespace: str,
        taxonomy: str,
        taxonomy_item: str,
    ):
        """Create a new relation to a taxonomy item."""
        self._check_path_params(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        if namespace != data["namespace_id"] or taxonomy != data["taxonomy_id"]:
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext(
                    "Cannot create a relation to a taxonomy item of a different taxonomy!"
                ),
            )

        found_taxonomy_item = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        self._check_if_modifiable(found_taxonomy_item)

        found_taxonomy_item_target = self._get_taxonomy_item(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=data["taxonomy_item_id"]
        )

        self._check_item_circle(found_taxonomy_item_target, found_taxonomy_item)

        relation = TaxonomyItemRelation(
            taxonomy_item_source=found_taxonomy_item,
            taxonomy_item_target=found_taxonomy_item_target,
        )
        DB.session.add(relation)
        DB.session.commit()

        taxonomy_item_relation_link = (
            taxonomy_item_relation_to_taxonomy_item_relation_data(relation).self
        )
        taxonomy_item_relation_data = taxonomy_item_relation_to_api_response(relation)
        taxonomy_item_source_link = taxonomy_item_to_api_link(found_taxonomy_item)
        taxonomy_item_source_data = taxonomy_item_to_api_response(found_taxonomy_item)
        taxonomy_item_target_link = taxonomy_item_to_api_link(found_taxonomy_item_target)
        taxonomy_item_target_data = taxonomy_item_to_api_response(
            found_taxonomy_item_target
        )

        self_link = create_action_link_for_taxonomy_item_relation_page(
            namespace=namespace, taxonomy=taxonomy, taxonomy_item=taxonomy_item
        )
        self_link.rel = (*self_link.rel, "ont-taxonomy-item-relation")
        self_link.resource_type = "new"

        return ApiResponse(
            links=[
                taxonomy_item_relation_link,
                taxonomy_item_source_link,
                taxonomy_item_target_link,
            ],
            embedded=[
                taxonomy_item_relation_data,
                taxonomy_item_source_data,
                taxonomy_item_target_data,
            ],
            data=NewApiObject(
                self=self_link,
                new=taxonomy_item_relation_link,
            ),
        )


@API_V1.route(
    "/namespaces/<string:namespace>/taxonomies/<string:taxonomy>/items/<string:taxonomy_item>/relations/<string:relation>/"
)
class TaxonomyItemRelationView(MethodView):
    """Endpoint for removing taxonomy item relations."""

    def _check_path_params(
        self, namespace: str, taxonomy: str, taxonomy_item: str, relation: str
    ):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not taxonomy or not taxonomy.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy id has the wrong format!"),
            )
        if not taxonomy_item or not taxonomy_item.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy item id has the wrong format!"),
            )
        if not relation or not relation.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext(
                    "The requested taxonomy item relation id has the wrong format!"
                ),
            )

    def _get_taxonomy_item_relation(
        self, namespace: str, taxonomy: str, taxonomy_item: str, relation: str
    ) -> TaxonomyItemRelation:
        namespace_id = int(namespace)
        taxonomy_id = int(taxonomy)
        taxonomy_item_id = int(taxonomy_item)
        relation_id = int(relation)
        found_taxonomy_item_relation: Optional[
            TaxonomyItemRelation
        ] = TaxonomyItemRelation.query.filter(
            TaxonomyItemRelation.id == relation_id,
            TaxonomyItemRelation.taxonomy_item_source_id == taxonomy_item_id,
        ).first()

        if (
            found_taxonomy_item_relation is None
            or found_taxonomy_item_relation.taxonomy_item_source.taxonomy_id
            != taxonomy_id
            or found_taxonomy_item_relation.taxonomy_item_source.taxonomy.namespace_id
            != namespace_id
        ):
            abort(
                HTTPStatus.NOT_FOUND, message=gettext("Taxonomy item relation not found.")
            )
        return found_taxonomy_item_relation  # is not None because abort raises exception

    def _check_if_modifiable(self, relation: TaxonomyItemRelation):
        taxonomy_item = relation.taxonomy_item_source
        taxonomy = taxonomy_item.taxonomy
        if taxonomy.namespace.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Namespace is marked as deleted and cannot be modified further."
                ),
            )
        if taxonomy.deleted_on is not None:
            # cannot modify deleted namespace!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy is marked as deleted and cannot be modified further."
                ),
            )
        if taxonomy_item.deleted_on is not None:
            # cannot modify deleted taxonomy item!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy item is marked as deleted and cannot be modified further."
                ),
            )
        if relation.deleted_on is not None:
            # cannot modify deleted item relation!
            abort(
                HTTPStatus.CONFLICT,
                message=gettext(
                    "Taxonomy item relation is marked as deleted and cannot be modified further."
                ),
            )

    @API_V1.response(DynamicApiResponseSchema(TaxonomyItemRelationSchema()))
    def get(
        self,
        namespace: str,
        taxonomy: str,
        taxonomy_item: str,
        relation: str,
        **kwargs: Any
    ):
        """Get a single relation."""
        self._check_path_params(
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            relation=relation,
        )
        found_relation = self._get_taxonomy_item_relation(
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            relation=relation,
        )
        return ApiResponse(
            links=(*action_links_for_taxonomy_item_relation(found_relation),),
            data=taxonomy_item_relation_to_taxonomy_item_relation_data(found_relation),
        )

    @API_V1.response(DynamicApiResponseSchema(ChangedApiObjectSchema()))
    def delete(
        self,
        namespace: str,
        taxonomy: str,
        taxonomy_item: str,
        relation: str,
        **kwargs: Any
    ):
        """Delete an existing relation."""
        self._check_path_params(
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            relation=relation,
        )
        found_relation = self._get_taxonomy_item_relation(
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            relation=relation,
        )
        self._check_if_modifiable(found_relation)

        # only actually delete when not already deleted
        if found_relation.deleted_on is not None:
            # delete taxonomy item relation
            found_relation.deleted_on = datetime.utcnow()
            DB.session.add(found_relation)
            DB.session.commit()

        relation_link = taxonomy_item_relation_to_taxonomy_item_relation_data(
            found_relation
        ).self
        relation_data = taxonomy_item_relation_to_api_response(found_relation)

        source_item_link = taxonomy_item_to_api_link(found_relation.taxonomy_item_source)
        source_item_data = taxonomy_item_to_api_response(
            found_relation.taxonomy_item_source
        )
        target_item_link = taxonomy_item_to_api_link(found_relation.taxonomy_item_target)
        target_item_data = taxonomy_item_to_api_response(
            found_relation.taxonomy_item_target
        )

        return ApiResponse(
            links=[relation_link, source_item_link, target_item_link],
            embedded=[relation_data, source_item_data, target_item_data],
            data=ChangedApiObject(
                self=ApiLink(
                    href=url_for(
                        "api-v1.TaxonomyItemRelationView",
                        namespace=namespace,
                        taxonomy=taxonomy,
                        taxonomy_item=taxonomy_item,
                        relation=relation,
                        _external=True,
                    ),
                    rel=(
                        "delete",
                        "ont-taxonomy-item-relation",
                    ),
                    resource_type="changed",
                ),
                changed=relation_link,
            ),
        )


@API_V1.route(
    "/namespaces/<string:namespace>/taxonomies/<string:taxonomy>/items/<string:taxonomy_item>/versions/"
)
class TaxonomyItemVersionsView(MethodView):
    """Endpoint for all versions of a taxonomy item."""

    def get(self, namespace: str, taxonomy: str, taxonomy_item: str, **kwargs: Any):
        """TODO."""


@API_V1.route(
    "/namespaces/<string:namespace>/taxonomies/<string:taxonomy>/items/<string:taxonomy_item>/versions/<string:version>/"
)
class TaxonomyItemVersionView(MethodView):
    """Endpoint for a single version of a taxonomy item."""

    def _check_path_params(
        self, namespace: str, taxonomy: str, taxonomy_item: str, version: str
    ):
        if not namespace or not namespace.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested namespace id has the wrong format!"),
            )
        if not taxonomy or not taxonomy.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy id has the wrong format!"),
            )
        if not taxonomy_item or not taxonomy_item.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext("The requested taxonomy item id has the wrong format!"),
            )
        if not version or not version.isdigit():
            abort(
                HTTPStatus.BAD_REQUEST,
                message=gettext(
                    "The requested taxonomy item version has the wrong format!"
                ),
            )

    def _get_taxonomy_item_version(
        self, namespace: str, taxonomy: str, taxonomy_item: str, version: str
    ) -> TaxonomyItemVersion:
        namespace_id = int(namespace)
        taxonomy_id = int(taxonomy)
        taxonomy_item_id = int(taxonomy_item)
        version_nr = int(version)
        found_taxonomy_item_version: Optional[
            TaxonomyItemVersion
        ] = TaxonomyItemVersion.query.filter(
            TaxonomyItemVersion.version == version_nr,
            TaxonomyItemVersion.taxonomy_item_id == taxonomy_item_id,
        ).first()

        if (
            found_taxonomy_item_version is None
            or found_taxonomy_item_version.taxonomy_item.taxonomy_id != taxonomy_id
            or found_taxonomy_item_version.taxonomy_item.taxonomy.namespace_id
            != namespace_id
        ):
            abort(
                HTTPStatus.NOT_FOUND, message=gettext("Taxonomy item version not found.")
            )
        return found_taxonomy_item_version  # is not None because abort raises exception

    @API_V1.response(DynamicApiResponseSchema(TaxonomyItemSchema()))
    def get(
        self,
        namespace: str,
        taxonomy: str,
        taxonomy_item: str,
        version: str,
        **kwargs: Any
    ):
        """Get a single taxonomy item version."""
        self._check_path_params(
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            version=version,
        )
        found_taxonomy_item_version = self._get_taxonomy_item_version(
            namespace=namespace,
            taxonomy=taxonomy,
            taxonomy_item=taxonomy_item,
            version=version,
        )

        return ApiResponse(
            links=[
                ApiLink(
                    href=url_for(
                        "api-v1.NamespacesView",
                        _external=True,
                        item_count=50,
                        sort="name",
                    ),
                    rel=("first", "page", "collection", "nav"),
                    resource_type="ont-namespace",
                    schema=url_for(
                        "api-v1.ApiSchemaView", schema_id="Namespace", _external=True
                    ),
                ),
                *nav_links_for_taxonomy_item_version(found_taxonomy_item_version),
                *action_links_for_taxonomy_item_version(found_taxonomy_item_version),
            ],
            data=taxonomy_item_to_taxonomy_item_data(found_taxonomy_item_version),
        )

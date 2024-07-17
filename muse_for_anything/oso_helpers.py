"""Module for setting up oso support for flask app."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Type

from flask import Flask
from flask.globals import g, request
from flask_oso import FlaskOso
from oso import Oso
from polar.exceptions import OsoError
from sqlalchemy.exc import ArgumentError

from muse_for_anything.db.models.namespace import Namespace
from muse_for_anything.db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectType,
    OntologyObjectTypeVersion,
    OntologyObjectVersion,
)
from muse_for_anything.db.models.taxonomies import (
    Taxonomy,
    TaxonomyItem,
    TaxonomyItemRelation,
    TaxonomyItemVersion,
)
from muse_for_anything.db.models.users import User, UserGrant, UserRole

_RESOURCE_TYPE_TO_RELATION_MAPPING: Dict[Type, str] = {
    Namespace: "ont-namespace",
    OntologyObjectType: "ont-type",
    OntologyObjectTypeVersion: "ont-type-version",
    OntologyObject: "ont-object",
    OntologyObjectVersion: "ont-object-version",
    Taxonomy: "ont-taxonomy",
    TaxonomyItem: "ont-taxonomy-item",
    TaxonomyItemVersion: "ont-taxonomy-item-version",
    TaxonomyItemRelation: "ont-taxonomy-item-relation",
    User: "user",
    UserRole: "user-role",
    UserGrant: "user-grant",
    # TODO add all resources here!
}


def get_oso_resource_type(resource_type: Type) -> str:
    if resource_type in _RESOURCE_TYPE_TO_RELATION_MAPPING:
        return _RESOURCE_TYPE_TO_RELATION_MAPPING[resource_type]
    raise ArgumentError("Unsupported type!")


@dataclass()
class OsoResource:
    resource_type: str
    is_collection: bool = False
    parent_resource: Optional[Any] = None
    arguments: Optional[Dict[str, Any]] = None


class CustomFlaskOso(FlaskOso):

    _oso: Oso
    _app: Flask
    _allowed_methods: Optional[Sequence[str]]

    def __init__(self, *, oso: Optional[Oso] = None, app: Optional[Flask] = None):
        super().__init__(oso=oso, app=app)
        self._allowed_methods = None

    def init_app(self, app: Flask):
        super().init_app(app)
        app.before_request(self._clear_old_cache)

    def _clear_old_cache(
        self,
    ):
        self._allowed_methods = None

    def _get_resource(self):
        if g.current_resource:
            return g.current_resource
        else:
            raise ValueError(
                "Must provide a resource or g.current_resource must not be None!"
            )

    def _get_current_actor(self):
        try:
            return self.current_actor
        except AttributeError as e:
            raise OsoError(
                "Getting the current actor failed. "
                "You may need to override the current actor function with "
                "FlaskOso#set_get_actor"
            ) from e

    def set_current_resource(self, resource: Any):
        g.current_resource = resource

    def authorize_and_set_resource(
        self, resource: Any, *, actor: Optional[Any] = None, action: Optional[Any] = None
    ):
        self.set_current_resource(resource=resource)
        return self.authorize(resource, actor=actor, action=action)

    def authorize(
        self,
        resource: Optional[Any] = None,
        *,
        actor: Optional[Any] = None,
        action: Optional[Any] = None,
    ):
        if resource is None:
            resource = self._get_resource()
        super().authorize(resource, actor=actor, action=action)

    def is_admin(
        self,
        resource: Optional[Any] = None,
        *,
        actor: Optional[Any] = None,
    ):
        if resource is None:
            resource = self._get_resource()

        if actor is None:
            actor = self._get_current_actor()

        oso: Oso = self.oso
        return oso.query_rule("is_admin", resource)

    def is_allowed(
        self,
        resource: Optional[Any] = None,
        *,
        actor: Optional[Any] = None,
        action: Optional[Any] = None,
    ) -> bool:
        if resource is None:
            resource = self._get_resource()

        if actor is None:
            actor = self._get_current_actor()

        if action is None:
            action = request.method

        oso: Oso = self.oso
        return oso.is_allowed(actor, action, resource)

    def get_allowed_actions(
        self, resource=None, *, actor=None, allow_wildcard: bool = True
    ) -> Sequence[str]:
        should_cache_result = resource is None and actor is None and allow_wildcard

        if should_cache_result and self._allowed_methods is not None:
            return self._allowed_methods

        if resource is None:
            resource = self._get_resource()

        if actor is None:
            actor = self._get_current_actor()

        oso: Oso = self.oso
        result = oso.get_allowed_actions(actor, resource, allow_wildcard=allow_wildcard)
        if should_cache_result:
            self._allowed_methods = result
        return result


OSO = Oso()

FLASK_OSO = CustomFlaskOso(oso=OSO)


def register_oso(app: Flask):
    """Register oso to enable access management for this app."""
    from .db.models.namespace import Namespace
    from .db.models.ontology_objects import (
        OntologyObject,
        OntologyObjectType,
        OntologyObjectTypeVersion,
        OntologyObjectVersion,
    )
    from .db.models.taxonomies import (
        Taxonomy,
        TaxonomyItem,
        TaxonomyItemRelation,
        TaxonomyItemVersion,
    )
    from .db.models.users import Guest, User

    FLASK_OSO.init_app(app)

    # Uncomment to enable fail fast on unchecked enpoints
    # FLASK_OSO.require_authorization(app)

    oso_classes = (
        OsoResource,
        User,
        Guest,
        UserRole,
        UserGrant,
        Namespace,
        OntologyObjectType,
        OntologyObjectTypeVersion,
        OntologyObject,
        OntologyObjectVersion,
        Taxonomy,
        TaxonomyItem,
        TaxonomyItemVersion,
        TaxonomyItemRelation,
    )
    for class_to_register in oso_classes:
        OSO.register_class(class_to_register)

    OSO.load_files(app.config.get("OSO_POLICY_FILES", []))

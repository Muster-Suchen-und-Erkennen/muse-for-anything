"""Module for setting up oso support for flask app."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, NoReturn, Optional, Sequence, Type

from flask import Flask, current_app
from flask.globals import request_ctx, g, request
from flask.wrappers import Request, Response
from oso import Oso
from polar.exceptions import OsoError
from sqlalchemy.exc import ArgumentError
from werkzeug.exceptions import Forbidden

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


class CustomFlaskOso:

    _oso: Optional[Oso]
    _app: Optional[Flask]
    _allowed_methods: Optional[Sequence[str]]

    def __init__(self, oso: Optional[Oso] = None, app: Optional[Flask] = None) -> None:
        self._app = app
        self._oso = None

        def unauthorized() -> NoReturn:
            raise Forbidden("Unauthorized")

        self._unauthorized_action = unauthorized

        self._get_actor = lambda: g.current_user

        if self._app is not None:
            self.init_app(self._app)
        if oso is not None:
            self.set_oso(oso)

        self._allowed_methods = None

    def set_oso(self, oso: Oso) -> None:
        if oso == self._oso:
            return
        self._oso = oso
        self._oso.register_class(Request)

    def init_app(self, app: Flask):
        app.teardown_appcontext(self.teardown)
        app.before_request(self._provide_oso)
        app.before_request(self._clear_old_cache)

    def teardown(self, exception):
        pass

    def _provide_oso(self) -> None:
        top = _app_context()
        if not hasattr(top, "oso_flask_oso"):
            top.oso_flask_oso = self

    def _clear_old_cache(
        self,
    ):
        self._allowed_methods = None

    def set_get_actor(self, func: Callable[[], Any]) -> None:
        self._get_actor = func

    def set_unauthorize_action(self, func: Callable[[], Any]) -> None:
        self._unauthorized_action = func

    def require_authorization(self, app: Optional[Flask] = None) -> None:
        if app is None:
            app = self._app
        if app is None:
            raise OsoError("Cannot require authorization without Flask app object")
        app.after_request(self._require_authorization)

    def perform_route_authorization(self, app: Optional[Flask] = None) -> None:
        if app is None:
            app = self._app
        if app is None:
            raise OsoError("Cannot perform route authorization without Flask app object")
        app.before_request(self.perform_route_authorization)

    def skip_authorization(self, reason: Optional[str] = None) -> None:
        _authorize_called()

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
        if actor is None:
            try:
                actor = self.current_actor
            except AttributeError as e:
                raise OsoError(
                    "Getting the current actor failed. "
                    "You may need to override the current actor function with "
                    "FlaskOso#set_get_actor"
                ) from e
        if action is None:
            action = request.method
        if resource is request:
            resource = request._get_currect_object()
        if self.oso is None:
            raise OsoError("Cannot perform authorization without oso instance")

        allowed = self.oso.is_allowed(actor, action, resource)
        _authorize_called()

        if not allowed:
            self._unauthorized_action()

    @property
    def app(self) -> Flask:
        return self._app or current_app

    @property
    def oso(self) -> Optional[Oso]:
        return self._oso

    @property
    def current_actor(self) -> Any:
        return self._get_actor()

    def _perform_route_authorization(self) -> None:
        if not request.url_rule:
            return
        self.authorize(resource=request)

    def _require_authorization(self, response: Response) -> Response:
        if not request.url_rule:
            return response
        if not getattr(_app_context(), "oso_flask_authorize_called", False):
            raise OsoError("Authorize not called.")
        return response

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

        oso = self.oso
        if oso is None:
            raise ValueError("No instance of oso set!")
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

        oso = self.oso
        if oso is None:
            raise ValueError("No instance of oso set!")
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

        oso = self.oso
        if oso is None:
            raise ValueError("No instance of oso set!")
        result = oso.get_allowed_actions(actor, resource, allow_wildcard=allow_wildcard)
        if should_cache_result:
            self._allowed_methods = result
        return result


OSO = Oso()

FLASK_OSO = CustomFlaskOso(oso=OSO)


def _authorize_called() -> None:
    _app_context().oso_flask_authorize_called = True


def _app_context():
    try:
        context = request_ctx._get_current_object()
    except RuntimeError:
        raise OsoError(
            "Application context doesn't exist. Did you use oso outside the context of a request? "
            "See https://flask.palletsprojects.com/en/1.1.x/appcontext/#manually-push-a-context"
        )
    return context


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

"""Module containing the namespace table definitions."""

from typing import List, Optional, Set, Union
from sqlalchemy.orm import relationship
from sqlalchemy.sql.elements import literal
from sqlalchemy.sql.schema import Column, ForeignKey
from ...password_helpers import FLASK_PASSWORD
from ..db import DB, MODEL
from .model_helpers import ExistsMixin, IdMixin, CreateDeleteMixin

from .namespace import Namespace
from .ontology_objects import OntologyObjectType, OntologyObject
from .taxonomies import Taxonomy


RESOURCE_TYPE = Union[Namespace, OntologyObjectType, OntologyObject, Taxonomy]


class Guest:
    def __init__(self) -> None:
        self.id = -1
        self.username = "guest"
        self.e_mail = None

    def authenticate(self, password: str) -> bool:
        return True

    def has_role(self, role: str) -> bool:
        return False

    def has_resource_role(
        self,
        role: str,
        resource: RESOURCE_TYPE,
    ) -> bool:
        return False  # FIXME implement this


def _resolve_resource_type(resource: RESOURCE_TYPE) -> str:
    if isinstance(resource, Namespace):
        return "ont-namespace"
    elif isinstance(resource, OntologyObjectType):
        return "ont-type"
    elif isinstance(resource, OntologyObject):
        return "ont-object"
    elif isinstance(resource, Taxonomy):
        return "ont-taxonomy"
    else:
        raise TypeError("Resource has the wrong type!")


class User(MODEL, IdMixin, CreateDeleteMixin, ExistsMixin):
    """User Table model."""

    __tablename__ = "User"

    username: Column = DB.Column(DB.String(120), unique=True, index=True)
    e_mail: Column = DB.Column(DB.Text, unique=True, index=True, nullable=True)
    password: Column = DB.Column(DB.String(120))

    # references
    roles: List["UserRole"] = relationship(
        "UserRole",
        lazy="joined",
        back_populates="user",
    )

    associated_namespaces: List["AssociatedNamespaces"] = relationship(
        "AssociatedNamespaces",
        lazy="joined",
        back_populates="user",
    )

    grants: List["UserGrant"] = relationship(
        "UserGrant",
        lazy="select",
        back_populates="user",
    )

    def __init__(
        self, username: str, password: str, e_mail: Optional[str] = None, **kwargs
    ) -> None:
        self.username = username
        self.set_new_password(password=password)
        if e_mail:
            self.e_mail = e_mail

    def set_new_password(self, password: str):
        self.password = FLASK_PASSWORD.generate_bcrypt_password_hash(password)

    def authenticate(self, password: str) -> bool:
        return FLASK_PASSWORD.check_password_hash(
            pw_hash=self.password, password=password
        )

    @staticmethod
    def fake_authenticate(password: str):
        """Fake checking a password by hashing the given password to make timing attacks less liekly to succeed."""
        FLASK_PASSWORD.generate_bcrypt_password_hash(password)

    def has_role(self, role: str) -> bool:
        for user_role in self.roles:
            if user_role.role == role:
                return True
        return False

    def is_associated_with_namespace(self, namespace: Namespace) -> bool:
        for associated_namespace in self.associated_namespaces:
            if (
                associated_namespace.namespace is None
                or associated_namespace.namespace_id == namespace.id
            ):
                return True
        return False

    def has_resource_role(
        self,
        role: str,
        resource: RESOURCE_TYPE,
    ) -> bool:
        resource_type: str = _resolve_resource_type(resource=resource)
        # TODO check if query slows down requests (if true, handle inheritance checking here and not in ozo)
        result: Optional[bool] = (
            DB.session.query(literal(True))
            .filter(
                UserGrant.query.filter(
                    UserGrant.user == self,
                    UserGrant.role == role,
                    UserGrant.resource_type == resource_type,
                    (UserGrant.resource_id == None)
                    | (UserGrant.resource_id == resource.id),
                ).exists()
            )
            .scalar()
        )
        return bool(result)

    def set_role_for_resource(self, role: str, resource: RESOURCE_TYPE):
        resource_type: str = _resolve_resource_type(resource=resource)
        grant = UserGrant(self, role, resource_type, resource.id)
        DB.session.add(grant)


def _get_allowed_user_roles() -> Set[str]:
    basic_roles = {"creator", "editor", "admin"}

    allowed_user_roles = set(basic_roles)

    for resource_type in ("ont-namepsace", "ont-type", "ont-object", "ont-taxonomy"):
        allowed_user_roles.update({f"{resource_type}_{role}" for role in basic_roles})
    return allowed_user_roles


ALLOWED_USER_ROLES = _get_allowed_user_roles()


class UserRole(MODEL, IdMixin):
    """User Role Table model."""

    __tablename__ = "UserRole"

    user_id: Column = DB.Column(DB.Integer, ForeignKey(User.id), nullable=False)
    role: Column = DB.Column(DB.String(64))

    # references
    user: User = relationship(
        User,
        innerjoin=True,
        lazy="selectin",
        back_populates="roles",
    )

    def __init__(self, user: User, role: str) -> None:
        if role not in ALLOWED_USER_ROLES:
            raise ValueError(f"Role '{role}' is not an allowed role!")
        self.user = user
        self.role = role


class AssociatedNamespaces(MODEL, IdMixin):
    """Maping from Users to associated Namespaces."""

    __tablename__ = "UserNamespace"

    user_id: Column = DB.Column(DB.Integer, ForeignKey(User.id), nullable=False)
    namespace_id: Column = DB.Column(DB.Integer, ForeignKey(Namespace.id), nullable=True)

    # references
    user: User = relationship(
        User,
        innerjoin=True,
        lazy="selectin",
        back_populates="associated_namespaces",
    )
    namespace: Namespace = relationship(
        Namespace,
        innerjoin=True,
        lazy="selectin",
    )


def _get_allowed_resource_roles() -> Set[str]:
    basic_resource_roles = {"owner", "admin", "editor", "creator"}

    allowed_resource_roles = set(basic_resource_roles)

    for resource_type in ("ont-type", "ont-object", "ont-taxonomy"):
        allowed_resource_roles.update(
            {f"{resource_type}_{role}" for role in basic_resource_roles}
        )
    return allowed_resource_roles


ALLOWED_RESOURCE_ROLES = _get_allowed_resource_roles()
ALLOWED_RESOURCE_TYPES = {"ont-namespace", "ont-type", "ont-object", "ont-taxonomy"}


class UserGrant(MODEL, IdMixin):
    """User Grant Table model."""

    __tablename__ = "UserGrant"

    user_id: Column = DB.Column(DB.Integer, ForeignKey(User.id), nullable=True)
    role: Column = DB.Column(DB.String(64))
    resource_type: Column = DB.Column(DB.String(64))
    resource_id: Column = DB.Column(DB.Integer())

    user: User = relationship(
        User,
        innerjoin=True,
        lazy="selectin",
        back_populates="grants",
    )

    def __init__(
        self, user: User, role: str, resource_type: str, resource_id: int
    ) -> None:
        if role not in ALLOWED_RESOURCE_ROLES:
            raise ValueError(f"Role '{role}' is not an allowed resource role!")
        if resource_type not in ALLOWED_RESOURCE_TYPES:
            raise ValueError(f"Type '{resource_type}' is not an allowed resource type!")
        self.user = user
        self.role = role
        self.resource_type = resource_type
        self.resource_id = resource_id

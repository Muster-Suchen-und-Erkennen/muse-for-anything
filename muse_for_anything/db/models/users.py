"""Module containing the namespace table definitions."""

from typing import List, Optional, Set, Union

from flask_babel import gettext
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.elements import literal
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.types import Text

from .model_helpers import CreateDeleteMixin, ExistsMixin, IdMixin
from .namespace import Namespace
from .ontology_objects import OntologyObject, OntologyObjectType
from .taxonomies import Taxonomy
from ..db import DB, MODEL
from ...password_helpers import FLASK_PASSWORD

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

    username: Mapped[str] = mapped_column(DB.String(120), unique=True, index=True)
    e_mail: Mapped[Text] = mapped_column(DB.Text, unique=True, index=True, nullable=True)
    password: Mapped[str] = mapped_column(DB.String(120))

    # references
    roles: Mapped[List["UserRole"]] = relationship(
        lazy="joined",
        back_populates="user",
    )

    grants: Mapped[List["UserGrant"]] = relationship(
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

    def update(
        self,
        username: str,
        e_mail: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs,
    ):
        if username != self.username:
            self.username = username
        if self.e_mail != e_mail:
            self.e_mail = e_mail
        if password:
            self.set_new_password(password=password)

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

    user_id: Mapped[int] = mapped_column(ForeignKey("User.id"), nullable=False)
    role: Mapped[str] = mapped_column(DB.String(64))

    # references
    user: Mapped[User] = relationship(
        innerjoin=True,
        lazy="selectin",
        back_populates="roles",
    )

    def __init__(self, user: User, role: str) -> None:
        if role not in ALLOWED_USER_ROLES:
            raise ValueError(f"Role '{role}' is not an allowed role!")
        self.user = user
        self.role = role

    @property
    def description(self) -> str:
        # FIXME provide a description for all possible roles!
        if self.role == "admin":
            return gettext("The 'admin' role gives the user all rights to do everything.")
        elif self.role == "editor":
            return gettext(
                "The 'editor' role gives the user the rights to do anything with objects but no rights to user management."
            )
        elif self.role == "creator":
            return gettext(
                "The 'creator' role gives the user the rights to create new objects. The creator of an object is granted owner rights of that object."
            )
        if self.role.startswith("ont-namespace"):
            if self.role.endswith("admin"):
                return gettext("The user has all rights concerning namespaces.")
            if self.role.endswith("editor"):
                return gettext("The user has the rights to edit namespaces.")
            if self.role.endswith("creator"):
                return gettext(
                    "The user has the rights to create namespaces. The creator of a namespace is granted owner rights of that namespace."
                )
        if self.role.startswith("ont-type"):
            if self.role.endswith("admin"):
                return gettext("The user has all rights concerning types.")
            if self.role.endswith("editor"):
                return gettext("The user has the rights to edit types.")
            if self.role.endswith("creator"):
                return gettext(
                    "The user has the rights to create types. The creator of a type is granted owner rights of that type."
                )
        if self.role.startswith("ont-object"):
            if self.role.endswith("admin"):
                return gettext("The user has all rights concerning objects.")
            if self.role.endswith("editor"):
                return gettext("The user has the rights to edit objects.")
            if self.role.endswith("creator"):
                return gettext(
                    "The user has the rights to create objects. The creator of an object is granted owner rights of that object."
                )
        if self.role.startswith("ont-taxonomy"):
            if self.role.endswith("admin"):
                return gettext("The user has all rights concerning taxonomies.")
            if self.role.endswith("editor"):
                return gettext("The user has the rights to edit taxonomies.")
            if self.role.endswith("creator"):
                return gettext(
                    "The user has the rights to create taxonomies. The creator of a taxonomy is granted owner rights of that taxonomy."
                )
        return gettext("A user role with no further description.")


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

    user_id: Mapped[int] = mapped_column(ForeignKey("User.id"), nullable=True)
    role: Mapped[str] = mapped_column(DB.String(64), index=True)
    resource_type: Mapped[str] = mapped_column(DB.String(64), index=True)
    resource_id: Mapped[int] = mapped_column(index=True)

    user: Mapped[User] = relationship(
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

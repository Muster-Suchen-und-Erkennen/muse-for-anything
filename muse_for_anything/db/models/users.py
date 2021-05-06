"""Module containing the namespace table definitions."""

from typing import List, Optional, Union
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column, ForeignKey, Index
from sqlalchemy.ext.declarative import declared_attr
from ..db import DB, MODEL
from .model_helpers import IdMixin, CreateDeleteMixin

from .namespace import Namespace
from .ontology_objects import OntologyObjectType, OntologyObject
from .taxonomies import Taxonomy


class User(MODEL, IdMixin, CreateDeleteMixin):
    """User Table model."""

    __tablename__ = "User"

    username: Column = DB.Column(DB.String(120), unique=True, index=True)
    e_mail: Column = DB.Column(DB.Text, unique=True, index=True)
    password: Column = DB.Column(DB.String(120))

    # references
    roles: List["UserRole"] = relationship(
        "UserRole",
        innerjoin=True,
        lazy="joined",
        back_populates="user",
    )

    associated_namespaces: List["AssociatedNamespaces"] = relationship(
        "AssociatedNamespaces",
        innerjoin=True,
        lazy="joined",
        back_populates="user",
    )

    def __init__(
        self, name: str, username: str, e_mail: str, password: str, **kwargs
    ) -> None:
        self.username = username
        self.e_mail = e_mail
        self.password = password

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
        resource: Union[Namespace, OntologyObjectType, OntologyObject, Taxonomy],
    ) -> bool:
        return False  # FIXME implement this


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


class UserGrant(MODEL, IdMixin):
    """User Grant Table model."""

    __tablename__ = "UserGrant"

    user_id: Column = DB.Column(DB.Integer, ForeignKey(User.id), nullable=True)
    role: Column = DB.Column(DB.String(64))
    resource_type: Column = DB.Column(DB.String(64))
    resource_id: Column = DB.Column(DB.String(64))

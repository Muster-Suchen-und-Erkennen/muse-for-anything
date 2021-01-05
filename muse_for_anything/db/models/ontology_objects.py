"""Module containing ontology object table definitions."""

from typing import Any
from sqlalchemy.sql.schema import ForeignKey, Column, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from ..db import DB, MODEL
from .model_helpers import (
    FULLTEXT_INDEX_PARAMS,
    ChangesMixin,
    CreateDeleteMixin,
    IdMixin,
    NameDescriptionMixin,
)

from .namespace import Namespace


class OntologyObjectType(MODEL, IdMixin, NameDescriptionMixin, ChangesMixin):
    """Ontology object type model."""

    __tablename__ = "Type"

    namespace_id: Column = DB.Column(DB.Integer, ForeignKey(Namespace.id), nullable=False)
    current_version_id: Column = DB.Column(
        DB.Integer, ForeignKey("TypeVersion.id"), nullable=True
    )
    is_toplevel_type: Column = DB.Column(DB.Boolean, nullable=False)

    # relationships
    namespace = relationship(Namespace, innerjoin=True, lazy="joined")
    current_version = relationship(
        "OntologyObjectTypeVersion",
        innerjoin=True,
        lazy="joined",
        primaryjoin="OntologyObjectType.current_version_id == OntologyObjectTypeVersion.id",
    )
    versions = relationship(
        "OntologyObjectTypeVersion",
        lazy="select",
        order_by="OntologyObjectTypeVersion.version",
        back_populates="ontology_type",
        primaryjoin="OntologyObjectType.id == OntologyObjectTypeVersion.object_type_id",
    )
    ontology_objects = relationship(
        "OntologyObject",
        lazy="select",
        back_populates="ontology_type",
    )

    @property
    def version(self) -> int:
        if self.current_version_id is None:
            return 0
        return self.current_version.version

    @property
    def schema(self) -> Any:
        if self.current_version_id is None:
            return None
        return self.current_version.data


class OntologyObjectTypeVersion(MODEL, IdMixin, CreateDeleteMixin):
    """Ontology object type version model."""

    __tablename__ = "TypeVersion"

    id: Column = DB.Column(DB.Integer, primary_key=True)
    object_type_id: Column = DB.Column(
        DB.Integer, ForeignKey(OntologyObjectType.id), nullable=False
    )
    version: Column = DB.Column(DB.Integer, nullable=False)
    data: Column = DB.Column(DB.JSON, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            Index(
                f"ix_uq_version_{cls.__tablename__}",
                "object_type_id",
                "version",
                unique=True,
            ),
        )

    # relationships
    ontology_type = relationship(
        OntologyObjectType,
        innerjoin=True,
        lazy="joined",
        back_populates="versions",
        primaryjoin=OntologyObjectType.id == object_type_id,
    )
    ontology_object_versions = relationship(
        "OntologyObjectVersion",
        lazy="select",
        back_populates="ontology_type_version",
    )


class OntologyObject(MODEL, IdMixin, NameDescriptionMixin, ChangesMixin):
    """Ontology object model."""

    __tablename__ = "Object"

    namespace_id: Column = DB.Column(DB.Integer, ForeignKey(Namespace.id), nullable=False)
    object_type_id: Column = DB.Column(
        DB.Integer, ForeignKey(OntologyObjectType.id), nullable=False
    )
    current_version_id: Column = DB.Column(
        DB.Integer, ForeignKey("ObjectVersion.id"), nullable=True
    )

    # relationships
    namespace = relationship(Namespace, innerjoin=True, lazy="joined")
    ontology_type = relationship(
        OntologyObjectType,
        innerjoin=True,
        lazy="joined",
        back_populates="ontology_objects",
    )
    current_version = relationship(
        "OntologyObjectVersion",
        innerjoin=True,
        lazy="joined",
        primaryjoin="OntologyObject.current_version_id == OntologyObjectVersion.id",
    )
    versions = relationship(
        "OntologyObjectVersion",
        lazy="select",
        order_by="OntologyObjectVersion.version",
        back_populates="ontology_object",
        primaryjoin="OntologyObject.id == OntologyObjectVersion.object_id",
    )


class OntologyObjectVersion(MODEL, IdMixin, CreateDeleteMixin):
    """Ontology object version model."""

    __tablename__ = "ObjectVersion"

    object_id: Column = DB.Column(
        DB.Integer, ForeignKey(OntologyObject.id), nullable=False
    )
    version: Column = DB.Column(DB.Integer, nullable=False)
    object_type_version_id: Column = DB.Column(
        DB.Integer, ForeignKey(OntologyObjectTypeVersion.id), nullable=False
    )
    data: Column = DB.Column(DB.JSON, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            Index(
                f"ix_uq_version_{cls.__tablename__}", "object_id", "version", unique=True
            ),
        )

    # relationships
    ontology_object = relationship(
        OntologyObject,
        innerjoin=True,
        lazy="joined",
        back_populates="versions",
        primaryjoin=OntologyObject.id == object_id,
    )
    ontology_type_version = relationship(
        OntologyObjectTypeVersion,
        innerjoin=True,
        lazy="joined",
        back_populates="ontology_object_versions",
    )

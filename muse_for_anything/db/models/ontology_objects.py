"""Module containing ontology object table definitions."""

from typing import Any, Dict, Optional, cast
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
    namespace: Namespace = relationship(Namespace, innerjoin=True, lazy="joined")
    current_version: "OntologyObjectTypeVersion" = relationship(
        "OntologyObjectTypeVersion",
        post_update=True,
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
    ontology_objects: "OntologyObject" = relationship(
        "OntologyObject",
        lazy="select",
        back_populates="ontology_type",
    )

    @declared_attr
    def __table_args__(cls):
        return (
            Index(
                f"ix_search{cls.__tablename__}",
                "name",
                "description",
                **FULLTEXT_INDEX_PARAMS,
            ),
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

    def __init__(
        self,
        namespace: Namespace,
        name: str,
        description: Optional[str] = None,
        is_top_level_type: Optional[bool] = True,
        **kwargs,
    ) -> None:
        self.namespace = namespace
        self.update(name, description, is_top_level_type=is_top_level_type, **kwargs)

    def update(
        self,
        name: str,
        description: Optional[str] = None,
        is_top_level_type: Optional[bool] = None,
        **kwargs,
    ):
        if kwargs:
            raise ValueError("Got unknown keyword arguments!")
        self.name = name
        self.description = description
        if is_top_level_type is None and self.is_toplevel_type is None:
            self.is_toplevel_type = True
        elif is_top_level_type is not None:
            self.is_toplevel_type = is_top_level_type


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
    ontology_type: OntologyObjectType = relationship(
        OntologyObjectType,
        innerjoin=True,
        lazy="joined",
        back_populates="versions",
        primaryjoin=OntologyObjectType.id == object_type_id,
    )
    ontology_object_versions: "OntologyObjectVersion" = relationship(
        "OntologyObjectVersion",
        lazy="select",
        back_populates="ontology_type_version",
    )

    @property
    def root_schema(self):
        root_schema: Dict[str, Any] = {}
        if self.data is not None:
            root_schema = self.data
        if root_schema.get("$ref", "").startswith("#/definitions/"):
            schema_key = cast(str, root_schema.get("$ref"))[14:]
            schema = root_schema.get("definitions", {}).get(schema_key, None)
            if schema is not None:
                root_schema = schema
        return root_schema

    @property
    def abstract(self) -> bool:
        return self.data is not None and self.data.get("abstract", False)

    @property
    def name(self) -> str:
        return self.root_schema.get("title", "")

    @property
    def description(self) -> str:
        description: Optional[str] = self.root_schema.get("description", "")
        if description:
            return description
        return ""

    def __init__(
        self, ontology_type: OntologyObjectType, version: int, data: Any, **kwargs
    ) -> None:
        self.ontology_type = ontology_type
        self.version = version
        self.update(data, **kwargs)

    def update(self, data: Any, **kwargs):
        if kwargs:
            raise ValueError("Got unknown keyword arguments!")
        self.data = data


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
    namespace: Namespace = relationship(Namespace, innerjoin=True, lazy="joined")
    ontology_type: OntologyObjectType = relationship(
        OntologyObjectType,
        innerjoin=True,
        lazy="joined",
        back_populates="ontology_objects",
    )
    current_version: "OntologyObjectVersion" = relationship(
        "OntologyObjectVersion",
        post_update=True,
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
    ontology_object: OntologyObject = relationship(
        OntologyObject,
        innerjoin=True,
        lazy="joined",
        back_populates="versions",
        primaryjoin=OntologyObject.id == object_id,
    )
    ontology_type_version: OntologyObjectTypeVersion = relationship(
        OntologyObjectTypeVersion,
        innerjoin=True,
        lazy="joined",
        back_populates="ontology_object_versions",
    )

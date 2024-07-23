"""Module containing ontology object table definitions."""

from typing import Any, Dict, List, Optional, cast
from sqlalchemy.sql.schema import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.types import Text

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

    namespace_id: Mapped[int] = mapped_column(ForeignKey("Namespace.id"), nullable=False)
    current_version_id: Mapped[int] = mapped_column(ForeignKey("TypeVesion.id"), nullable=True)
    is_toplevel_type: Mapped[int] = mapped_column(nullable=False)
    
    # relationships
    namespace: Mapped[Namespace] = relationship(innerjoin=True, lazy="selectin")
    current_version: Mapped["OntologyObjectTypeVersion"] = relationship(
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
    ontology_objects: Mapped["OntologyObject"] = relationship(
        lazy="select",
        back_populates="ontology_type",
    )

    referenced_by_types: Mapped[List["rel.OntologyTypeVersionToType"]] = relationship(
        lazy="select",
        order_by="OntologyTypeVersionToType.id",
        back_populates="type_target",
        primaryjoin="OntologyObjectType.id == OntologyTypeVersionToType.type_target_id",
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

    id: Mapped[int] = mapped_column(primary_key=True)
    object_type_id: Mapped[int] = mapped_column(ForeignKey("OntologyObjectType.id"), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    data: Mapped[Text] = mapped_column(DB.JSON, nullable=False)

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
    ontology_type: Mapped[OntologyObjectType] = relationship(
        lazy="select",  # should already be in chache in most cases
        back_populates="versions",
        primaryjoin=OntologyObjectType.id == object_type_id,
    )
    ontology_object_versions: Mapped["OntologyObjectVersion"] = relationship(
        lazy="select",
        back_populates="ontology_type_version",
    )

    imported_types: Mapped[List["rel.OntologyTypeVersionToTypeVersion"]] = relationship(
        lazy="select",
        order_by="OntologyTypeVersionToTypeVersion.id",
        back_populates="type_version_source",
        primaryjoin="OntologyObjectTypeVersion.id == OntologyTypeVersionToTypeVersion.type_version_source_id",
    )
    imported_by_types: Mapped[List["rel.OntologyTypeVersionToTypeVersion"]] = relationship(
        lazy="select",
        order_by="OntologyTypeVersionToTypeVersion.id",
        back_populates="type_version_target",
        primaryjoin="OntologyObjectTypeVersion.id == OntologyTypeVersionToTypeVersion.type_version_target_id",
    )

    referenced_types: Mapped[List["rel.OntologyTypeVersionToType"]] = relationship(
        lazy="select",
        order_by="OntologyTypeVersionToType.id",
        back_populates="type_version_source",
        primaryjoin="OntologyObjectTypeVersion.id == OntologyTypeVersionToType.type_version_source_id",
    )

    referenced_taxonomies: Mapped[List["rel.OntologyTypeVersionToTaxonomy"]] = relationship(
        lazy="select",
        order_by="OntologyTypeVersionToTaxonomy.id",
        back_populates="type_version_source",
        primaryjoin="OntologyObjectTypeVersion.id == OntologyTypeVersionToTaxonomy.type_version_source_id",
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
        return self.data is not None and self.data.get("title", "")

    @property
    def description(self) -> str:
        return self.data is not None and self.data.get("description", "")

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

    namespace_id: Mapped[int] = mapped_column(ForeignKey("Namespace.id"), nullable=False)
    object_type_id: Mapped[int] = mapped_column(ForeignKey("OnotologyObjectType.id"), nullable=False)
    current_version_id: Mapped[int] = mapped_column(ForeignKey("ObjectVersion.id"), nullable=True)

    # relationships
    namespace: Mapped[Namespace] = relationship(innerjoin=True, lazy="selectin")
    ontology_type: Mapped[OntologyObjectType] = relationship(
        innerjoin=True,
        lazy="selectin",  # load the type in a seperate query (and maybe benefit from session chache)
        back_populates="ontology_objects",
    )
    current_version: Mapped["OntologyObjectVersion"] = relationship(
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

    referenced_by_objects: Mapped[List["rel.OntologyObjectVersionToObject"]] = relationship(
        lazy="select",
        order_by="OntologyObjectVersionToObject.id",
        back_populates="object_target",
        primaryjoin="OntologyObject.id == OntologyObjectVersionToObject.object_target_id",
    )

    @property
    def data(self):
        if self.current_version is None:
            return None
        return self.current_version.data

    @property
    def version(self):
        if self.current_version is None:
            return None
        return self.current_version.version

    @property
    def ontology_type_version(self) -> Optional[OntologyObjectTypeVersion]:
        if self.current_version is None:
            return None
        return self.current_version.ontology_type_version

    def __init__(
        self,
        namespace: Namespace,
        ontology_type: OntologyObjectType,
        name: str,
        description: Optional[str] = None,
        **kwargs,
    ) -> None:
        self.namespace = namespace
        self.ontology_type = ontology_type
        self.update(name, description, **kwargs)

    def update(
        self,
        name: str,
        description: Optional[str] = None,
        **kwargs,
    ):
        if kwargs:
            raise ValueError("Got unknown keyword arguments!")
        self.name = name
        self.description = description


class OntologyObjectVersion(MODEL, IdMixin, NameDescriptionMixin, CreateDeleteMixin):
    """Ontology object version model."""

    __tablename__ = "ObjectVersion"

    object_id: Mapped[int] = mapped_column(ForeignKey("OntologyObject.id"), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    object_type_version_id: Mapped[int] = mapped_column(ForeignKey("OntologyObjectTypeVersion.id"), nullable=False)
    data: Mapped[Text] = mapped_column(DB.JSON, nullable=False)

    @declared_attr
    def __table_args__(cls):
        return (
            Index(
                f"ix_uq_version_{cls.__tablename__}", "object_id", "version", unique=True
            ),
        )

    # relationships
    ontology_object: Mapped[OntologyObject] = relationship(
        innerjoin=True,
        lazy="select",  # should already be in session cache
        back_populates="versions",
        primaryjoin=OntologyObject.id == object_id,
    )
    ontology_type_version: Mapped[OntologyObjectTypeVersion] = relationship(
        innerjoin=True,
        lazy="selectin",  # selectin uses a second (or more) queries and is more memory efficient compared to direct join
        back_populates="ontology_object_versions",
    )

    referenced_objects: Mapped[List["rel.OntologyObjectVersionToObject"]] = relationship(
        lazy="select",
        order_by="OntologyObjectVersionToObject.id",
        back_populates="object_version_source",
        primaryjoin="OntologyObjectVersion.id == OntologyObjectVersionToObject.object_version_source_id",
    )

    referenced_taxonomy_items: Mapped[List["rel.OntologyObjectVersionToTaxonomyItem"]] = relationship(
        lazy="select",
        order_by="OntologyObjectVersionToTaxonomyItem.id",
        back_populates="object_version_source",
        primaryjoin="OntologyObjectVersion.id == OntologyObjectVersionToTaxonomyItem.object_version_source_id",
    )

    @property
    def updated_on(self):
        return self.created_on

    def __init__(
        self,
        object: OntologyObject,
        type_version: OntologyObjectTypeVersion,
        version: int,
        name: str,
        data: Any,
        description: Optional[str] = None,
        **kwargs,
    ) -> None:
        self.ontology_object = object
        self.ontology_type_version = type_version
        self.version = version
        self.update(data=data, name=name, description=description, **kwargs)

    def update(self, data: Any, name: str, description: Optional[str] = None, **kwargs):
        if kwargs:
            raise ValueError("Got unknown keyword arguments!")
        self.data = data
        self.name = name
        self.description = description


# late imports for type checker. at the end to avoid circular imports!
from . import object_relation_tables as rel

"""Module containing relation tables."""

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
from .ontology_objects import (
    OntologyObjectType,
    OntologyObjectTypeVersion,
    OntologyObject,
    OntologyObjectVersion,
)
from .taxonomies import Taxonomy, TaxonomyItem


class OntologyTypeVersionToTypeVersion(MODEL, IdMixin):
    """Import relation between type versions."""

    __tablename__ = "TypeVersionToTypeVersion"

    # the type version importing
    type_version_source_id: Column = DB.Column(
        DB.Integer, ForeignKey(OntologyObjectTypeVersion.id), nullable=False
    )
    # the imported type version
    type_version_target_id: Column = DB.Column(
        DB.Integer, ForeignKey(OntologyObjectTypeVersion.id), nullable=False
    )

    # relationships
    type_version_source: OntologyObjectTypeVersion = relationship(
        OntologyObjectTypeVersion,
        lazy="select",  # is nearly always in cache anyway
        back_populates="imported_types",
        primaryjoin=OntologyObjectTypeVersion.id == type_version_source_id,
    )

    type_version_target: OntologyObjectTypeVersion = relationship(
        OntologyObjectTypeVersion,
        lazy="select",  # is nearly always in cache anyway
        back_populates="imported_by_types",
        primaryjoin=OntologyObjectTypeVersion.id == type_version_target_id,
    )

    def __init__(
        self,
        type_version_source: OntologyObjectTypeVersion,
        type_version_target: OntologyObjectTypeVersion,
    ) -> None:
        self.type_version_source = type_version_source
        self.type_version_target = type_version_target


class OntologyTypeVersionToType(MODEL, IdMixin):
    """Reference relation between a type version and a type."""

    __tablename__ = "TypeVersionToType"

    type_version_source_id: Column = DB.Column(
        DB.Integer, ForeignKey(OntologyObjectTypeVersion.id), nullable=False
    )
    type_target_id: Column = DB.Column(
        DB.Integer, ForeignKey(OntologyObjectType.id), nullable=False
    )

    # relationships
    type_version_source: OntologyObjectTypeVersion = relationship(
        OntologyObjectTypeVersion,
        lazy="select",  # is nearly always in cache anyway
        back_populates="referenced_types",
        primaryjoin=OntologyObjectTypeVersion.id == type_version_source_id,
    )

    type_target: OntologyObjectType = relationship(
        OntologyObjectType,
        lazy="select",  # is nearly always in cache anyway
        back_populates="referenced_by_types",
        primaryjoin=OntologyObjectType.id == type_target_id,
    )

    def __init__(
        self,
        type_version_source: OntologyObjectTypeVersion,
        type_target: OntologyObjectType,
    ) -> None:
        self.type_version_source = type_version_source
        self.type_target = type_target


class OntologyTypeVersionToTaxonomy(MODEL, IdMixin):
    """Reference relation between a type version and a taxonomy."""

    __tablename__ = "TypeVersionToTaxonomy"

    type_version_source_id: Column = DB.Column(
        DB.Integer, ForeignKey(OntologyObjectTypeVersion.id), nullable=False
    )
    taxonomy_target_id: Column = DB.Column(
        DB.Integer, ForeignKey(Taxonomy.id), nullable=False
    )

    # relationships
    type_version_source: OntologyObjectTypeVersion = relationship(
        OntologyObjectTypeVersion,
        lazy="select",  # is nearly always in cache anyway
        back_populates="referenced_taxonomies",
        primaryjoin=OntologyObjectTypeVersion.id == type_version_source_id,
    )

    taxonomy_target: Taxonomy = relationship(
        Taxonomy,
        lazy="select",  # is nearly always in cache anyway
        back_populates="referenced_by_types",
        primaryjoin=Taxonomy.id == taxonomy_target_id,
    )

    def __init__(
        self,
        type_version_source: OntologyObjectTypeVersion,
        taxonomy_target: Taxonomy,
    ) -> None:
        self.type_version_source = type_version_source
        self.taxonomy_target = taxonomy_target


class OntologyObjectVersionToObject(MODEL, IdMixin):
    """Reference relation between a object version and another object."""

    __tablename__ = "ObjectVersionToObject"

    object_version_source_id: Column = DB.Column(
        DB.Integer, ForeignKey(OntologyObjectVersion.id), nullable=False
    )
    object_target_id: Column = DB.Column(
        DB.Integer, ForeignKey(OntologyObject.id), nullable=False
    )

    # relationships
    object_version_source: OntologyObjectVersion = relationship(
        OntologyObjectVersion,
        lazy="select",  # is nearly always in cache anyway
        back_populates="referenced_objects",
        primaryjoin=OntologyObjectVersion.id == object_version_source_id,
    )

    object_target: OntologyObject = relationship(
        OntologyObject,
        lazy="select",  # is nearly always in cache anyway
        back_populates="referenced_by_objects",
        primaryjoin=OntologyObject.id == object_target_id,
    )

    def __init__(
        self,
        object_version_source: OntologyObjectVersion,
        object_target: OntologyObject,
    ) -> None:
        self.object_version_source = object_version_source
        self.object_target = object_target


class OntologyObjectVersionToTaxonomyItem(MODEL, IdMixin):
    """Reference relation between a object version and a taxonomy item."""

    __tablename__ = "ObjectVersionToTaxonomyItem"

    object_version_source_id: Column = DB.Column(
        DB.Integer, ForeignKey(OntologyObjectVersion.id), nullable=False
    )
    taxonomy_item_target_id: Column = DB.Column(
        DB.Integer, ForeignKey(TaxonomyItem.id), nullable=False
    )

    # relationships
    object_version_source: OntologyObjectVersion = relationship(
        OntologyObjectVersion,
        lazy="select",  # is nearly always in cache anyway
        back_populates="referenced_taxonomy_items",
        primaryjoin=OntologyObjectVersion.id == object_version_source_id,
    )

    taxonomy_item_target: TaxonomyItem = relationship(
        TaxonomyItem,
        lazy="select",  # is nearly always in cache anyway
        back_populates="referenced_by_objects",
        primaryjoin=TaxonomyItem.id == taxonomy_item_target_id,
    )

    def __init__(
        self,
        object_version_source: OntologyObjectVersion,
        taxonomy_item_target: TaxonomyItem,
    ) -> None:
        self.object_version_source = object_version_source
        self.taxonomy_item_target = taxonomy_item_target

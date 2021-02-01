"""Module containing ontology object table definitions."""

from typing import Any, Dict, List, Optional, cast
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


class Taxonomy(MODEL, IdMixin, NameDescriptionMixin, ChangesMixin):
    """Taxonomy model."""

    __tablename__ = "Taxonomy"

    namespace_id: Column = DB.Column(DB.Integer, ForeignKey(Namespace.id), nullable=False)

    # relationships
    namespace = relationship(Namespace, innerjoin=True, lazy="joined")

    items: List["TaxonomyItem"] = relationship(
        "TaxonomyItem",
        innerjoin=True,
        lazy="joined",
        order_by="TaxonomyItem.id",
        back_populates="taxonomy",
        primaryjoin="Taxonomy.id == TaxonomyItem.taxonomy_id",
    )

    def __init__(
        self,
        namespace: Namespace,
        name: str,
        description: Optional[str] = None,
        **kwargs,
    ) -> None:
        self.namespace = namespace
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


class TaxonomyItem(MODEL, IdMixin, ChangesMixin):
    """Taxonomy Item model."""

    __tablename__ = "TaxonomyItem"

    taxonomy_id: Column = DB.Column(DB.Integer, ForeignKey(Taxonomy.id), nullable=False)
    current_version_id: Column = DB.Column(
        DB.Integer, ForeignKey("TaxonomyItemVersion.id"), nullable=True
    )

    # relationships
    taxonomy: Taxonomy = relationship(
        Taxonomy, innerjoin=True, lazy="joined", back_populates="items"
    )
    current_version: "TaxonomyItemVersion" = relationship(
        "TaxonomyItemVersion",
        post_update=True,
        innerjoin=True,
        lazy="joined",
        primaryjoin="TaxonomyItem.current_version_id == TaxonomyItemVersion.id",
    )
    versions: List["TaxonomyItemVersion"] = relationship(
        "TaxonomyItemVersion",
        lazy="select",
        order_by="TaxonomyItemVersion.version",
        back_populates="taxonomy_item",
        primaryjoin="TaxonomyItem.id == TaxonomyItemVersion.taxonomy_item_id",
    )

    @property
    def name(self) -> str:
        if self.current_version is None:
            return ""
        return self.current_version.name

    @property
    def description(self) -> str:
        if self.current_version is None:
            return ""
        description = self.current_version.description
        if description is None:
            return ""
        return description


class TaxonomyItemVersion(MODEL, IdMixin, NameDescriptionMixin, CreateDeleteMixin):
    """Taxonomy Item version model."""

    __tablename__ = "TaxonomyItemVersion"

    taxonomy_item_id: Column = DB.Column(
        DB.Integer, ForeignKey(TaxonomyItem.id), nullable=False
    )
    version: Column = DB.Column(DB.Integer, nullable=False)
    sort_key: Column = DB.Column(DB.Float, nullable=True, default=10)

    @declared_attr
    def __table_args__(cls):
        return (
            Index(
                f"ix_uq_version_{cls.__tablename__}",
                "taxonomy_item_id",
                "version",
                unique=True,
            ),
            Index(
                f"ix_search{cls.__tablename__}",
                "name",
                "description",
                **FULLTEXT_INDEX_PARAMS,
            ),
        )

    # relationships
    taxonomy_item: TaxonomyItem = relationship(
        TaxonomyItem,
        innerjoin=True,
        lazy="joined",
        back_populates="versions",
        primaryjoin=TaxonomyItem.id == taxonomy_item_id,
    )
    related: List["TaxonomyItemRelation"] = relationship(
        "TaxonomyItemRelation",
        innerjoin=True,
        lazy="joined",
        order_by="TaxonomyItemRelation.id",
        back_populates="taxonomy_item_source",
        primaryjoin="TaxonomyItem.id == TaxonomyItemRelation.taxonomy_item_source_id",
    )
    ancestors: List["TaxonomyItemRelation"] = relationship(
        "TaxonomyItemRelation",
        lazy="select",
        order_by="TaxonomyItemRelation.id",
        back_populates="taxonomy_item_target",
        primaryjoin="TaxonomyItem.id == TaxonomyItemRelation.taxonomy_item_target_id",
    )


class TaxonomyItemRelation(MODEL, IdMixin, CreateDeleteMixin):
    """Taxonomy Item relation model."""

    __tablename__ = "TaxonomyItemRelation"

    taxonomy_item_source_id: Column = DB.Column(
        DB.Integer, ForeignKey(TaxonomyItemVersion.id), nullable=False
    )

    taxonomy_item_target_id: Column = DB.Column(
        DB.Integer, ForeignKey(TaxonomyItemVersion.id), nullable=False
    )

    # relationships
    taxonomy_item_source: TaxonomyItemVersion = relationship(
        TaxonomyItemVersion,
        lazy="select",
        back_populates="related",
        primaryjoin=TaxonomyItemVersion.id == taxonomy_item_source_id,
    )

    # relationships
    taxonomy_item_source: TaxonomyItemVersion = relationship(
        TaxonomyItemVersion,
        innerjoin=True,
        lazy="joined",
        back_populates="ancestors",
        primaryjoin=TaxonomyItemVersion.id == taxonomy_item_target_id,
    )

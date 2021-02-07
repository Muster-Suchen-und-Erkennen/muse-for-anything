"""Module containing ontology object table definitions."""

from typing import Any, Dict, List, Optional, cast
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.schema import ForeignKey, Column, Index
from sqlalchemy.orm import relationship, selectinload
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
    namespace = relationship(Namespace, innerjoin=True, lazy="selectin")

    items: List["TaxonomyItem"] = relationship(
        "TaxonomyItem",
        lazy="select",  # do not always load this
        order_by="TaxonomyItem.id",
        back_populates="taxonomy",
        primaryjoin="Taxonomy.id == TaxonomyItem.taxonomy_id",
    )
    current_items: List["TaxonomyItem"] = relationship(
        "TaxonomyItem",
        viewonly=True,
        # lazy="select",  # do not always load this
        order_by="TaxonomyItem.id",
        back_populates="taxonomy",
        primaryjoin="and_(Taxonomy.id == TaxonomyItem.taxonomy_id, TaxonomyItem.deleted_on == None)",
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

    @staticmethod
    def get_eager_query() -> Query:
        return Taxonomy.query.options(selectinload(Taxonomy.current_items))


class TaxonomyItem(MODEL, IdMixin, ChangesMixin):
    """Taxonomy Item model."""

    __tablename__ = "TaxonomyItem"

    taxonomy_id: Column = DB.Column(DB.Integer, ForeignKey(Taxonomy.id), nullable=False)
    current_version_id: Column = DB.Column(
        DB.Integer, ForeignKey("TaxonomyItemVersion.id"), nullable=True
    )

    # relationships
    taxonomy: Taxonomy = relationship(
        Taxonomy, innerjoin=True, lazy="selectin", back_populates="items"
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
    related: List["TaxonomyItemRelation"] = relationship(
        "TaxonomyItemRelation",
        lazy="select",
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
    current_related: List["TaxonomyItemRelation"] = relationship(
        "TaxonomyItemRelation",
        viewonly=True,
        lazy="selectin",  # deals better with multiple levels of hierarchy
        order_by="TaxonomyItemRelation.id",
        primaryjoin="and_(TaxonomyItem.id == TaxonomyItemRelation.taxonomy_item_source_id, TaxonomyItemRelation.deleted_on == None)",
    )
    current_ancestors: List["TaxonomyItemRelation"] = relationship(
        "TaxonomyItemRelation",
        viewonly=True,
        lazy="selectin",  # deals better with multiple levels of hierarchy
        order_by="TaxonomyItemRelation.id",
        primaryjoin="and_(TaxonomyItem.id == TaxonomyItemRelation.taxonomy_item_target_id, TaxonomyItemRelation.deleted_on == None)",
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

    @property
    def sort_key(self) -> float:
        if self.current_version is None:
            return 10
        return self.current_version.sort_key

    @property
    def version(self) -> int:
        if self.current_version is None:
            return 0
        return self.current_version.version

    def __init__(
        self,
        taxonomy: Taxonomy,
        **kwargs,
    ) -> None:
        self.taxonomy = taxonomy


class TaxonomyItemVersion(MODEL, IdMixin, NameDescriptionMixin, CreateDeleteMixin):
    """Taxonomy Item version model."""

    __tablename__ = "TaxonomyItemVersion"

    taxonomy_item_id: Column = DB.Column(
        DB.Integer, ForeignKey(TaxonomyItem.id), nullable=False
    )
    version: Column = DB.Column(DB.Integer, nullable=False)
    sort_key: Column = DB.Column(DB.Float, nullable=True)

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
        lazy="select",  # normally loaded from the taxonmy item -> less queries needed
        back_populates="versions",
        primaryjoin=TaxonomyItem.id == taxonomy_item_id,
    )

    def __init__(
        self,
        taxonomy_item: TaxonomyItem,
        version: int,
        name: str,
        description: Optional[str] = None,
        sort_key: Optional[float] = 10,
        **kwargs,
    ) -> None:
        self.taxonomy_item = taxonomy_item
        self.version = version
        self.name = name
        self.description = description
        self.sort_key = sort_key if sort_key is not None else 10


class TaxonomyItemRelation(MODEL, IdMixin, CreateDeleteMixin):
    """Taxonomy Item relation model."""

    __tablename__ = "TaxonomyItemRelation"

    taxonomy_item_source_id: Column = DB.Column(
        DB.Integer, ForeignKey(TaxonomyItem.id), nullable=False
    )

    taxonomy_item_target_id: Column = DB.Column(
        DB.Integer, ForeignKey(TaxonomyItem.id), nullable=False
    )

    # relationships
    taxonomy_item_source: TaxonomyItem = relationship(
        TaxonomyItem,
        lazy="select",  # is nearly always in cache anyway
        back_populates="related",
        primaryjoin=TaxonomyItem.id == taxonomy_item_source_id,
    )

    # relationships
    taxonomy_item_target: TaxonomyItem = relationship(
        TaxonomyItem,
        lazy="select",  # is nearly always in cache anyway
        back_populates="ancestors",
        primaryjoin=TaxonomyItem.id == taxonomy_item_target_id,
    )

    def __init__(
        self,
        taxonomy_item_source: TaxonomyItem,
        taxonomy_item_target: TaxonomyItem,
        **kwargs,
    ) -> None:
        self.taxonomy_item_source = taxonomy_item_source
        self.taxonomy_item_target = taxonomy_item_target

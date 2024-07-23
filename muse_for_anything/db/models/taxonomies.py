"""Module containing ontology object table definitions."""

from typing import Any, Dict, List, Optional, cast
from sqlalchemy.orm.query import Query
from sqlalchemy.sql.schema import ForeignKey, Column, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
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

    namespace_id: Mapped[int] = mapped_column(ForeignKey("Namespace.id"), nullable=False)

    # relationships
    namespace = relationship(Namespace, innerjoin=True, lazy="selectin")

    items: Mapped[List["TaxonomyItem"]] = relationship(
        lazy="select",  # do not always load this
        order_by="TaxonomyItem.id",
        back_populates="taxonomy",
        primaryjoin="Taxonomy.id == TaxonomyItem.taxonomy_id",
    )
    current_items: Mapped[List["TaxonomyItem"]] = relationship(
        viewonly=True,
        # lazy="select",  # do not always load this
        order_by="TaxonomyItem.id",
        back_populates="taxonomy",
        primaryjoin="and_(Taxonomy.id == TaxonomyItem.taxonomy_id, TaxonomyItem.deleted_on == None)",
    )

    referenced_by_types: Mapped[List["rel.OntologyTypeVersionToTaxonomy"]] = relationship(
        lazy="select",
        order_by="OntologyTypeVersionToTaxonomy.id",
        back_populates="taxonomy_target",
        primaryjoin="Taxonomy.id == OntologyTypeVersionToTaxonomy.taxonomy_target_id",
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

    taxonomy_id: Mapped[int] = mapped_column(ForeignKey("Taxonomy.id"), nullable=False)
    current_version_id: Mapped[int] = mapped_column(ForeignKey("TaxonomyItemVersion.id"), nullable=True)

    # relationships
    taxonomy: Mapped[Taxonomy] = relationship(
        innerjoin=True,
        lazy="selectin",
        back_populates="items",
        sync_backref=False,
    )
    current_version: Mapped["TaxonomyItemVersion"] = relationship(
        post_update=True,
        innerjoin=True,
        lazy="joined",
        primaryjoin="TaxonomyItem.current_version_id == TaxonomyItemVersion.id",
    )
    versions: Mapped[List["TaxonomyItemVersion"]] = relationship(
        lazy="select",
        order_by="TaxonomyItemVersion.version",
        back_populates="taxonomy_item",
        primaryjoin="TaxonomyItem.id == TaxonomyItemVersion.taxonomy_item_id",
    )
    related: Mapped[List["TaxonomyItemRelation"]] = relationship(
        lazy="select",
        order_by="TaxonomyItemRelation.id",
        back_populates="taxonomy_item_source",
        primaryjoin="TaxonomyItem.id == TaxonomyItemRelation.taxonomy_item_source_id",
    )
    ancestors: Mapped[List["TaxonomyItemRelation"]] = relationship(
        lazy="select",
        order_by="TaxonomyItemRelation.id",
        back_populates="taxonomy_item_target",
        primaryjoin="TaxonomyItem.id == TaxonomyItemRelation.taxonomy_item_target_id",
    )
    current_related: Mapped[List["TaxonomyItemRelation"]] = relationship(
        viewonly=True,
        lazy="selectin",  # deals better with multiple levels of hierarchy
        order_by="TaxonomyItemRelation.id",
        primaryjoin="and_(TaxonomyItem.id == TaxonomyItemRelation.taxonomy_item_source_id, TaxonomyItemRelation.deleted_on == None)",
    )
    current_ancestors: Mapped[List["TaxonomyItemRelation"]] = relationship(
        viewonly=True,
        lazy="selectin",  # deals better with multiple levels of hierarchy
        order_by="TaxonomyItemRelation.id",
        primaryjoin="and_(TaxonomyItem.id == TaxonomyItemRelation.taxonomy_item_target_id, TaxonomyItemRelation.deleted_on == None)",
    )

    referenced_by_objects: Mapped[List["rel.OntologyObjectVersionToTaxonomyItem"]] = relationship(
        lazy="select",
        order_by="OntologyObjectVersionToTaxonomyItem.id",
        back_populates="taxonomy_item_target",
        primaryjoin="TaxonomyItem.id == OntologyObjectVersionToTaxonomyItem.taxonomy_item_target_id",
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

    taxonomy_item_id: Mapped[int] = mapped_column(ForeignKey("TaxonomyItem.id"), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    sort_key: Mapped[float] = mapped_column(nullable=True)
    
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
    taxonomy_item: Mapped[TaxonomyItem] = relationship(
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

    taxonomy_item_source_id: Mapped[int] = mapped_column(ForeignKey("TaxonomyItem.id"), nullable=False)

    taxonomy_item_target_id: Mapped[int] = mapped_column(ForeignKey("TaxonomyItem.id"), nullable=False)

    # relationships
    taxonomy_item_source: Mapped[TaxonomyItem] = relationship(
        lazy="select",  # is nearly always in cache anyway
        back_populates="related",
        primaryjoin=TaxonomyItem.id == taxonomy_item_source_id,
    )

    taxonomy_item_target: Mapped[TaxonomyItem] = relationship(
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


# late imports for type checker. at the end to avoid circular imports!
from . import object_relation_tables as rel

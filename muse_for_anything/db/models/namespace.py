"""Module containing the namespace table definitions."""

from sqlalchemy.sql.schema import Column, Index
from sqlalchemy.ext.declarative import declared_attr
from ..db import DB, MODEL
from .model_helpers import (
    FULLTEXT_INDEX_PARAMS,
    ChangesMixin,
    IdMixin,
    UniqueNameDescriptionMixin,
)


class Namespace(IdMixin, UniqueNameDescriptionMixin, ChangesMixin, MODEL):
    """Namespace Table model."""

    __tablename__ = "Namespace"

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

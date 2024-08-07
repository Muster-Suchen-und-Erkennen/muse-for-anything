from datetime import datetime, timezone
from typing import Any, Sequence
from sqlalchemy import DateTime
from sqlalchemy.sql.elements import literal
from sqlalchemy.sql.schema import Column
from sqlalchemy.types import Unicode, UnicodeText
from sqlalchemy.orm import Mapped, mapped_column

from ...util.import_helpers import get_all_classes_of_module

from ..db import DB, MODEL


FULLTEXT_INDEX_PARAMS = {"mysql_prefix": "FULLTEXT", "postgresql_using": "gin"}


class ExistsMixin:
    @classmethod
    def exists(cls, query_filter: Sequence[Any] = tuple()):
        return (
            DB.session.query(literal(True))
            .filter(cls.query.filter(*query_filter).exists())
            .scalar()
        )


class IdMixin:
    """Add an 'id' column that is the primary key for this table."""

    id: Mapped[int] = mapped_column(primary_key=True)


class NameDescriptionMixin:
    """Add a 'name' and 'description' column to the table."""

    name: Mapped[str] = mapped_column(
        DB.Unicode, nullable=False, index=True, info={"collate": "NOCASE"}
    )
    description: Mapped[str] = mapped_column(DB.UnicodeText, nullable=True, index=True)


class UniqueNameDescriptionMixin:
    """Add a 'name' (with a unique constraint) and 'description' column to the table."""

    name: Mapped[str] = mapped_column(
        DB.Unicode, nullable=False, unique=True, index=True, info={"collate": "NOCASE"}
    )
    description: Mapped[str] = mapped_column(DB.UnicodeText, nullable=True, index=True)


class CreateDeleteMixin:
    """Add the columns 'created_on' and 'deleted_on' to track creation and deletion of immutable database entries."""

    created_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_on is not None


class ChangesMixin(CreateDeleteMixin):
    """Add the columns 'created_on', 'updated_on' and 'deleted_on' to track changes to the database entries."""

    updated_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


__all__ = list(get_all_classes_of_module(__name__))

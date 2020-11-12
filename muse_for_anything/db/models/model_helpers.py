from datetime import datetime
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql import func

from ...util.import_helpers import get_all_classes_of_module

from ..db import DB, MODEL


FULLTEXT_INDEX_PARAMS = {"mysql_prefix": "FULLTEXT", "postgresql_using": "gin"}


class IdMixin:
    """Add an 'id' column that is the primary key for this table."""

    id: Column = DB.Column(DB.Integer, primary_key=True)


class NameDescriptionMixin:
    """Add a 'name' and 'description' column to the table."""

    name: Column = DB.Column(DB.Unicode, nullable=False, index=True)
    description: Column = DB.Column(DB.UnicodeText, nullable=True, index=True)


class UniqueNameDescriptionMixin:
    """Add a 'name' (with a unique constraint) and 'description' column to the table."""

    name: Column = DB.Column(DB.Unicode, nullable=False, unique=True, index=True)
    description: Column = DB.Column(DB.UnicodeText, nullable=True, index=True)


class CreateDeleteMixin:
    """Add the columns 'created_on' and 'deleted_on' to track creation and deletion of immutable database entries."""

    created_on: Column = DB.Column(DB.DateTime, default=datetime.utcnow, nullable=False)
    deleted_on: Column = DB.Column(DB.DateTime, nullable=True)


class ChangesMixin(CreateDeleteMixin):
    """Add the columns 'created_on', 'updated_on' and 'deleted_on' to track changes to the database entries."""

    updated_on: Column = DB.Column(DB.DateTime, onupdate=datetime.utcnow, nullable=False)


__all__ = list(get_all_classes_of_module(__name__))

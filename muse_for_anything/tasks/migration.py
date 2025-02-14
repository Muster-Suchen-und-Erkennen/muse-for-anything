# ==============================================================================
# MIT License
#
# Copyright (c) 2024 Jan Weber
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

from celery.utils.log import get_task_logger
from flask import url_for
from flask.globals import current_app
from sqlalchemy.sql.expression import select

from muse_for_anything.api.v1_api.constants import TYPE_VERSION_RESOURCE
from muse_for_anything.api.v1_api.ontology_object_validation import validate_object
from muse_for_anything.db.db import DB
from muse_for_anything.db.models.object_relation_tables import (
    OntologyObjectVersionToObject,
    OntologyObjectVersionToTaxonomyItem,
)
from muse_for_anything.db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectTypeVersion,
    OntologyObjectVersion,
)
from muse_for_anything.json_migrations.data_migration import DataMigrator, JsonSchema

from ..celery import CELERY, FlaskTask

_name = "muse_for_anything.tasks.migration"

TASK_LOGGER = get_task_logger(_name)

DEFAULT_BATCH_SIZE = 20


@CELERY.task(name=f"{_name}.run_migration", bind=True, ignore_result=True)
def run_migration(self: FlaskTask, data_object_id: int, host_url: str):
    """This Celery background tasks migrates data stored in an object to the
    current type version. It creates a new object version for each update
    until the current type version is reached.

    Args:
        self (FlaskTask):
        data_object_id (int): The id of the object to be migrated
        host_url (str): URL where migration was initiated
    """
    q = select(OntologyObject).where(OntologyObject.id == data_object_id)
    data_object = DB.session.execute(q).scalars().first()
    if not data_object:
        TASK_LOGGER.warning(f"OntologyObject with ID {data_object_id} not found.")
        return

    # Type versions
    current_version = data_object.current_version.ontology_type_version
    target_version = data_object.ontology_type.current_version

    if target_version == current_version:
        TASK_LOGGER.info(
            f"OntologyObject with ID {data_object_id} is already up-to-date."
        )
        return

    try:
        with current_app.test_request_context(host_url, method="GET"):
            _migrate_object(
                data_object=data_object,
                current_version=current_version,
                target_version=target_version,
            )
    except ValueError as error:
        TASK_LOGGER.error(
            f"""
            OntologyObject {data_object.name} ({data_object_id}) could not be migrated.
            {str(error)}
            """
        )
        DB.session.rollback()

    except Exception as error:
        TASK_LOGGER.error(
            f"""
            Error during migration of OntologyObject {data_object.name} ({data_object_id}).
            {str(error)}
        """
        )
        DB.session.rollback()


def _migrate_object(
    data_object: OntologyObject,
    current_version: OntologyObjectTypeVersion,
    target_version: OntologyObjectTypeVersion,
):
    """Migrates an OntologyObject to the newest type version.

    Args:
        data_object (OntologyObject): A data object from the repository
        current_version (OntologyObjectTypeVersion): Current type version
        target_version (OntologyObjectTypeVersion): Latest type version
        host_url (str): URL where migration was initiated
    """
    while current_version != target_version:
        next_version = _get_next_version(
            data_object=data_object, current_version=current_version
        )

        if next_version is None:
            break

        updated_data = DataMigrator.migrate_data(
            data=data_object.current_version.data,
            source_schema=JsonSchema(
                schema_url=url_for(
                    TYPE_VERSION_RESOURCE,
                    namespace=str(current_version.ontology_type.namespace_id),
                    object_type=str(current_version.object_type_id),
                    version=str(current_version.version),
                    _external=True,
                ),
                schema=current_version.data,
            ),
            target_schema=JsonSchema(
                schema_url=url_for(
                    TYPE_VERSION_RESOURCE,
                    namespace=str(next_version.ontology_type.namespace_id),
                    object_type=str(next_version.object_type_id),
                    version=str(next_version.version),
                    _external=True,
                ),
                schema=current_version.data,
            ),
        )
        _save_new_version(
            data_object=data_object, next_version=next_version, updated_data=updated_data
        )

        current_version = next_version


def _get_next_version(
    data_object: OntologyObject, current_version: OntologyObjectTypeVersion
):
    """Retrieve the next type version of an object.

    Args:
        data_object (OntologyObject): Object of the repository
        current_version (OntologyObjectTypeVersion): Current type version

    Returns:
        OntologyObjectTypeVersion: Next type version of the data object
    """
    next_q = (
        select(OntologyObjectTypeVersion)
        .where(OntologyObjectTypeVersion.object_type_id == data_object.object_type_id)
        .where(OntologyObjectTypeVersion.version > current_version.version)
        .where(OntologyObjectTypeVersion.deleted_on == None)
        .order_by(OntologyObjectTypeVersion.version.asc())
        .limit(1)
    )
    return DB.session.execute(next_q).scalars().first()


def _save_new_version(
    data_object: OntologyObject, next_version: OntologyObjectTypeVersion, updated_data
):
    """Saves a new ObjectVersion to the database with the migrated data

    Args:
        data_object (OntologyObject): Object to be updated
        next_version (OntologyObjectTypeVersion): New version of the object
        updated_data: New data value to be saved to database
    """
    name = data_object.name
    description = data_object.description
    object_version = OntologyObjectVersion(
        object=data_object,
        type_version=next_version,
        version=data_object.version + 1,
        name=name,
        description=description,
        data=updated_data,
    )
    DB.session.add(object_version)

    # validate against object type
    # and validate and extract resource references
    metadata = validate_object(
        object_version=object_version,
        type_version=next_version,
    )
    # add references
    for object_ref in metadata.referenced_objects:
        object_relation = OntologyObjectVersionToObject(
            object_version_source=object_version, object_target=object_ref
        )
        DB.session.add(object_relation)
    for taxonomy_item in metadata.referenced_taxonomy_items:
        taxonomy_item_relation = OntologyObjectVersionToTaxonomyItem(
            object_version_source=object_version,
            taxonomy_item_target=taxonomy_item,
        )
        DB.session.add(taxonomy_item_relation)

    data_object.update(
        name=name,
        description=description,
    )
    data_object.current_version = object_version
    DB.session.add(data_object)
    DB.session.commit()

    TASK_LOGGER.info(
        f"OntologyObject {data_object.name} migrated to version {next_version.version}."
    )

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
from flask.globals import current_app
from sqlalchemy.sql.expression import select

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
from muse_for_anything.json_migrations.data_migration import migrate_data
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
    """
    q = select(OntologyObject).where(OntologyObject.id == data_object_id)
    data_object = DB.session.execute(q).scalars().first()
    if not data_object:
        TASK_LOGGER.warning(f"OntologyObject with ID {data_object_id} not found.")
        return
    # Data and type version from object
    data_object_version = data_object.current_version
    data_entry = data_object_version.data
    current_version = data_object_version.ontology_type_version

    # Latest type version
    target_version = data_object.ontology_type.current_version

    if target_version == current_version:
        TASK_LOGGER.info(
            f"OntologyObject with ID {data_object_id} is already up-to-date."
        )
        return

    # Get next type version
    next_q = (
        select(OntologyObjectTypeVersion)
        .where(OntologyObjectTypeVersion.object_type_id == data_object.object_type_id)
        .where(OntologyObjectTypeVersion.version > current_version.version)
        .where(OntologyObjectTypeVersion.deleted_on == None)
        .order_by(OntologyObjectTypeVersion.version.asc())
    )
    next_version = DB.session.execute(next_q).scalars().first()

    try:
        updated_data = None
        with current_app.test_request_context(host_url, method="GET"):
            updated_data = migrate_data(
                data=data_entry,
                source_schema=current_version.data,
                target_schema=next_version.data,
            )
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

            # update existing object
            data_object.update(
                name=name,
                description=description,
            )
            DB.session.add(object_version)
            data_object.current_version = object_version
            DB.session.add(data_object)
            DB.session.commit()
        TASK_LOGGER.info(
            f"OntologyObject with ID {data_object_id} migrated to version {next_version.version}."
        )

        if next_version != target_version:
            run_migration.apply_async(args=[data_object_id, host_url])
    except ValueError:
        TASK_LOGGER.warning(
            f"OntologyObject with ID {data_object_id} could not be migrated."
        )
        DB.session.rollback()
        return
    except Exception:
        TASK_LOGGER.error(
            f"Error during migration of OntologyObject {data_object_id}. Likely due to validation error."
        )

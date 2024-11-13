from celery.utils.log import get_task_logger
from sqlalchemy.sql.expression import select

from muse_for_anything.api.v1_api.constants import UPDATE
from muse_for_anything.api.v1_api.ontology_object_validation import validate_object
from muse_for_anything.db.db import DB
from muse_for_anything.db.models.object_relation_tables import (
    OntologyObjectVersionToObject,
    OntologyObjectVersionToTaxonomyItem,
)
from muse_for_anything.db.models.ontology_objects import (
    OntologyObject,
    OntologyObjectVersion,
)
from muse_for_anything.json_migrations.data_migration import migrate_data
from muse_for_anything.oso_helpers import FLASK_OSO
from ..celery import CELERY, FlaskTask

_name = "muse_for_anything.tasks.migration"

TASK_LOGGER = get_task_logger(_name)

DEFAULT_BATCH_SIZE = 20


@CELERY.task(name=f"{_name}.run_schema_match", bind=True, ignore_result=True)
def run_schema_match(self: FlaskTask, data_objects_ids: list):
    # TODO: Run migration later button click
    for id in data_objects_ids:
        q = select(OntologyObject).where(OntologyObject.id == id)
        data_object = DB.session.execute(q).scalars().first()
        data_object_version = data_object.current_version
        data_entry = data_object_version.data
        data_object_type_version = data_object_version.ontology_type_version
        source_schema = data_object_type_version.data
        data_object_type_current_version = data_object.ontology_type.current_version
        target_schema = data_object_type_current_version.data
        try:
            updated_data = migrate_data(
                data=data_entry, source_schema=source_schema, target_schema=target_schema
            )

            name = data_object.name
            description = data_object.description

            object_version = OntologyObjectVersion(
                object=data_object,
                type_version=data_object_type_current_version,
                version=data_object.version + 1,
                name=name,
                description=description,
                data=updated_data,
            )

            # validate against object type and validate and extract resource references
            metadata = validate_object(
                object_version=object_version,
                type_version=data_object_type_current_version,
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
            data_object.current_version = object_version
            DB.session.add(object_version)
            DB.session.add(data_object)
            DB.session.commit()
        except ValueError:
            # TODO: Handle errors correctly
            return f"Object with id {id} could not be migrated"
    return "Task completed"

from typing import Optional

from muse_for_anything.api.v1_api.constants import OBJECT_REL_TYPE, TAXONOMY_REL_TYPE

from .data_migration import DataMigrator, JsonSchema


class TaxRefToTaxRef(DataMigrator):

    source_types = {"resourceReference"}
    target_types = {"resourceReference"}

    def basic_check_concrete_schema_change(
        self, source_type: str, target_type: str, source_schema: dict, target_schema: dict
    ) -> bool:
        if source_type not in self.source_types:
            return False

        source_ref_type = source_schema.get("referenceType", None)
        target_ref_type = target_schema.get("referenceType", None)

        if not (source_ref_type == target_ref_type == TAXONOMY_REL_TYPE):
            return False  # not a taxonomy reference

        source_ref_key = source_schema.get("referenceKey", {})
        target_ref_key = target_schema.get("referenceKey", {})

        source_namespace = source_ref_key["namespaceId"]
        target_namespace = target_ref_key["namespaceId"]
        source_taxonomy = source_ref_key["taxonomyId"]
        target_taxonomy = target_ref_key["taxonomyId"]

        # check if equal
        if (source_namespace, source_taxonomy) != (target_namespace, target_taxonomy):
            return False

        # check if not None
        return target_taxonomy and target_namespace

    def migrate_data_concrete(
        self,
        data,
        source_type: str,
        target_type: str,
        source_schema: JsonSchema,
        target_schema: JsonSchema,
        *,
        depth: int = 0,
    ) -> Optional[dict]:
        if data is None and target_schema.is_nullable:
            return None

        if data is None:
            raise ValueError(
                "Transformation from None to taxonomy reference without default value is not possible!"
            )

        if not isinstance(data, dict):
            raise ValueError("Cannot convert data to a taxonomy reference!")

        target_namespace = target_schema.schema.get("referenceKey", {})["namespaceId"]
        target_taxonomy = target_schema.schema.get("referenceKey", {})["taxonomyId"]

        if not target_namespace or not target_taxonomy:
            raise ValueError("Could not determine target namespace and taxonomy!")

        if data.get("namespaceId", None) != target_namespace:
            raise ValueError("Could not convert a reference from another namespace!")

        if data.get("taxonomyId", None) != target_taxonomy:
            raise ValueError("Could not convert a reference from another taxonomy!")

        if not data.get("taxonomyItemId", None):
            raise ValueError("Data is not a taxonomy item reference!")

        return data  # nothing to migrate


class ObjectRefToObjectRef(DataMigrator):

    source_types = {"resourceReference"}
    target_types = {"resourceReference"}

    def basic_check_concrete_schema_change(
        self, source_type: str, target_type: str, source_schema: dict, target_schema: dict
    ) -> bool:
        if source_type not in self.source_types:
            return False

        source_ref_type = source_schema.get("referenceType", None)
        target_ref_type = target_schema.get("referenceType", None)

        if not (source_ref_type == target_ref_type == OBJECT_REL_TYPE):
            return False  # not an object reference

        source_ref_key = source_schema.get("referenceKey", {})
        target_ref_key = target_schema.get("referenceKey", {})

        if source_ref_key and target_ref_key:
            source_namespace = source_schema["referenceKey"]["namespaceId"]
            target_namespace = target_schema["referenceKey"]["namespaceId"]
            source_type_id = source_schema["referenceKey"]["typeId"]
            target_type_id = target_schema["referenceKey"]["typeId"]

            if (source_namespace, source_type_id) != (target_namespace, target_type_id):
                return False

            # check if not None
            return target_type_id and target_namespace

        return True

    def migrate_data_concrete(
        self,
        data,
        source_type: str,
        target_type: str,
        source_schema: JsonSchema,
        target_schema: JsonSchema,
        *,
        depth: int = 0,
    ) -> Optional[dict]:
        if data is None and target_schema.is_nullable:
            return None

        if data is None:
            raise ValueError(
                "Transformation from None to taxonomy reference without default value is not possible!"
            )

        if not isinstance(data, dict):
            raise ValueError("Cannot convert data to a taxonomy reference!")

        target_key = target_schema.schema.get("referenceKey", {})

        data_namespace = data.get("namespaceId", None)

        data_type_id = data.get("typeId", None)

        if not data_namespace:
            raise ValueError("Data is missing a namespace id!")

        if not data_type_id:
            raise ValueError("Data is missing an object type id!")

        if not data.get("objectId", None):
            raise ValueError("Data is not an object reference!")

        if target_key:
            target_namespace = target_key["namespaceId"]
            target_taxonomy = target_key["typeId"]

            if data_namespace != target_namespace:
                raise ValueError("Could not convert a reference from another namespace!")

            if data_type_id != target_taxonomy:
                raise ValueError(
                    "Could not convert a reference from another object type!"
                )

        return data  # nothing to migrate

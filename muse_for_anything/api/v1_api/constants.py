"""Constants to be used for the API."""


# actions ######################################################################

GET = "GET"
CREATE = "CREATE"
UPDATE = "EDIT"
EDIT = UPDATE
DELETE = "DELETE"
RESTORE = "RESTORE"


# special relations ############################################################

COLLECTION_REL = "collection"

PAGE_REL = "page"

FIRST_REL = "first"
LAST_REL = "last"

PREV_REL = "prev"
NEXT_REL = "next"

UP_REL = "up"
NAV_REL = "nav"

POST_REL = "post"
PUT_REL = "put"
DELETE_REL = "delete"

CREATE_REL = "create"
UPDATE_REL = "update"
RESTORE_REL = "restore"

NEW_REL = "new"
CHANGED_REL = "changed"


# relation types ###############################################################

NAMESPACE_REL_TYPE = "ont-namespace"

TYPE_REL_TYPE = "ont-type"
TYPE_VERSION_REL_TYPE = "ont-type-version"

OBJECT_REL_TYPE = "ont-object"
OBJECT_VERSION_REL_TYPE = "ont-object-version"

TAXONOMY_REL_TYPE = "ont-taxonomy"

TAXONOMY_ITEM_REL_TYPE = "ont-taxonomy-item"
TAXONOMY_ITEM_VERSION_REL_TYPE = "ont-taxonomy-item-version"
PARENT_REL = "parent"
CHILD_REL = "child"

TAXONOMY_ITEM_RELATION_REL_TYPE = "ont-taxonomy-item-relation"
SOURCE_REL = "source"
TARGET_REL = "target"


# link to relations ############################################################

NAMESPACE_EXTRA_LINK_RELATIONS = (OBJECT_REL_TYPE, TYPE_REL_TYPE, TAXONOMY_REL_TYPE)


TYPE_PAGE_EXTRA_LINK_RELATIONS = (NAMESPACE_REL_TYPE,)
TYPE_EXTRA_LINK_RELATIONS = (
    NAMESPACE_REL_TYPE,
    TYPE_VERSION_REL_TYPE,
    OBJECT_REL_TYPE,
    f"{CREATE_REL}_{OBJECT_REL_TYPE}",
)

TYPE_VERSION_PAGE_EXTRA_LINK_RELATIONS = (NAMESPACE_REL_TYPE,)
TYPE_VERSION_EXTRA_LINK_RELATIONS = (NAMESPACE_REL_TYPE, TYPE_REL_TYPE)


OBJECT_PAGE_EXTRA_LINK_RELATIONS = (NAMESPACE_REL_TYPE,)
OBJECT_EXTRA_LINK_RELATIONS = (
    NAMESPACE_REL_TYPE,
    OBJECT_VERSION_REL_TYPE,
    TYPE_REL_TYPE,
)

OBJECT_VERSION_PAGE_EXTRA_LINK_RELATIONS = (NAMESPACE_REL_TYPE, TYPE_REL_TYPE)
OBJECT_VERSION_EXTRA_LINK_RELATIONS = (
    NAMESPACE_REL_TYPE,
    OBJECT_REL_TYPE,
    TYPE_VERSION_REL_TYPE,
)


TAXONOMY_PAGE_EXTRA_LINK_RELATIONS = (NAMESPACE_REL_TYPE,)
TAXONOMY_EXTRA_LINK_RELATIONS = (
    NAMESPACE_REL_TYPE,
    TAXONOMY_ITEM_REL_TYPE,
    f"{CREATE_REL}_{TAXONOMY_ITEM_REL_TYPE}",
)

TAXONOMY_ITEM_PAGE_EXTRA_LINK_RELATIONS = (
    NAMESPACE_REL_TYPE,
    TAXONOMY_REL_TYPE,
)
TAXONOMY_ITEM_EXTRA_LINK_RELATIONS = (
    NAMESPACE_REL_TYPE,
    TAXONOMY_REL_TYPE,
    TAXONOMY_ITEM_RELATION_REL_TYPE,
    TAXONOMY_ITEM_VERSION_REL_TYPE,
    f"{CREATE_REL}_{TAXONOMY_ITEM_RELATION_REL_TYPE}",
)

TAXONOMY_ITEM_VERSION_PAGE_EXTRA_LINK_RELATIONS = (
    NAMESPACE_REL_TYPE,
    TAXONOMY_REL_TYPE,
)
TAXONOMY_ITEM_VERSION_EXTRA_LINK_RELATIONS = (
    NAMESPACE_REL_TYPE,
    TAXONOMY_REL_TYPE,
    TAXONOMY_ITEM_RELATION_REL_TYPE,
)

TAXONOMY_ITEM_RELATION_PAGE_EXTRA_LINK_RELATIONS = (
    NAMESPACE_REL_TYPE,
    TAXONOMY_REL_TYPE,
)
TAXONOMY_ITEM_RELATION_EXTRA_LINK_RELATIONS = (
    NAMESPACE_REL_TYPE,
    TAXONOMY_REL_TYPE,
)

# key variables ################################################################

# normal keys
VERSION_KEY = "version"

NAMESPACE_ID_KEY = "namespaceId"

OBJECT_ID_KEY = "objectId"

TYPE_ID_KEY = "typeId"

TAXONOMY_ID_KEY = "taxonomyId"
TAXONOMY_ITEM_ID_KEY = "taxonomyItemId"
TAXONOMY_ITEM_RELATION_ID_KEY = "relationId"


# query keys
ITEM_COUNT_QUERY_KEY = "item-count"

TYPE_ID_QUERY_KEY = "type-id"
TYPE_EXTRA_ARG = "type"


# key defaults
ITEM_COUNT_DEFAULT = "25"


# schemas ######################################################################

NAMESPACE_SCHEMA = "Namespace"

TYPE_SCHEMA = "TypeSchema"

TAXONOMY_SCHEMA = "TaxonomySchema"
TAXONOMY_ITEM_SCHEMA = "TaxonomyItemSchema"
TAXONOMY_ITEM_RELATION_SCHEMA = "TaxonomyRelationSchema"
TAXONOMY_ITEM_RELATION_POST_SCHEMA = "TaxonomyItemRelationPostSchema"


# endpoints ####################################################################

SCHEMA_RESOURCE = "api-v1.ApiSchemaView"
TYPE_SCHEMA_RESOURCE = "api-v1.TypeSchemaView"


NAMESPACE_PAGE_RESOURCE = "api-v1.NamespacesView"
NAMESPACE_RESOURCE = "api-v1.NamespaceView"


TYPE_PAGE_RESOURCE = "api-v1.TypesView"
TYPE_RESOURCE = "api-v1.TypeView"

TYPE_VERSION_PAGE_RESOURCE = "api-v1.TypeVersionsView"
TYPE_VERSION_RESOURCE = "api-v1.TypeVersionView"


OBJECT_PAGE_RESOURCE = "api-v1.ObjectsView"
OBJECT_RESOURCE = "api-v1.ObjectView"

OBJECT_VERSION_PAGE_RESOURCE = "api-v1.ObjectVersionsView"
OBJECT_VERSION_RESOURCE = "api-v1.ObjectVersionView"


TAXONOMY_PAGE_RESOURCE = "api-v1.TaxonomiesView"
TAXONOMY_RESOURCE = "api-v1.TaxonomyView"

TAXONOMY_ITEM_PAGE_RESOURCE = "api-v1.TaxonomyItemsView"
TAXONOMY_ITEM_RESOURCE = "api-v1.TaxonomyItemView"

TAXONOMY_ITEM_VERSION_PAGE_RESOURCE = "api-v1.TaxonomyItemVersionsView"
TAXONOMY_ITEM_VERSION_RESOURCE = "api-v1.TaxonomyItemVersionView"

TAXONOMY_ITEM_RELATION_PAGE_RESOURCE = "api-v1.TaxonomyItemRelationsView"
TAXONOMY_ITEM_RELATION_RESOURCE = "api-v1.TaxonomyItemRelationView"

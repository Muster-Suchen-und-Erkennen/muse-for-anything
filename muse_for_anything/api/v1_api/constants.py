"""Constants to be used for the API."""

# actions ######################################################################

GET = "GET"
CREATE = "CREATE"
UPDATE = "EDIT"
EDIT = UPDATE
DELETE = "DELETE"
RESTORE = "RESTORE"
EXPORT = "EXPORT"


# special relations ############################################################

COLLECTION_REL = "collection"

PAGE_REL = "page"

FIRST_REL = "first"
LAST_REL = "last"

PREV_REL = "prev"
NEXT_REL = "next"

UP_REL = "up"
NAV_REL = "nav"
LATEST_REL = "latest"

POST_REL = "post"
PUT_REL = "put"
DELETE_REL = "delete"

CREATE_REL = "create"
UPDATE_REL = "update"
RESTORE_REL = "restore"
EXPORT_REL = "export"

NEW_REL = "new"
CHANGED_REL = "changed"
DELETED_REL = "deleted"

DANGER_REL = "danger"
PERMANENT_REL = "permanent"

LOGIN_REL = "login"
REFRESH_TOKEN_REL = "refresh"
FRESH_LOGIN_REL = "fresh-login"
LOGOUT_REL = "logout"

REQUIRES_FRESH_LOGIN_REL = "requires-fresh-login"


# relation types ###############################################################

DATA_EXPORT_REL_TYPE = "ont-export"

SCHEMA_REL_TYPE = "schema"

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

# auth related rels

USER_REL_TYPE = "user"
USER_ROLE_REL_TYPE = "user-role"
USER_GRANT_REL_TYPE = "user-grant"


# link to relations ############################################################

NAMESPACE_EXTRA_LINK_RELATIONS = (OBJECT_REL_TYPE, TYPE_REL_TYPE, TAXONOMY_REL_TYPE)


TYPE_PAGE_EXTRA_LINK_RELATIONS = (NAMESPACE_REL_TYPE,)
TYPE_EXTRA_LINK_RELATIONS = (
    NAMESPACE_REL_TYPE,
    TYPE_VERSION_REL_TYPE,
    LATEST_REL,
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

# Auth related

USER_EXTRA_LINK_RELATIONS = (
    USER_ROLE_REL_TYPE,
    # USER_GRANT_REL_TYPE,
    f"{CREATE_REL}_{USER_ROLE_REL_TYPE}",
)
USER_ROLE_EXTRA_LINK_RELATIONS = tuple()
USER_GRANT_EXTRA_LINK_RELATIONS = tuple()

# key variables ################################################################

# normal keys
VERSION_KEY = "version"

NAMESPACE_ID_KEY = "namespaceId"

OBJECT_ID_KEY = "objectId"
OBJECT_VERSION_KEY = "objectVersion"

TYPE_ID_KEY = "typeId"
TYPE_VERSION_KEY = "typeVersion"

TAXONOMY_ID_KEY = "taxonomyId"
TAXONOMY_ITEM_ID_KEY = "taxonomyItemId"
TAXONOMY_ITEM_RELATION_ID_KEY = "relationId"


# query keys
ITEM_COUNT_QUERY_KEY = "item-count"

TYPE_ID_QUERY_KEY = "type-id"
TYPE_EXTRA_ARG = "type"


# key defaults
ITEM_COUNT_DEFAULT = "25"


# Auth related

USER_ID_KEY = "username"

USER_ROLE_ID_KEY = "userRole"
USER_GRANT_ID_KEY = "userGrantId"

VIEW_ALL_USERS_EXTRA_ARG = "VIEW_ALL_USERS"  # extra argument only for authentication!


# schemas ######################################################################

NAMESPACE_SCHEMA = "Namespace"

NAMESPACE_EXPORT_SCHEMA = "NamespaceExportSchema"

TYPE_SCHEMA = "OntologyType"
TYPE_SCHEMA_POST = "TypeSchema"

TAXONOMY_SCHEMA = "TaxonomySchema"
TAXONOMY_ITEM_SCHEMA = "TaxonomyItemSchema"
TAXONOMY_ITEM_RELATION_SCHEMA = "TaxonomyRelationSchema"
TAXONOMY_ITEM_RELATION_POST_SCHEMA = "TaxonomyItemRelationPostSchema"

# Auth related
USER_SCHEMA = "UserSchema"
USER_CREATE_SCHEMA = "UserCreateSchema"
USER_UPDATE_SCHEMA = "UserUpdateSchema"

USER_ROLE_SCHEMA = "UserRoleSchema"
USER_ROLE_POST_SCHEMA = "UserRolePostSchema"
USER_GRANT_SCHEMA = "UserGrantSchema"


# endpoints ####################################################################

SCHEMA_RESOURCE = "api-v1.ApiSchemaView"
TYPE_SCHEMA_RESOURCE = "api-v1.TypeSchemaView"


NAMESPACE_PAGE_RESOURCE = "api-v1.NamespacesView"
NAMESPACE_RESOURCE = "api-v1.NamespaceView"
NAMESPACE_EXPORT_RESOURCE = "api-v1.NamespaceExportView"


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

# Auth related
USER_PAGE_RESOURCE = "api-v1.UsersView"
USER_RESOURCE = "api-v1.UserView"

USER_ROLE_COLLECTION_RESOURCE = "api-v1.UserRolesView"
USER_ROLE_RESOURCE = "api-v1.UserRoleView"

USER_GRANT_PAGE_RESOURCE = "api-v1.UserGrantsView"
USER_GRANT_RESOURCE = "api-v1.UserGrantView"

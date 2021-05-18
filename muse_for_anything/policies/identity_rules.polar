# resource identity rules
is_namespace(_resource: Namespace);
is_type(_resource: OntologyObjectType);
is_type_version(_resource: OntologyObjectTypeVersion);
is_object(_resource: OntologyObject);
is_object_version(_resource: OntologyObjectVersion);
is_taxonomy(_resource: Taxonomy);
is_taxonomy_item(_resource: TaxonomyItem);
is_taxonomy_item_version(_resource: TaxonomyItemVersion);
is_taxonomy_item_relation(_resource: TaxonomyItemRelation);

# general user identity rules
has_role(user: User, role: String) if
    user.has_role(role);

# admin rules
is_admin(user: User) if
    has_role(user, "admin");

is_namespace_admin(user: User) if
    has_role(user, "ont-namespace_admin");

is_type_admin(user: User) if
    has_role(user, "ont-type_admin");

is_taxonomy_admin(user: User) if
    has_role(user, "ont-taxonomy_admin");

is_object_admin(user: User) if
    has_role(user, "ont-object_admin");

# editor rules
is_editor(user: User) if
    has_role(user, "editor");

is_namespace_editor(user: User) if
    has_role(user, "ont-namespace_editor");

is_type_editor(user: User) if
    has_role(user, "ont-type_editor");

is_taxonomy_editor(user: User) if
    has_role(user, "ont-taxonomy_editor");

is_object_editor(user: User) if
    has_role(user, "ont-object_editor");

# creator rules
is_creator(user: User) if
    has_role(user, "creator");

is_namespace_creator(user: User) if
    has_role(user, "ont-namespace_creator");

is_type_creator(user: User) if
    has_role(user, "ont-type_creator");

is_taxonomy_creator(user: User) if
    has_role(user, "ont-taxonomy_creator");

is_object_creator(user: User) if
    has_role(user, "ont-object_creator");


# resource specific identity rules
is_admin(user: User, resource) if
    is_owner(user, resource);

is_owner(user: User, resource) if
    has_resource_role(user, "owner", resource);

is_editor(user: User, resource) if
    has_resource_role(user, "editor", resource);

is_creator(user: User, resource) if
    has_resource_role(user, "creator", resource);

# type specific resource roles
is_admin(user: User, type: String, resource) if
    is_admin(user, resource) or is_owner(user, type, resource);

is_owner(user: User, type: String, resource) if
    is_owner(user, resource) or has_resource_role(user, "owner", type, resource);

is_editor(user: User, type: String, resource) if
    is_editor(user, resource) or has_resource_role(user, "editor", type, resource);

is_creator(user: User, type: String, resource) if
    is_creator(user, resource) or has_resource_role(user, "creator", type, resource);


# actual resource roles
user_object_has_resource_role(user: User, role: String, resource) if
    # print("Test user for role", user, role, resource) and
    user.has_resource_role(role, resource);

has_resource_role(user: User, role: String, resource: Namespace) if
    user_object_has_resource_role(user, role, resource);

has_resource_role(user: User, role: String, resource_type: String, resource: Namespace) if
    has_resource_role(user, new String().join([resource_type, "_", role]), resource);

has_resource_role(user: User, role: String, resource: OntologyObjectType) if
    user_object_has_resource_role(user, role, resource)
    or has_resource_role(user, role, resource.namespace)
    or has_resource_role(user, role, "ont-type", resource.namespace);

has_resource_role(user: User, role: String, resource: OntologyObjectTypeVersion) if
    has_resource_role(user, role, resource.ontology_type);

has_resource_role(user: User, role: String, resource: OntologyObject) if
    user_object_has_resource_role(user, role, resource)
    or has_resource_role(user, role, resource.namespace)
    or has_resource_role(user, role, "ont-object", resource.namespace);

has_resource_role(user: User, role: String, resource: OntologyObjectVersion) if
    has_resource_role(user, role, resource.ontology_object);

has_resource_role(user: User, role: String, resource: Taxonomy) if
    user_object_has_resource_role(user, role, resource)
    or has_resource_role(user, role, resource.namespace)
    or has_resource_role(user, role, "ont-taxonomy", resource.namespace);

has_resource_role(user: User, role: String, resource: TaxonomyItem) if
    has_resource_role(user, role, resource.taxonomy);

has_resource_role(user: User, role: String, resource: TaxonomyItemVersion) if
    has_resource_role(user, role, resource.taxonomy_item);

has_resource_role(user: User, role: String, resource: TaxonomyItemRelation) if
    has_resource_role(user, role, resource.taxonomy_item_source);

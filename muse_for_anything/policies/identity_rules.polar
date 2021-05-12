# general identity rules
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
is_owner(user: User, resource) if
    has_resource_role(user, "owner", resource);

is_editor(user: User, resource) if
    has_resource_role(user, "editor", resource);

user_object_has_resource_role(user: User, role: String, resource) if
    user.has_resource_role(role, resource);


has_resource_role(user: User, role: String, resource: Namespace) if
    user_object_has_resource_role(user, role, resource);

has_resource_role(user: User, role: String, resource: OntologyObjectType) if
    user_object_has_resource_role(user, role, resource)
    or has_resource_role(user, role, resource.namespace)
    or has_resource_role(user, "ont-type_" + role, resource.namespace);

has_resource_role(user: User, role: String, resource: OntologyObjectTypeVersion) if
    has_resource_role(user, role, resource.ontology_type);

has_resource_role(user: User, role: String, resource: OntologyObject) if
    user_object_has_resource_role(user, role, resource)
    or has_resource_role(user, role, resource.namespace)
    or has_resource_role(user, "ont-object_" + role, resource.namespace);

has_resource_role(user: User, role: String, resource: OntologyObjectVersion) if
    has_resource_role(user, role, resource.ontology_object);

has_resource_role(user: User, role: String, resource: Taxonomy) if
    user_object_has_resource_role(user, role, resource)
    or has_resource_role(user, role, resource.namespace)
    or has_resource_role(user, "ont-taxonomy_" + role, resource.namespace);

has_resource_role(user: User, role: String, resource: TaxonomyItem) if
    has_resource_role(user, role, resource.taxonomy);

has_resource_role(user: User, role: String, resource: TaxonomyItemVersion) if
    has_resource_role(user, role, resource.taxonomy_item);

has_resource_role(user: User, role: String, resource: TaxonomyItemRelation) if
    has_resource_role(user, role, resource.taxonomy_item_source);

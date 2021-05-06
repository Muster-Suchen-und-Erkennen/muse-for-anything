# general identity rules
has_role(user: User, role: String) if
    user.has_role(role);

# admin rules
is_admin(user: User) if
    has_role(user, "admin");

is_namespace_admin(user: User) if
    has_role(user, "namespace_admin");

is_type_admin(user: User) if
    has_role(user, "type_admin");

is_taxonomy_admin(user: User) if
    has_role(user, "taxonomy_admin");

is_object_admin(user: User) if
    has_role(user, "object_admin");

# editor rules
is_editor(user: User) if
    has_role(user, "editor");

is_namespace_editor(user: User) if
    has_role(user, "namespace_editor");

is_type_editor(user: User) if
    has_role(user, "type_editor");

is_taxonomy_editor(user: User) if
    has_role(user, "taxonomy_editor");

is_object_editor(user: User) if
    has_role(user, "object_editor");


# resource specific identity rules
is_owner(user: User, resource) if
    has_resource_role(user, "owner", resource);

is_editor(user: User, resource) if
    has_resource_role(user, "editor", resource);


has_resource_role(user: User, role: String, resource: Namespace) if
    user.has_resource_role(user, role, resource);

has_resource_role(user: User, role: String, resource: OntologyObjectType) if
    user.has_resource_role(user, role, resource)
    or user.has_resource_role(user, role, resource.namespace);

has_resource_role(user: User, role: String, resource: OntologyObjectTypeVersion) if
    user.has_resource_role(user, role, resource.ontology_type);

has_resource_role(user: User, role: String, resource: OntologyObject) if
    user.has_resource_role(user, role, resource)
    or user.has_resource_role(user, role, resource.namespace);

has_resource_role(user: User, role: String, resource: OntologyObjectVersion) if
    user.has_resource_role(user, role, resource.ontology_object);

has_resource_role(user: User, role: String, resource: Taxonomy) if
    user.has_resource_role(user, role, resource)
    or user.has_resource_role(user, role, resource.namespace);

has_resource_role(user: User, role: String, resource: TaxonomyItem) if
    user.has_resource_role(user, role, resource.taxonomy);

has_resource_role(user: User, role: String, resource: TaxonomyItemVersion) if
    user.has_resource_role(user, role, resource.taxonomy_item);

has_resource_role(user: User, role: String, resource: TaxonomyItemRelation) if
    user.has_resource_role(user, role, resource.taxonomy_item_source);

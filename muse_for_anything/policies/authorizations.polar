allow(_guest: Guest, "GET", _resource: OsoResource{resource_type: "ont-namespace", is_collection: true, arguments: nil});
allow(_guest: Guest, "GET", _resource: OsoResource{resource_type: "ont-namespace", is_collection: false, arguments: nil});
allow(_guest: Guest, "GET", _resource: Namespace);
allow(_user: User, "GET", _resource);

# namespace
allow(user: User, "CREATE", resource: OsoResource{resource_type: "ont-namespace", is_collection: false, arguments: nil})
    if can_create(user) or can_create(user, resource);

allow(user: User, "EDIT", resource: Namespace)
    if can_edit(user) or can_edit(user, "ont-namespace") or can_edit(user, resource);

allow(user: User, "RESTORE", resource: Namespace)
    if can_restore(user) or can_restore(user, "ont-namespace") or can_restore(user, resource);

allow(user: User, "DELETE", resource: Namespace)
    if can_delete(user) or can_delete(user, "ont-namespace") or can_delete(user, resource);



# type
allow(user: User, "CREATE", resource: OsoResource{resource_type: "ont-type", is_collection: false, arguments: nil})
    if is_namespace(resource.parent_resource) and (
        can_create(user) or can_create(user, resource)
    );


allow(user: User, "EDIT", resource: OntologyObjectType)
    if can_edit(user) or can_edit(user, "ont-type") or can_edit(user, resource);

allow(user: User, "RESTORE", resource: OntologyObjectType)
    if can_restore(user) or can_restore(user, "ont-type") or can_restore(user, resource);

allow(user: User, "DELETE", resource: OntologyObjectType)
    if can_delete(user) or can_delete(user, "ont-type") or can_delete(user, resource);



# object
allow(user: User, "CREATE", resource: OsoResource{resource_type: "ont-object", is_collection: false, arguments: {type: object_type}})
    if is_namespace(resource.parent_resource) and (
        can_create(user) or can_create(user, resource) or can_create(user, resource.resource_type, resource.parent_resource, object_type)
    );


allow(user: User, "EDIT", resource: OntologyObject)
    if can_edit(user) or can_edit(user, "ont-object") or can_edit(user, resource);

allow(user: User, "RESTORE", resource: OntologyObject)
    if can_restore(user) or can_restore(user, "ont-object") or can_restore(user, resource);

allow(user: User, "DELETE", resource: OntologyObject)
    if can_delete(user) or can_delete(user, "ont-object") or can_delete(user, resource);



# taxonomy
allow(user: User, "CREATE", resource: OsoResource{resource_type: "ont-taxonomy", is_collection: false, arguments: nil})
    if is_namespace(resource.parent_resource) and (
        can_create(user) or can_create(user, resource)
    );


allow(user: User, "EDIT", resource: Taxonomy)
    if can_edit(user) or can_edit(user, "ont-namespace") or can_edit(user, resource);

allow(user: User, "RESTORE", resource: Taxonomy)
    if can_restore(user) or can_restore(user, "ont-namespace") or can_restore(user, resource);

allow(user: User, "DELETE", resource: Taxonomy)
    if can_delete(user) or can_delete(user, "ont-namespace") or can_delete(user, resource);

# taxonomy items
allow(user: User, "CREATE", resource: OsoResource{resource_type: "ont-taxonomy-item", is_collection: false, arguments: nil})
    if is_taxonomy(resource.parent_resource) and (
        can_create(user) or can_create(user, resource)
    );

allow(user: User, "EDIT", resource: TaxonomyItem)
    if can_edit(user) or can_edit(user, "ont-taxonomy") or can_edit(user, resource);

allow(user: User, "RESTORE", resource: TaxonomyItem)
    if can_restore(user) or can_restore(user, "ont-taxonomy") or can_restore(user, resource);

allow(user: User, "DELETE", resource: TaxonomyItem)
    if can_delete(user) or can_delete(user, "ont-taxonomy") or can_delete(user, resource);

# taxonomy item relations
allow(user: User, "CREATE", resource: OsoResource{resource_type: "ont-taxonomy-item-relation", is_collection: false, arguments: nil})
    if is_taxonomy(resource.parent_resource.taxonomy) and (
        can_create(user) or can_create(user, resource)
    );

allow(user: User, "RESTORE", resource: TaxonomyItemRelation)
    if can_restore(user) or can_restore(user, "ont-taxonomy") or can_restore(user, resource);

allow(user: User, "DELETE", resource: TaxonomyItemRelation)
    if can_delete(user) or can_delete(user, "ont-taxonomy") or can_delete(user, resource);


# create rules #################################################################
can_create(user: User)
    if is_creator(user) or is_admin(user);

# namespace specific
can_create(user: User, _resource: "ont-namespace")
    if is_namespace_admin(user) or is_namespace_creator(user);

can_create(user: User, resource: OsoResource{resource_type: "ont-namespace", is_collection: false})
    if can_create(user, resource.resource_type);


# generic
can_create(user: User, resource_type: String, parent_resource: Namespace)
    if is_admin(user, resource_type, parent_resource) or is_creator(user, resource_type, parent_resource);



# type specific
can_create(user: User, _resource: "ont-type")
    if is_namespace_admin(user) or is_type_creator(user);

can_create(user: User, resource: OsoResource{resource_type: "ont-type", is_collection: false})
    if is_namespace(resource.parent_resource) and (
        can_create(user, resource.resource_type) or can_create(user, resource.resource_type, resource.parent_resource)
    );



# object specific
can_create(user: User, _resource: "ont-object")
    if is_namespace_admin(user) or is_object_creator(user);

can_create(user: User, resource: OsoResource{resource_type: "ont-object", is_collection: false})
    if is_namespace(resource.parent_resource) and (
        can_create(user, resource.resource_type) or can_create(user, resource.resource_type, resource.parent_resource)
    );

can_create(user: User, resource_type: String, parent_resource: Namespace, object_type: OntologyObjectType)
    if is_creator(user, resource_type, parent_resource) or is_owner(user, object_type) or is_creator(user, resource_type, object_type);



# taxonomy specific
can_create(user: User, _resource: "ont-taxonomy")
    if is_namespace_admin(user) or is_taxonomy_creator(user);

can_create(user: User, resource: OsoResource{resource_type: "ont-taxonomy", is_collection: false})
    if is_namespace(resource.parent_resource) and (
        can_create(user, resource.resource_type) or can_create(user, resource.resource_type, resource.parent_resource)
    );

# taxonomy item specific
can_create(user: User, _resource: "ont-taxonomy-item")
    if can_create(user, "ont-taxonomy");

can_create(user: User, resource_type: String, parent_resource: Taxonomy)
    if is_admin(user, resource_type, parent_resource) or is_creator(user, resource_type, parent_resource);

can_create(user: User, resource: OsoResource{resource_type: "ont-taxonomy-item", is_collection: false})
    if is_taxonomy(resource.parent_resource) and (
        can_create(user, resource.resource_type) or can_create(user, resource.resource_type, resource.parent_resource)
    );

# taxonomy item relation specific
can_create(user: User, _resource: "ont-taxonomy-item-relation")
    if can_create(user, "ont-taxonomy");

can_create(user: User, resource_type: String, parent_resource: TaxonomyItem)
    if is_admin(user, resource_type, parent_resource.taxonomy) or is_creator(user, resource_type, parent_resource.taxonomy);

can_create(user: User, resource: OsoResource{resource_type: "ont-taxonomy-item-relation", is_collection: false})
    if is_taxonomy(resource.parent_resource.taxonomy) and (
        can_create(user, resource.resource_type) or can_create(user, resource.resource_type, resource.parent_resource.taxonomy)
    );


# edit rules
can_edit(user: User)
    if is_editor(user) or is_admin(user);

can_edit(user: User, _resource: "ont-namespace")
    if is_namespace_admin(user) or is_namespace_editor(user);

can_edit(user: User, resource)
    if is_owner(user, resource) or is_editor(user, resource);

# delete rules
can_delete(user: User)
    if is_admin(user);

can_delete(user: User, _resource: "ont-namespace")
    if is_namespace_admin(user) or is_namespace_editor(user);

can_delete(user: User, resource)
    if is_owner(user, resource);

# special cases for taxonomy sub-resources
can_delete(user: User, resource: TaxonomyItem)
    if can_edit(user, resource.taxonomy);

can_delete(user: User, resource: TaxonomyItemRelation)
    if can_delete(user, resource.taxonomy_item_source.taxonomy);

# restore rules
can_restore(user: User)
    if can_delete(user);

can_restore(user: User, resource)
    if can_delete(user, resource);

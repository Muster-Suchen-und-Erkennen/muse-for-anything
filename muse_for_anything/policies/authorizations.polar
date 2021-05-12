allow(_guest: Guest, "GET", _resource: OsoResource{resource_type: "ont-namespace", is_collection: true, arguments: nil});
allow(_guest: Guest, "GET", _resource: OsoResource{resource_type: "ont-namespace", is_collection: false, arguments: nil});
allow(_guest: Guest, "GET", _resource: Namespace);
allow(_user: User, "GET", _resource);

allow(user: User, "CREATE", resource: OsoResource{resource_type: "ont-namespace", is_collection: false, arguments: nil})
    if can_create(user) or can_create(user, resource);

allow(user: User, "EDIT", resource: Namespace)
    if can_edit(user) or can_edit(user, "ont-namespace") or can_edit(user, resource);

allow(user: User, "RESTORE", resource: Namespace)
    if can_restore(user) or can_restore(user, "ont-namespace") or can_restore(user, resource);

allow(user: User, "DELETE", resource: Namespace)
    if can_delete(user) or can_delete(user, "ont-namespace") or can_delete(user, resource);



# craete rules
can_create(user: User)
    if is_creator(user) or is_admin(user);

can_create(user: User, _resource: "ont-namespace")
    if is_namespace_admin(user) or is_namespace_creator(user);

can_create(user: User, resource: OsoResource{resource_type: "ont-namespace", is_collection: false})
    if can_create(user, resource.resource_type);


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

# restore rules
can_restore(user: User)
    if can_delete(user);

can_restore(user: User, resource)
    if can_delete(user, resource);

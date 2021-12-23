
is_protected_resource(_user: User, _resource: OsoResource{resource_type: "user", is_collection: true, arguments: extraArguments})
    if extraArguments.get("VIEW_ALL_USERS");

is_protected_resource(_user: User, _resource: User);

is_protected_resource(_user: User, _resource: OsoResource{resource_type: "user", is_collection: false});

allow(user: User, "GET", _resource: OsoResource{resource_type: "user", is_collection: true, arguments: extraArguments}) 
    if is_admin(user) or (not extraArguments.get("VIEW_ALL_USERS"));

allow(user: User, "GET", resource: OsoResource{resource_type: "user", is_collection: false})
    if user.username == resource.arguments.get("username") or is_admin(user);

allow(user: User, "GET", resource: User)
    if user == resource or is_admin(user);


allow(user: User, "CREATE", _resource: OsoResource{resource_type: "user", is_collection: false, arguments: nil})
    if print(user.has_role("admin"))  and is_admin(user);

allow(user: User, "EDIT", resource: User)
    if is_admin(user) or user == resource;

allow(user: User, "DELETE", resource: Namespace)
    if is_admin(user) or user == resource;

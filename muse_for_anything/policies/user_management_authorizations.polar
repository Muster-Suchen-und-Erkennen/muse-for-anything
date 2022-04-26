
is_protected_resource(_user: User, _resource: OsoResource{resource_type: "user", is_collection: true, arguments: extraArguments})
    if extraArguments.get("VIEW_ALL_USERS");

is_protected_resource(_user: User, _resource: User);

is_protected_resource(_user: User, _resource: OsoResource{resource_type: "user", is_collection: false});

is_protected_resource(_user: User, _resource: OsoResource{resource_type: "user-role"});

is_protected_resource(_user: User, _resource: UserRole);

is_protected_resource(_user: User, _resource: OsoResource{resource_type: "user-grant"});

is_protected_resource(_user: User, _resource: UserGrant);

allow(user: User, "GET", _resource: OsoResource{resource_type: "user", is_collection: true, arguments: extraArguments}) 
    if is_admin(user) or (not extraArguments.get("VIEW_ALL_USERS"));

allow(user: User, "GET", resource: OsoResource{resource_type: "user", is_collection: false})
    if user.username == resource.arguments.get("username") or is_admin(user);

allow(user: User, "GET", resource: User)
    if user == resource or is_admin(user);


allow(user: User, "CREATE", _resource: OsoResource{resource_type: "user", is_collection: false, arguments: nil})
    if print(user.has_role("admin"))  and is_admin(user);

allow(user: User, "EDIT", resource: OsoResource{resource_type: "user", is_collection: false})
    if user.username == resource.arguments.get("username") or is_admin(user);

allow(user: User, "EDIT", resource: User)
    if is_admin(user) or user == resource;

allow(user: User, "DELETE", resource: OsoResource{resource_type: "user", is_collection: false})
    if user.username == resource.arguments.get("username") or is_admin(user);

allow(user: User, "DELETE", resource: User)
    if is_admin(user) or user == resource;


allow(user: User, "GET", _: OsoResource{resource_type: "user-role"})
    if is_admin(user);

allow(user: User, "GET", resource: OsoResource{resource_type: "user-role", parent_resource: User})
    if user == resource.parent_resource;

allow(user: User, "GET", resource: OsoResource{resource_type: "user-role"})
    if resource.arguments != nil and user.username == resource.arguments.get("username");

allow(user: User, "GET", resource: UserRole)
    if user == resource.user or is_admin(user);

allow(user: User, "CREATE", _: OsoResource{resource_type: "user-role"})
    if is_admin(user);

allow(user: User, "DELETE", _: OsoResource{resource_type: "user-role"})
    if is_admin(user);

allow(user: User, "DELETE", _: UserRole)
    if is_admin(user);

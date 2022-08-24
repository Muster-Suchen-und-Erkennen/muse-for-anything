class OsoProductionConfig:
    OSO_POLICY_FILES = [
        "muse_for_anything/policies/identity_rules.polar",
        "muse_for_anything/policies/authorizations.polar",
        "muse_for_anything/policies/user_management_authorizations.polar",
    ]


class OsoDebugConfig(OsoProductionConfig):
    pass
    # OSO_POLICY_FILES = [
    #     "muse_for_anything/policies/identity_rules.polar",
    #     "muse_for_anything/policies/authorizations.polar",
    #     "muse_for_anything/policies/user_management_authorizations.polar",
    # ]

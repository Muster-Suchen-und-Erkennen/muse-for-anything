class PasswordsProductionConfig:
    PASSWORD_HASH_ALGORITHM = "bcrypt"  # "pbkdf2"
    # PBKDF2_ROUNDS = 1_000_000
    # PBKDF2_HASH_FUNCTION = "sha256"
    # PBKDF2_SALT_LENGTH = 8

    BCRYPT_HANDLE_LONG_PASSWORDS = True
    BCRYPT_LOG_ROUNDS = 13
    # BCRYPT_HASH_PREFIX = "2b"
    # BCRYPT_LONG_PASSWORDS_HASH = "sha256"


class PasswordsDebugConfig(PasswordsProductionConfig):
    """Config values overrides for debug mode."""

    # uncomment to force password settings check (slows down startup significantly)
    # CHECK_PASSWORD_HASH_SETTINGS = True

class SQLAchemyProductionConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class SQLAchemyDebugConfig(SQLAchemyProductionConfig):
    SQLALCHEMY_ECHO = False  # True

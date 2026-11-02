import os


class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_ACCESS_TOKEN_EXPIRES_SECONDS = 3600
    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    def __init__(self):
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
        self.JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", self.SECRET_KEY)
        self.ENABLE_SCHEDULER = os.environ.get("ENABLE_SCHEDULER", "false").lower() == "true"
        self.SCHEDULER_INTERVAL_SECONDS = int(os.environ.get("SCHEDULER_INTERVAL_SECONDS", "60"))
        self.MAIL_ENABLED = os.environ.get("MAIL_ENABLED", "false").lower() == "true"
        self.SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///itsm_dev.db")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    JWT_ACCESS_TOKEN_EXPIRES_SECONDS = 300
    ENABLE_SCHEDULER = False
    SECRET_KEY = "test-secret-key-32-bytes-minimum"
    JWT_SECRET_KEY = "test-jwt-secret-32-bytes-minimum"

    def __init__(self):
        super().__init__()
        self.SECRET_KEY = "test-secret-key-32-bytes-minimum"
        self.JWT_SECRET_KEY = "test-jwt-secret-32-bytes-minimum"
        self.ENABLE_SCHEDULER = False
        self.SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite://")
        self.WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True

    def __init__(self):
        super().__init__()
        secret = os.environ.get("SECRET_KEY")
        jwt_secret = os.environ.get("JWT_SECRET_KEY")
        database_url = os.environ.get("DATABASE_URL")
        if not secret or secret in {"change-me-to-a-long-random-string", "dev-only-change-me"}:
            raise RuntimeError("SECRET_KEY must be set to a strong value in production")
        if not jwt_secret or jwt_secret.startswith("change-me"):
            raise RuntimeError("JWT_SECRET_KEY must be set to a strong value in production")
        if not database_url:
            raise RuntimeError("DATABASE_URL is required in production")
        self.SECRET_KEY = secret
        self.JWT_SECRET_KEY = jwt_secret
        self.SQLALCHEMY_DATABASE_URI = database_url


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    env_name = (name or os.environ.get("FLASK_CONFIG") or "development").lower()
    config_cls = CONFIGS.get(env_name)
    if config_cls is None:
        raise ValueError(f"Unknown FLASK_CONFIG: {env_name}")
    return config_cls()

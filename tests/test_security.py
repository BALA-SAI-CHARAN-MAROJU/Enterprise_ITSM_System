from app.config import ProductionConfig, get_config


def test_production_config_requires_secrets(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "dev-only-change-me")
    monkeypatch.setenv("JWT_SECRET_KEY", "change-me")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    try:
        ProductionConfig()
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


def test_production_config_accepts_real_values(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "a-sufficiently-long-production-secret")
    monkeypatch.setenv("JWT_SECRET_KEY", "another-sufficiently-long-jwt-secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://itsm:itsm@localhost:5432/itsm")
    config = ProductionConfig()
    assert "postgresql" in config.SQLALCHEMY_DATABASE_URI


def test_unknown_config_rejected():
    try:
        get_config("not-a-real-env")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_protected_page_redirects_anonymous(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code in (302, 401)

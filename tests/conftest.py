import pytest

from app import create_app
from app.constants import Role
from app.extensions import db
from app.models import User
from app.services.defaults import seed_default_sla_rules


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "itsm_test.db"
    monkeypatch.setenv("TEST_DATABASE_URL", f"sqlite:///{db_path}")
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        seed_default_sla_rules()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def employee(app):
    with app.app_context():
        user = User(
            email="employee@example.com",
            first_name="Eva",
            last_name="Employee",
            role=Role.EMPLOYEE,
            is_active=True,
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture()
def admin(app):
    with app.app_context():
        user = User(
            email="admin@example.com",
            first_name="Ada",
            last_name="Admin",
            role=Role.ADMIN,
            is_active=True,
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user.id

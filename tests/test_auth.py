from app.constants import Role
from app.extensions import db
from app.models import SlaRule, User


def test_register_creates_employee_and_hashes_password(client, app):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "new.user@example.com",
            "password": "secret123",
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["user"]["role"] == Role.EMPLOYEE
    assert body["user"]["email"] == "new.user@example.com"
    assert "access_token" in body
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]

    with app.app_context():
        user = db.session.query(User).filter_by(email="new.user@example.com").one()
        assert user.password_hash != "secret123"
        assert user.check_password("secret123")


def test_register_rejects_duplicate_email(client):
    payload = {
        "email": "dup@example.com",
        "password": "secret123",
        "first_name": "A",
        "last_name": "B",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "conflict"


def test_register_rejects_short_password(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "short@example.com",
            "password": "123",
            "first_name": "A",
            "last_name": "B",
        },
    )
    assert response.status_code == 422


def test_register_ignores_attempted_admin_role(client, app):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "sneaky@example.com",
            "password": "secret123",
            "first_name": "Sneaky",
            "last_name": "User",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.get_json()["user"]["role"] == Role.EMPLOYEE
    with app.app_context():
        user = db.session.query(User).filter_by(email="sneaky@example.com").one()
        assert user.role == Role.EMPLOYEE


def test_login_success_and_me(client):
    client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "password": "secret123",
            "first_name": "Log",
            "last_name": "In",
        },
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "secret123"},
    )
    assert response.status_code == 200
    token = response.get_json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.get_json()["user"]["email"] == "login@example.com"


def test_login_rejects_bad_password(client, employee):
    response = client.post(
        "/api/auth/login",
        json={"email": "employee@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert "password" not in response.get_data(as_text=True).lower() or "invalid" in response.get_json()["error"]["message"].lower()


def test_me_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_update_profile(client):
    register = client.post(
        "/api/auth/register",
        json={
            "email": "profile@example.com",
            "password": "secret123",
            "first_name": "Old",
            "last_name": "Name",
        },
    )
    token = register.get_json()["access_token"]
    response = client.put(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"first_name": "New", "last_name": "Name"},
    )
    assert response.status_code == 200
    assert response.get_json()["user"]["first_name"] == "New"


def test_web_login_and_dashboard(client, employee):
    response = client.post(
        "/login",
        data={"email": "employee@example.com", "password": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Eva Employee" in response.data


def test_default_sla_rules_seeded(app):
    with app.app_context():
        rules = {row.priority: float(row.resolution_hours) for row in db.session.query(SlaRule).all()}
        assert rules == {"Critical": 2.0, "High": 6.0, "Medium": 24.0, "Low": 48.0}

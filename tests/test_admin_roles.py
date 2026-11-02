"""Tests for Admin Management of Corporate Employee Roles and Department Assignments."""

import pytest
from app.constants import Role, TicketCategory
from app.extensions import db
from app.models import Department, Technician, User
from app.services.defaults import seed_organization_data
from app.services.user_service import update_employee_role_and_assignment


def _token(client, email="admin@example.com", password="password123"):
    login_resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200
    return login_resp.get_json()["access_token"]


def test_admin_lists_all_users_api(client, app, admin, employee):
    token = _token(client, "admin@example.com")
    resp = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "users" in data
    assert data["count"] >= 2
    emails = [u["email"] for u in data["users"]]
    assert "admin@example.com" in emails
    assert "employee@example.com" in emails


def test_non_admin_cannot_list_or_modify_users(client, app, admin, employee):
    emp_token = _token(client, "employee@example.com")
    # List users forbidden
    resp = client.get("/api/users", headers={"Authorization": f"Bearer {emp_token}"})
    assert resp.status_code == 403

    # Modify user forbidden
    resp_put = client.put(
        f"/api/users/{employee}",
        headers={"Authorization": f"Bearer {emp_token}"},
        json={"role": Role.ADMIN},
    )
    assert resp_put.status_code == 403


def test_admin_updates_employee_role_and_department(client, app, admin, employee):
    admin_token = _token(client, "admin@example.com")

    with app.app_context():
        dept = Department(name="Finance", description="Accounting operations")
        db.session.add(dept)
        db.session.commit()
        dept_id = dept.id

    # Update employee to Senior Financial Analyst in Finance department with VIP status
    payload = {
        "role": Role.EMPLOYEE,
        "department_id": dept_id,
        "job_title": "Senior Financial Analyst",
        "is_vip": True,
        "is_active": True,
    }
    resp = client.put(
        f"/api/users/{employee}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload,
    )
    assert resp.status_code == 200
    user_data = resp.get_json()["user"]
    assert user_data["job_title"] == "Senior Financial Analyst"
    assert user_data["is_vip"] is True
    assert user_data["department_name"] == "Finance"


def test_admin_promotes_employee_to_technician_with_skills(client, app, admin, employee):
    admin_token = _token(client, "admin@example.com")

    # Promote employee to Tier 3 Security Specialist
    payload = {
        "role": Role.TECHNICIAN,
        "job_title": "Principal Security Operations Engineer",
        "tier": 3,
        "specialization": "Enterprise Cyber Defense & Threat Intelligence",
        "skills": [TicketCategory.SECURITY, TicketCategory.NETWORK],
        "is_vip": False,
        "is_active": True,
    }
    resp = client.put(
        f"/api/users/{employee}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=payload,
    )
    assert resp.status_code == 200
    user_data = resp.get_json()["user"]
    assert user_data["role"] == Role.TECHNICIAN
    assert "technician" in user_data
    assert user_data["technician"]["tier"] == 3
    assert TicketCategory.SECURITY in user_data["technician"]["skills"]
    assert TicketCategory.NETWORK in user_data["technician"]["skills"]


def test_admin_web_users_directory_and_edit_view(client, app, admin, employee):
    # Log in as admin via web session
    client.post("/login", data={"email": "admin@example.com", "password": "password123"}, follow_redirects=True)

    # Access /admin/users
    resp = client.get("/admin/users")
    assert resp.status_code == 200
    assert b"Corporate Employee Directory" in resp.data
    assert b"admin@example.com" in resp.data
    assert b"employee@example.com" in resp.data

    # Access edit page for employee
    edit_resp = client.get(f"/admin/users/{employee}/edit")
    assert edit_resp.status_code == 200
    assert b"Designate Corporate Role" in edit_resp.data
    assert b"Eva Employee" in edit_resp.data

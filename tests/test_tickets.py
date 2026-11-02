from app.constants import Priority, Role, TicketCategory, TicketStatus
from app.extensions import db
from app.models import Ticket, User


def _jwt_token_for(client, email="user@example.com", password="password123"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.get_json()["access_token"]


def test_create_ticket_api_success(client, app, employee):
    token = _jwt_token_for(client, "employee@example.com", "password123")
    payload = {
        "title": "Database connection timeout in ERP module",
        "description": "Database query times out after 30 seconds when fetching monthly payroll records.",
        "category": TicketCategory.DATABASE,
        "business_impact": "high",
        "urgency": "high",
        "affected_users_count": 25,
    }
    response = client.post(
        "/api/tickets",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.get_json()["ticket"]
    assert data["ticket_number"].startswith("INC-")
    assert data["status"] == TicketStatus.OPEN
    assert data["category"] == TicketCategory.DATABASE
    assert data["recommended_priority"] in (Priority.HIGH, Priority.CRITICAL)
    assert data["final_priority"] == data["recommended_priority"]
    assert data["sla_deadline"] is not None
    assert len(data["history"]) >= 2


def test_create_ticket_validation_failures(client, employee):
    token = _jwt_token_for(client, "employee@example.com", "password123")

    # Missing title
    res = client.post(
        "/api/tickets",
        json={"title": "", "description": "some text", "category": TicketCategory.SOFTWARE},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422

    # Invalid category
    res = client.post(
        "/api/tickets",
        json={"title": "Valid title", "description": "some text", "category": "NonExistent"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


def test_ticket_role_isolation_and_listing(client, app, employee, admin):
    # Register a second employee
    client.post(
        "/api/auth/register",
        json={"email": "emp2@example.com", "password": "password123", "first_name": "Bob", "last_name": "Two"},
    )
    token_emp1 = _jwt_token_for(client, "employee@example.com", "password123")
    token_emp2 = _jwt_token_for(client, "emp2@example.com", "password123")
    token_admin = _jwt_token_for(client, "admin@example.com", "password123")

    # Emp1 creates ticket
    res1 = client.post(
        "/api/tickets",
        json={"title": "Ticket from Emp1", "description": "Need assistance", "category": TicketCategory.HARDWARE},
        headers={"Authorization": f"Bearer {token_emp1}"},
    )
    ticket1_id = res1.get_json()["ticket"]["id"]

    # Emp2 creates ticket
    res2 = client.post(
        "/api/tickets",
        json={"title": "Ticket from Emp2", "description": "Keyboard issue", "category": TicketCategory.HARDWARE},
        headers={"Authorization": f"Bearer {token_emp2}"},
    )
    ticket2_id = res2.get_json()["ticket"]["id"]

    # Emp1 lists tickets -> sees only ticket1
    list1 = client.get("/api/tickets", headers={"Authorization": f"Bearer {token_emp1}"})
    ids1 = [t["id"] for t in list1.get_json()["tickets"]]
    assert ticket1_id in ids1
    assert ticket2_id not in ids1

    # Emp2 cannot access Emp1's ticket directly
    forbidden_res = client.get(f"/api/tickets/{ticket1_id}", headers={"Authorization": f"Bearer {token_emp2}"})
    assert forbidden_res.status_code == 403

    # Admin lists tickets -> sees both
    admin_list = client.get("/api/tickets", headers={"Authorization": f"Bearer {token_admin}"})
    admin_ids = [t["id"] for t in admin_list.get_json()["tickets"]]
    assert ticket1_id in admin_ids
    assert ticket2_id in admin_ids


def test_add_ticket_comment(client, employee):
    token = _jwt_token_for(client, "employee@example.com", "password123")
    t_res = client.post(
        "/api/tickets",
        json={"title": "Comment test ticket", "description": "Description", "category": TicketCategory.NETWORK},
        headers={"Authorization": f"Bearer {token}"},
    )
    ticket_id = t_res.get_json()["ticket"]["id"]

    # Add comment
    c_res = client.post(
        f"/api/tickets/{ticket_id}/comments",
        json={"body": "Issue still persists after router restart."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert c_res.status_code == 201
    assert c_res.get_json()["comment"]["body"] == "Issue still persists after router restart."

    # Verify detail includes comment
    detail_res = client.get(f"/api/tickets/{ticket_id}", headers={"Authorization": f"Bearer {token}"})
    assert len(detail_res.get_json()["ticket"]["comments"]) == 1


def test_ticket_status_transitions_and_reopen(client, employee, admin):
    token_emp = _jwt_token_for(client, "employee@example.com", "password123")
    token_admin = _jwt_token_for(client, "admin@example.com", "password123")

    t_res = client.post(
        "/api/tickets",
        json={"title": "Lifecycle ticket", "description": "Testing status flow", "category": TicketCategory.SOFTWARE},
        headers={"Authorization": f"Bearer {token_emp}"},
    )
    ticket_id = t_res.get_json()["ticket"]["id"]

    # Admin moves to In Progress
    res_in_prog = client.put(
        f"/api/tickets/{ticket_id}/status",
        json={"status": TicketStatus.IN_PROGRESS, "note": "Technician reviewing code"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert res_in_prog.status_code == 200
    assert res_in_prog.get_json()["ticket"]["status"] == TicketStatus.IN_PROGRESS

    # Admin resolves ticket
    res_resolved = client.put(
        f"/api/tickets/{ticket_id}/status",
        json={"status": TicketStatus.RESOLVED, "note": "Bug patch deployed"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert res_resolved.status_code == 200
    assert res_resolved.get_json()["ticket"]["status"] == TicketStatus.RESOLVED
    assert res_resolved.get_json()["ticket"]["resolved_at"] is not None

    # Employee reopens resolved ticket
    res_reopen = client.put(
        f"/api/tickets/{ticket_id}/status",
        json={"status": TicketStatus.OPEN, "note": "Issue reoccurred after restart"},
        headers={"Authorization": f"Bearer {token_emp}"},
    )
    assert res_reopen.status_code == 200
    assert res_reopen.get_json()["ticket"]["status"] == TicketStatus.OPEN
    assert res_reopen.get_json()["ticket"]["resolved_at"] is None


def test_admin_priority_override(client, employee, admin):
    token_emp = _jwt_token_for(client, "employee@example.com", "password123")
    token_admin = _jwt_token_for(client, "admin@example.com", "password123")

    t_res = client.post(
        "/api/tickets",
        json={"title": "Override test", "description": "Priority override test", "category": TicketCategory.OTHER},
        headers={"Authorization": f"Bearer {token_emp}"},
    )
    ticket_id = t_res.get_json()["ticket"]["id"]

    # Employee cannot override priority
    emp_override = client.put(
        f"/api/tickets/{ticket_id}/priority",
        json={"priority": Priority.CRITICAL, "reason": "I think it is critical"},
        headers={"Authorization": f"Bearer {token_emp}"},
    )
    assert emp_override.status_code == 403

    # Admin overrides priority
    admin_override = client.put(
        f"/api/tickets/{ticket_id}/priority",
        json={"priority": Priority.CRITICAL, "reason": "Impacts enterprise executive board"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert admin_override.status_code == 200
    assert admin_override.get_json()["ticket"]["final_priority"] == Priority.CRITICAL


def test_web_ticket_flow(client, employee):
    # Log in through web session
    client.post(
        "/login",
        data={"email": "employee@example.com", "password": "password123"},
        follow_redirects=True,
    )

    # Access new ticket page
    res_get = client.get("/tickets/new")
    assert res_get.status_code == 200

    # Submit new ticket
    res_post = client.post(
        "/tickets/new",
        data={
            "title": "Printer on 2nd floor jammed",
            "description": "Paper tray 2 is stuck and making grinding noise",
            "category": TicketCategory.HARDWARE,
            "business_impact": "low",
            "urgency": "medium",
            "affected_users_count": 4,
        },
        follow_redirects=True,
    )
    assert res_post.status_code == 200
    assert b"Printer on 2nd floor jammed" in res_post.data
    assert b"Activity & Comments" in res_post.data
    assert b"INC-" in res_post.data

from app.constants import Availability, Role, TicketCategory, TicketStatus
from app.extensions import db
from app.models import Technician, TechnicianSkill, Ticket, User
from app.services.assignment_engine import assign_technician, recommend_technician_for_ticket
from app.services.ticket_service import create_ticket


def _jwt_token_for(client, email="admin@example.com", password="password123"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.get_json()["access_token"]


def _create_technician(app, email, name, skill_categories=None, status=Availability.AVAILABLE):
    with app.app_context():
        user = User(
            email=email,
            first_name=name,
            last_name="Tech",
            role=Role.TECHNICIAN,
            is_active=True,
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        tech = Technician(
            user_id=user.id,
            availability_status=status,
            max_concurrent_tickets=5,
        )
        db.session.add(tech)
        db.session.flush()

        if skill_categories:
            for cat in skill_categories:
                skill = TechnicianSkill(technician_id=tech.id, category=cat)
                db.session.add(skill)

        db.session.commit()
        return tech.id


def test_recommendation_prefers_matching_skill(client, app, employee):
    tech_db_id = _create_technician(app, "tech1@example.com", "Alice", [TicketCategory.DATABASE])
    tech_net_id = _create_technician(app, "tech2@example.com", "Bob", [TicketCategory.NETWORK])

    with app.app_context():
        emp = db.session.get(User, employee)
        ticket = create_ticket(
            requester=emp,
            title="Postgres Index issue",
            description="Slow queries on customer table",
            category=TicketCategory.DATABASE,
            business_impact="medium",
            urgency="medium",
        )
        rec = recommend_technician_for_ticket(ticket)
        assert rec.recommended_technician_id == tech_db_id
        assert "Alice Tech" in rec.recommended_technician_name
        assert "matching expertise" in rec.justification


def test_recommendation_prefers_lower_workload(client, app, employee):
    tech1_id = _create_technician(app, "tech_busy@example.com", "Charlie", [TicketCategory.SOFTWARE])
    tech2_id = _create_technician(app, "tech_free@example.com", "Dave", [TicketCategory.SOFTWARE])

    with app.app_context():
        emp = db.session.get(User, employee)
        # Assign 2 active tickets to Charlie
        for i in range(2):
            t = create_ticket(
                requester=emp,
                title=f"Bug #{i}",
                description="Software defect",
                category=TicketCategory.SOFTWARE,
                business_impact="low",
                urgency="low",
            )
            t.assigned_technician_id = tech1_id
            t.status = TicketStatus.IN_PROGRESS
            db.session.add(t)
        db.session.commit()

        # Create new ticket needing assignment
        new_ticket = create_ticket(
            requester=emp,
            title="New software crash",
            description="App crashed on startup",
            category=TicketCategory.SOFTWARE,
            business_impact="medium",
            urgency="high",
        )
        rec = recommend_technician_for_ticket(new_ticket)
        assert rec.recommended_technician_id == tech2_id
        assert "Dave Tech" in rec.recommended_technician_name


def test_recommendation_excludes_unavailable_technician(client, app, employee):
    tech1_id = _create_technician(app, "tech_unavail@example.com", "Eve", [TicketCategory.SECURITY], status=Availability.UNAVAILABLE)
    tech2_id = _create_technician(app, "tech_avail@example.com", "Frank", [TicketCategory.HARDWARE], status=Availability.AVAILABLE)

    with app.app_context():
        emp = db.session.get(User, employee)
        ticket = create_ticket(
            requester=emp,
            title="Firewall rule change",
            description="Need open port 443",
            category=TicketCategory.SECURITY,
            business_impact="high",
            urgency="high",
        )
        rec = recommend_technician_for_ticket(ticket)
        # Eve is unavailable so Frank is selected or Eve is disqualified
        assert rec.recommended_technician_id == tech2_id


def test_assign_technician_workflow_and_audit(client, app, employee, admin):
    tech_id = _create_technician(app, "tech_assign@example.com", "Grace", [TicketCategory.HARDWARE])

    with app.app_context():
        emp = db.session.get(User, employee)
        adm = db.session.get(User, admin)
        ticket = create_ticket(
            requester=emp,
            title="Laptop screen cracked",
            description="Screen broken",
            category=TicketCategory.HARDWARE,
            business_impact="low",
            urgency="low",
        )
        assert ticket.status == TicketStatus.OPEN

        updated = assign_technician(
            ticket=ticket,
            technician_id=tech_id,
            assigned_by=adm,
            is_override=True,
            override_reason="Grace is on site today",
        )
        assert updated.status == TicketStatus.ASSIGNED
        assert updated.assigned_technician_id == tech_id

        # Check audit trail
        history_actions = [h.action for h in updated.history]
        assert "technician_overridden" in history_actions


def test_technician_api_assignment_rbAC(client, app, employee, admin):
    tech_id = _create_technician(app, "tech_api@example.com", "Heidi", [TicketCategory.NETWORK])
    token_emp = _jwt_token_for(client, "employee@example.com", "password123")
    token_admin = _jwt_token_for(client, "admin@example.com", "password123")

    # Employee creates ticket
    res_ticket = client.post(
        "/api/tickets",
        json={"title": "WiFi disconnected", "description": "Cannot connect", "category": TicketCategory.NETWORK},
        headers={"Authorization": f"Bearer {token_emp}"},
    )
    ticket_id = res_ticket.get_json()["ticket"]["id"]

    # Employee attempts to assign technician -> 403 Forbidden
    res_forbidden = client.post(
        "/api/technicians/assign",
        json={"ticket_id": ticket_id, "technician_id": tech_id},
        headers={"Authorization": f"Bearer {token_emp}"},
    )
    assert res_forbidden.status_code == 403

    # Admin assigns technician -> 200 OK
    res_success = client.post(
        "/api/technicians/assign",
        json={"ticket_id": ticket_id, "technician_id": tech_id, "override_reason": "Primary network lead"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert res_success.status_code == 200
    assert res_success.get_json()["ticket"]["assigned_technician_id"] == tech_id
    assert res_success.get_json()["ticket"]["status"] == TicketStatus.ASSIGNED

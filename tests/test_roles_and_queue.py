"""Tests for Corporate Roles Differentiation, Problem-Based Assignment, and Dynamic Work Queue Re-ordering."""

from datetime import timedelta

import pytest
from app.constants import Availability, Priority, Role, TicketCategory, TicketStatus
from app.extensions import db
from app.models import Department, Technician, TechnicianSkill, Ticket, User
from app.services.assignment_engine import recommend_technician_for_ticket
from app.services.priority_engine import calculate_priority
from app.services.queue_engine import get_technician_prioritized_work_queue
from app.services.ticket_service import create_ticket
from app.utils.datetime import utcnow


@pytest.fixture
def org_setup(app):
    """Set up departments, employees with different corporate roles, and specialized technicians."""
    with app.app_context():
        # 1. Departments
        exec_dept = Department(name="Executive", description="C-Suite leadership")
        fin_dept = Department(name="Finance & Accounting", description="Financial operations")
        eng_dept = Department(name="Software Engineering", description="Core engineering")
        db.session.add_all([exec_dept, fin_dept, eng_dept])
        db.session.flush()

        # 2. Differentiated Corporate Employees
        ceo = User(
            email="ceo_test@example.com",
            first_name="Eleanor",
            last_name="Vance",
            role=Role.EMPLOYEE,
            job_title="Chief Executive Officer",
            is_vip=True,
            department_id=exec_dept.id,
            is_active=True,
        )
        ceo.set_password("pass123")

        cfo = User(
            email="cfo_test@example.com",
            first_name="Marcus",
            last_name="Sterling",
            role=Role.EMPLOYEE,
            job_title="Chief Financial Officer",
            is_vip=True,
            department_id=fin_dept.id,
            is_active=True,
        )
        cfo.set_password("pass123")

        staff = User(
            email="staff_test@example.com",
            first_name="Sam",
            last_name="Green",
            role=Role.EMPLOYEE,
            job_title="Junior Analyst",
            is_vip=False,
            department_id=eng_dept.id,
            is_active=True,
        )
        staff.set_password("pass123")

        db.session.add_all([ceo, cfo, staff])
        db.session.flush()

        # 3. Specialized Problem-Solver Technicians
        # Alice: Security & Database Specialist (Tier 3)
        alice_u = User(email="tech_sec@example.com", first_name="Alice", last_name="Sec", role=Role.TECHNICIAN, is_active=True)
        alice_u.set_password("pass123")
        db.session.add(alice_u)
        db.session.flush()
        alice_tech = Technician(user_id=alice_u.id, availability_status=Availability.AVAILABLE, max_concurrent_tickets=8, tier=3)
        db.session.add(alice_tech)
        db.session.flush()
        db.session.add_all([
            TechnicianSkill(technician_id=alice_tech.id, category=TicketCategory.SECURITY),
            TechnicianSkill(technician_id=alice_tech.id, category=TicketCategory.DATABASE),
        ])

        # Bob: Network & Hardware Specialist (Tier 2)
        bob_u = User(email="tech_net@example.com", first_name="Bob", last_name="Net", role=Role.TECHNICIAN, is_active=True)
        bob_u.set_password("pass123")
        db.session.add(bob_u)
        db.session.flush()
        bob_tech = Technician(user_id=bob_u.id, availability_status=Availability.AVAILABLE, max_concurrent_tickets=10, tier=2)
        db.session.add(bob_tech)
        db.session.flush()
        db.session.add_all([
            TechnicianSkill(technician_id=bob_tech.id, category=TicketCategory.NETWORK),
            TechnicianSkill(technician_id=bob_tech.id, category=TicketCategory.HARDWARE),
        ])

        db.session.commit()

        return {
            "exec_dept_id": exec_dept.id,
            "fin_dept_id": fin_dept.id,
            "ceo_id": ceo.id,
            "cfo_id": cfo.id,
            "staff_id": staff.id,
            "alice_tech_id": alice_tech.id,
            "bob_tech_id": bob_tech.id,
        }


def test_priority_engine_elevates_vip_and_executive_roles():
    """Verify that VIP status and Executive/Finance departments boost ticket priority."""
    # Standard employee ticket
    regular = calculate_priority(
        category=TicketCategory.SOFTWARE,
        business_impact="medium",
        urgency="medium",
        affected_users_count=1,
        requester_department="Operations",
        is_vip=False,
    )

    # Executive VIP ticket with identical impact & urgency
    vip_exec = calculate_priority(
        category=TicketCategory.SOFTWARE,
        business_impact="medium",
        urgency="medium",
        affected_users_count=1,
        requester_department="Executive",
        is_vip=True,
    )

    # VIP (+15) + Executive Department (+15) = +30 points higher
    assert vip_exec.total_score >= regular.total_score + 25
    assert any("VIP" in r for r in vip_exec.reasons)
    assert any("Executive" in r for r in vip_exec.reasons)


def test_problem_based_technician_assignment(app, org_setup):
    """Verify assignment matches specific problem category to the certified technician."""
    with app.app_context():
        ceo = db.session.get(User, org_setup["ceo_id"])

        # Problem 1: Security Breach -> Alice (Security Specialist)
        sec_ticket = create_ticket(
            requester=ceo,
            title="Unauthorized login attempts detected on firewall",
            description="Brute force activity on port 443",
            category=TicketCategory.SECURITY,
            business_impact="high",
            urgency="high",
        )
        rec_sec = recommend_technician_for_ticket(sec_ticket)
        assert rec_sec.recommended_technician_id == org_setup["alice_tech_id"]
        assert "Alice Sec" in rec_sec.recommended_technician_name
        assert "matching expertise" in rec_sec.justification

        # Problem 2: Network Outage -> Bob (Network Specialist)
        net_ticket = create_ticket(
            requester=ceo,
            title="Core switch dropped connection on Floor 3",
            description="Switch offline affecting local workstations",
            category=TicketCategory.NETWORK,
            business_impact="medium",
            urgency="high",
        )
        rec_net = recommend_technician_for_ticket(net_ticket)
        assert rec_net.recommended_technician_id == org_setup["bob_tech_id"]
        assert "Bob Net" in rec_net.recommended_technician_name
        assert "matching expertise" in rec_net.justification


def test_technician_work_queue_dynamic_reordering(app, org_setup):
    """Verify that a technician's personal work queue re-ranks tickets dynamically based on severity, SLA urgency, and employee role."""
    with app.app_context():
        alice_tech_id = org_setup["alice_tech_id"]
        cfo = db.session.get(User, org_setup["cfo_id"])
        staff = db.session.get(User, org_setup["staff_id"])

        # Ticket 1: Low priority general query assigned to Alice
        t1 = create_ticket(
            requester=staff,
            title="Database documentation query",
            description="Looking for database schema dictionary",
            category=TicketCategory.DATABASE,
            business_impact="low",
            urgency="low",
        )
        t1.assigned_technician_id = alice_tech_id
        t1.status = TicketStatus.IN_PROGRESS
        db.session.add(t1)

        # Ticket 2: Medium priority issue from staff
        t2 = create_ticket(
            requester=staff,
            title="Query performance on analytics report",
            description="Takes 30 seconds to generate report",
            category=TicketCategory.DATABASE,
            business_impact="medium",
            urgency="medium",
        )
        t2.assigned_technician_id = alice_tech_id
        t2.status = TicketStatus.ASSIGNED
        db.session.add(t2)
        db.session.commit()

        # Alice checks queue: t2 should be rank #1 (Medium > Low)
        queue_before = get_technician_prioritized_work_queue(alice_tech_id)
        assert len(queue_before) == 2
        assert queue_before[0].ticket_id == t2.id
        assert queue_before[0].queue_rank == 1
        assert queue_before[1].ticket_id == t1.id
        assert queue_before[1].queue_rank == 2

        # NOW: An urgent Critical Incident arrives from the CFO (VIP / Finance Department)!
        t3_urgent = create_ticket(
            requester=cfo,
            title="Payroll Database Outage - Payment Run Blocked",
            description="Direct database deadlock on payroll ledger during monthly run",
            category=TicketCategory.DATABASE,
            business_impact="critical",
            urgency="critical",
            affected_users_count=50,
        )
        t3_urgent.assigned_technician_id = alice_tech_id
        t3_urgent.status = TicketStatus.ASSIGNED
        db.session.add(t3_urgent)
        db.session.commit()

        # Alice's priority order MUST IMMEDIATELY CHANGE:
        # t3_urgent must jump straight to Rank #1, pushing t2 to #2 and t1 to #3!
        queue_after = get_technician_prioritized_work_queue(alice_tech_id)
        assert len(queue_after) == 3
        assert queue_after[0].ticket_id == t3_urgent.id
        assert queue_after[0].queue_rank == 1
        assert queue_after[0].is_vip is True
        assert "Critical priority" in queue_after[0].reasons[0]
        assert any("VIP" in r or "Finance" in r for r in queue_after[0].reasons)

        assert queue_after[1].ticket_id == t2.id
        assert queue_after[1].queue_rank == 2

        assert queue_after[2].ticket_id == t1.id
        assert queue_after[2].queue_rank == 3


def test_technician_queue_api_endpoint(client, app, org_setup):
    """Verify REST API endpoint for retrieving technician prioritized work queue."""
    # Login as admin to get token
    login_resp = client.post("/api/auth/login", json={"email": "tech_sec@example.com", "password": "pass123"})
    token = login_resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    tech_id = org_setup["alice_tech_id"]
    resp = client.get(f"/api/technicians/{tech_id}/queue", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "queue" in data
    assert "queue_count" in data
    assert data["technician_id"] == tech_id

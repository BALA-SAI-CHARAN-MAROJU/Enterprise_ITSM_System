from datetime import timedelta

from app.constants import Priority, Role, TicketCategory, TicketStatus
from app.extensions import db
from app.models import Technician, Ticket, User
from app.services.analytics import get_admin_dashboard_metrics, get_technician_performance_analytics
from app.services.assignment_engine import assign_technician
from app.services.incident_analysis import analyze_recurring_incidents
from app.services.ticket_service import create_ticket, update_ticket_status
from app.utils.datetime import utcnow


def _jwt_token_for(client, email="admin@example.com", password="password123"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.get_json()["access_token"]


def test_admin_dashboard_metrics_aggregation(app, employee, admin):
    with app.app_context():
        emp = db.session.get(User, employee)
        adm = db.session.get(User, admin)

        t1 = create_ticket(
            requester=emp,
            title="Outage in Network switch",
            description="Network switch failure",
            category=TicketCategory.NETWORK,
            business_impact="critical",
            urgency="critical",
        )
        t2 = create_ticket(
            requester=emp,
            title="Software install request",
            description="Install Python IDE",
            category=TicketCategory.SOFTWARE,
            business_impact="low",
            urgency="low",
        )
        update_ticket_status(t2, TicketStatus.RESOLVED, adm)

        metrics = get_admin_dashboard_metrics()
        kpis = metrics["kpis"]
        assert kpis["total_tickets"] >= 2
        assert kpis["open_tickets"] >= 1
        assert kpis["resolved_tickets"] >= 1
        assert "charts" in metrics
        assert len(metrics["charts"]["trends"]["labels"]) == 7


def test_technician_performance_analytics(app, employee, admin):
    with app.app_context():
        emp = db.session.get(User, employee)
        adm = db.session.get(User, admin)

        # Create technician
        tech_user = User(
            email="tech_perf@example.com",
            first_name="Sam",
            last_name="Tech",
            role=Role.TECHNICIAN,
            is_active=True,
        )
        tech_user.set_password("password123")
        db.session.add(tech_user)
        db.session.flush()

        tech = Technician(user_id=tech_user.id, max_concurrent_tickets=8)
        db.session.add(tech)
        db.session.commit()

        # Create and assign ticket
        t = create_ticket(
            requester=emp,
            title="Database performance lag",
            description="Slow index",
            category=TicketCategory.DATABASE,
            business_impact="medium",
            urgency="medium",
        )
        assign_technician(t, tech.id, adm)
        update_ticket_status(t, TicketStatus.RESOLVED, tech_user)

        perf = get_technician_performance_analytics()
        tech_p = next((p for p in perf if p["technician_id"] == tech.id), None)
        assert tech_p is not None
        assert tech_p["name"] == "Sam Tech"
        assert tech_p["total_assigned"] == 1
        assert tech_p["resolved_tickets"] == 1
        assert tech_p["sla_compliance_rate"] == 100.0


def test_incident_analysis_detects_recurring_keywords(app, employee):
    with app.app_context():
        emp = db.session.get(User, employee)

        for i in range(3):
            create_ticket(
                requester=emp,
                title=f"VPN connection dropped #{i}",
                description="Remote VPN client drops every 10 minutes",
                category=TicketCategory.NETWORK,
                business_impact="medium",
                urgency="medium",
            )

        for i in range(2):
            create_ticket(
                requester=emp,
                title=f"Printer offline on 4th floor #{i}",
                description="Network printer not responding to ping",
                category=TicketCategory.HARDWARE,
                business_impact="low",
                urgency="low",
            )

        analysis = analyze_recurring_incidents(min_frequency=2)
        assert analysis["total_analyzed_tickets"] >= 5
        patterns = analysis["recurring_patterns"]
        keywords = [p["keyword"] for p in patterns]
        assert "vpn" in keywords or "printer" in keywords

        vpn_cluster = next((p for p in patterns if p["keyword"] == "vpn"), None)
        if vpn_cluster:
            assert vpn_cluster["frequency"] >= 3
            assert "Repeated issue with keyword 'vpn'" in vpn_cluster["hypothesis"]


def test_analytics_api_rbac(client, employee, admin):
    token_emp = _jwt_token_for(client, "employee@example.com", "password123")
    token_admin = _jwt_token_for(client, "admin@example.com", "password123")

    # Employee denied
    res_emp = client.get("/api/analytics/dashboard", headers={"Authorization": f"Bearer {token_emp}"})
    assert res_emp.status_code == 403

    # Admin allowed
    res_dash = client.get("/api/analytics/dashboard", headers={"Authorization": f"Bearer {token_admin}"})
    assert res_dash.status_code == 200
    assert "kpis" in res_dash.get_json()

    res_inc = client.get("/api/analytics/incidents", headers={"Authorization": f"Bearer {token_admin}"})
    assert res_inc.status_code == 200
    assert "recurring_patterns" in res_inc.get_json()

    res_techs = client.get("/api/analytics/technicians", headers={"Authorization": f"Bearer {token_admin}"})
    assert res_techs.status_code == 200
    assert "technicians" in res_techs.get_json()

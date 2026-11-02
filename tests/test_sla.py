from datetime import timedelta

from app.constants import EscalationLevel, Priority, Role, TicketCategory, TicketStatus
from app.extensions import db
from app.models import Escalation, Notification, Ticket, User
from app.services.notification_service import create_notification, get_user_notifications
from app.services.sla_engine import (
    evaluate_ticket_sla,
    get_sla_rules,
    scan_all_active_tickets_sla,
    update_sla_rule,
)
from app.services.ticket_service import create_ticket
from app.utils.datetime import utcnow


def _jwt_token_for(client, email="admin@example.com", password="password123"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.get_json()["access_token"]


def test_sla_rules_retrieval_and_update(app, admin):
    with app.app_context():
        rules = get_sla_rules()
        assert len(rules) >= 4

        adm = db.session.get(User, admin)
        updated = update_sla_rule(
            priority=Priority.CRITICAL,
            resolution_hours=1.5,
            warning_percent=75,
            admin_user=adm,
        )
        assert float(updated.resolution_hours) == 1.5
        assert updated.warning_percent == 75


def test_sla_warning_and_breach_detection(app, employee):
    with app.app_context():
        emp = db.session.get(User, employee)
        base_time = utcnow()

        # Ticket 1: 85% elapsed (Warning)
        t_warn = create_ticket(
            requester=emp,
            title="Warning SLA Ticket",
            description="Ticket nearing deadline",
            category=TicketCategory.NETWORK,
            business_impact="high",
            urgency="high",
        )
        # Set created_at 85 minutes ago with 100-minute SLA window
        t_warn.created_at = base_time - timedelta(minutes=85)
        t_warn.sla_deadline = base_time + timedelta(minutes=15)
        db.session.commit()

        is_warn, is_breach = evaluate_ticket_sla(t_warn, current_time=base_time)
        assert is_warn is True
        assert is_breach is False

        esc_warn = db.session.scalar(
            db.select(Escalation).where(
                Escalation.ticket_id == t_warn.id,
                Escalation.level == EscalationLevel.WARNING,
            )
        )
        assert esc_warn is not None

        # Ticket 2: Past deadline (Breach)
        t_breach = create_ticket(
            requester=emp,
            title="Breached SLA Ticket",
            description="Ticket past deadline",
            category=TicketCategory.DATABASE,
            business_impact="critical",
            urgency="critical",
        )
        t_breach.created_at = base_time - timedelta(hours=3)
        t_breach.sla_deadline = base_time - timedelta(minutes=30)
        db.session.commit()

        is_warn2, is_breach2 = evaluate_ticket_sla(t_breach, current_time=base_time)
        assert is_breach2 is True
        assert t_breach.sla_breached is True

        esc_breach = db.session.scalar(
            db.select(Escalation).where(
                Escalation.ticket_id == t_breach.id,
                Escalation.level == EscalationLevel.BREACH,
            )
        )
        assert esc_breach is not None


def test_scan_all_active_tickets_sla(app, employee):
    with app.app_context():
        emp = db.session.get(User, employee)
        create_ticket(
            requester=emp,
            title="Active Ticket for Scan",
            description="Scan test",
            category=TicketCategory.SOFTWARE,
            business_impact="low",
            urgency="low",
        )
        stats = scan_all_active_tickets_sla()
        assert stats["scanned"] >= 1
        assert "warnings" in stats
        assert "breaches" in stats


def test_sla_api_rbac_and_scan(client, employee, admin):
    token_emp = _jwt_token_for(client, "employee@example.com", "password123")
    token_admin = _jwt_token_for(client, "admin@example.com", "password123")

    # Public list of SLA rules
    res = client.get("/api/sla/rules", headers={"Authorization": f"Bearer {token_emp}"})
    assert res.status_code == 200
    assert len(res.get_json()["rules"]) >= 4

    # Employee tries to update rule -> 403 Forbidden
    res_emp = client.put(
        f"/api/sla/rules/{Priority.HIGH}",
        json={"resolution_hours": 4},
        headers={"Authorization": f"Bearer {token_emp}"},
    )
    assert res_emp.status_code == 403

    # Admin updates rule -> 200 OK
    res_admin = client.put(
        f"/api/sla/rules/{Priority.HIGH}",
        json={"resolution_hours": 5, "warning_percent": 85},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert res_admin.status_code == 200
    assert res_admin.get_json()["rule"]["resolution_hours"] == 5.0

    # Admin triggers scan -> 200 OK
    res_scan = client.post("/api/sla/scan", headers={"Authorization": f"Bearer {token_admin}"})
    assert res_scan.status_code == 200
    assert "stats" in res_scan.get_json()


def test_notifications_flow(client, app, employee):
    token = _jwt_token_for(client, "employee@example.com", "password123")

    with app.app_context():
        create_notification(
            user_id=employee,
            title="System Alert",
            body="Scheduled maintenance tonight at 10 PM.",
            notification_type="system_alert",
        )

    # Fetch notifications
    res = client.get("/api/notifications", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    notifs = res.get_json()["notifications"]
    assert len(notifs) >= 1
    target_id = notifs[0]["id"]
    assert notifs[0]["is_read"] is False

    # Mark as read
    res_read = client.put(f"/api/notifications/{target_id}/read", headers={"Authorization": f"Bearer {token}"})
    assert res_read.status_code == 200

    # Mark all as read
    res_all = client.put("/api/notifications/read-all", headers={"Authorization": f"Bearer {token}"})
    assert res_all.status_code == 200

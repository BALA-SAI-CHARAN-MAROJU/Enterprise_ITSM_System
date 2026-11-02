"""SLA Monitoring and Escalation Engine.

Tracks ticket resolution deadlines, detects SLA warning thresholds (e.g. 80% elapsed),
identifies overdue breaches, logs escalations, and broadcasts notifications.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select

from app.constants import EscalationLevel, Priority, TicketStatus
from app.extensions import db
from app.models import Escalation, SlaRule, Ticket, TicketHistory, User
from app.services.notification_service import notify_ticket_stakeholders
from app.utils.datetime import ensure_utc, utcnow


def get_sla_rules() -> List[SlaRule]:
    """Retrieve all configured SLA priority rules."""
    return db.session.scalars(select(SlaRule).order_by(SlaRule.resolution_hours.asc())).all()


def update_sla_rule(
    priority: str,
    resolution_hours: float,
    warning_percent: int = 80,
    admin_user: Optional[User] = None,
) -> SlaRule:
    """Update or insert an SLA rule."""
    if priority not in Priority.ALL:
        raise ValueError(f"Invalid priority: {priority}")
    if resolution_hours <= 0:
        raise ValueError("Resolution hours must be greater than zero")
    if not (1 <= warning_percent <= 99):
        raise ValueError("Warning percent must be between 1 and 99")

    rule = db.session.scalar(select(SlaRule).where(SlaRule.priority == priority))
    if not rule:
        rule = SlaRule(
            priority=priority,
            resolution_hours=Decimal(str(resolution_hours)),
            warning_percent=warning_percent,
            clock_start="created",
            updated_by_id=admin_user.id if admin_user else None,
        )
        db.session.add(rule)
    else:
        rule.resolution_hours = Decimal(str(resolution_hours))
        rule.warning_percent = warning_percent
        if admin_user:
            rule.updated_by_id = admin_user.id

    db.session.commit()
    return rule


def evaluate_ticket_sla(ticket: Ticket, current_time: Optional[datetime] = None) -> Tuple[bool, bool]:
    """Evaluate SLA status for a single ticket.

    Returns tuple (is_warning, is_breached).
    """
    now = ensure_utc(current_time or utcnow())

    # Closed or Resolved tickets don't advance SLA clocks
    if ticket.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
        return False, ticket.sla_breached

    if not ticket.sla_deadline or not ticket.created_at:
        return False, False

    deadline = ensure_utc(ticket.sla_deadline)
    created_at = ensure_utc(ticket.created_at)

    total_duration = (deadline - created_at).total_seconds()
    if total_duration <= 0:
        total_duration = 1.0

    elapsed = (now - created_at).total_seconds()
    elapsed_percent = (elapsed / total_duration) * 100.0

    rule = db.session.scalar(select(SlaRule).where(SlaRule.priority == ticket.final_priority))
    warning_threshold = rule.warning_percent if rule else 80

    is_warning = False
    is_breached = False

    # 1. Breach check
    if now > deadline:
        is_breached = True
        if not ticket.sla_breached:
            ticket.sla_breached = True
            # Check if breach escalation already logged
            existing_breach = db.session.scalar(
                select(Escalation).where(
                    Escalation.ticket_id == ticket.id,
                    Escalation.level == EscalationLevel.BREACH,
                )
            )
            if not existing_breach:
                esc = Escalation(
                    ticket_id=ticket.id,
                    level=EscalationLevel.BREACH,
                    reason=f"SLA resolution deadline ({deadline.strftime('%Y-%m-%d %H:%M')}) breached for priority {ticket.final_priority}.",
                    created_at=now,
                )
                hist = TicketHistory(
                    ticket_id=ticket.id,
                    user_id=None,
                    action="sla_breached",
                    field_name="sla_breached",
                    old_value="False",
                    new_value="True",
                    created_at=now,
                )
                db.session.add_all([esc, hist])
                db.session.flush()

                notify_ticket_stakeholders(
                    ticket=ticket,
                    title=f"SLA BREACH: Ticket {ticket.ticket_number}",
                    body=f"Ticket '{ticket.title}' has breached its SLA resolution deadline.",
                    notification_type="sla_breach",
                )

    # 2. Warning check (if not yet breached)
    elif elapsed_percent >= warning_threshold:
        is_warning = True
        existing_warning = db.session.scalar(
            select(Escalation).where(
                Escalation.ticket_id == ticket.id,
                Escalation.level == EscalationLevel.WARNING,
            )
        )
        if not existing_warning:
            esc = Escalation(
                ticket_id=ticket.id,
                level=EscalationLevel.WARNING,
                reason=f"{warning_threshold}% of SLA resolution window has elapsed for ticket {ticket.ticket_number}.",
                created_at=now,
            )
            db.session.add(esc)
            db.session.flush()

            notify_ticket_stakeholders(
                ticket=ticket,
                title=f"SLA Warning: Ticket {ticket.ticket_number}",
                body=f"Ticket '{ticket.title}' is approaching its SLA deadline ({warning_threshold}% time elapsed).",
                notification_type="sla_warning",
            )

    return is_warning, is_breached


def scan_all_active_tickets_sla(current_time: Optional[datetime] = None) -> Dict[str, int]:
    """Scan all active tickets, detect warnings/breaches, and record escalations."""
    now = ensure_utc(current_time or utcnow())
    active_statuses = (
        TicketStatus.OPEN,
        TicketStatus.ASSIGNED,
        TicketStatus.IN_PROGRESS,
        TicketStatus.PENDING,
        TicketStatus.ON_HOLD,
    )
    stmt = select(Ticket).where(Ticket.status.in_(active_statuses))
    active_tickets = db.session.scalars(stmt).all()

    scanned_count = len(active_tickets)
    warnings_count = 0
    breaches_count = 0

    for ticket in active_tickets:
        is_warn, is_breach = evaluate_ticket_sla(ticket, current_time=now)
        if is_warn:
            warnings_count += 1
        if is_breach:
            breaches_count += 1

    db.session.commit()
    return {
        "scanned": scanned_count,
        "warnings": warnings_count,
        "breaches": breaches_count,
    }

"""Ticket management service.

Handles ticket creation, sequential ticket numbering, rule-based priority
assignment, status transitions with validation, comments, and audit history.
"""

from datetime import timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select

from app.constants import DEFAULT_SLA_HOURS, ImpactLevel, Priority, Role, TicketCategory, TicketStatus, UrgencyLevel
from app.extensions import db
from app.models import Department, SlaRule, Technician, Ticket, TicketComment, TicketHistory, User
from app.services.notification_service import notify_admins, notify_ticket_stakeholders
from app.services.priority_engine import calculate_priority
from app.utils.datetime import utcnow


class TicketError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "bad_request"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def _generate_ticket_number() -> str:
    """Generate human-readable ticket number like INC-2026-00001."""
    year = utcnow().year
    prefix = f"INC-{year}-"
    # Find maximum existing sequence number for the current year
    # Equivalent SQL: SELECT ticket_number FROM tickets WHERE ticket_number LIKE 'INC-2026-%' ORDER BY id DESC LIMIT 1;
    stmt = (
        select(Ticket.ticket_number)
        .where(Ticket.ticket_number.like(f"{prefix}%"))
        .order_by(Ticket.id.desc())
        .limit(1)
    )
    last_ticket_number = db.session.scalar(stmt)
    if last_ticket_number:
        try:
            last_seq = int(last_ticket_number.split("-")[-1])
            seq = last_seq + 1
        except ValueError:
            seq = db.session.scalar(select(func.count(Ticket.id))) + 1
    else:
        seq = 1
    return f"{prefix}{seq:05d}"


def calculate_sla_deadline(priority: str, start_time=None):
    """Compute SLA deadline based on priority rule in database or default hours."""
    start = start_time or utcnow()
    rule = db.session.scalar(select(SlaRule).where(SlaRule.priority == priority))
    hours = rule.resolution_hours if rule else DEFAULT_SLA_HOURS.get(priority, 24)
    if isinstance(hours, Decimal):
        hours = float(hours)
    return start + timedelta(hours=hours)


def create_ticket(
    requester: User,
    title: str,
    description: str,
    category: str,
    business_impact: str,
    urgency: str,
    affected_users_count: int = 1,
    department_id: Optional[int] = None,
    manual_priority: Optional[str] = None,
) -> Ticket:
    """Create a new support ticket, evaluate priority, and record history."""
    if not title or not title.strip():
        raise TicketError("Ticket title is required", 422, "validation_error")
    if len(title.strip()) > 200:
        raise TicketError("Ticket title cannot exceed 200 characters", 422, "validation_error")
    if not description or not description.strip():
        raise TicketError("Ticket description is required", 422, "validation_error")

    category = category.strip() if category else TicketCategory.OTHER
    if category not in TicketCategory.ALL:
        raise TicketError(f"Invalid category: {category}", 422, "validation_error")

    impact = (business_impact or "low").strip().lower()
    if impact not in ImpactLevel.ALL:
        raise TicketError(f"Invalid business impact: {business_impact}", 422, "validation_error")

    urgency = (urgency or "low").strip().lower()
    if urgency not in UrgencyLevel.ALL:
        raise TicketError(f"Invalid urgency: {urgency}", 422, "validation_error")

    try:
        user_count = max(1, int(affected_users_count))
    except (TypeError, ValueError):
        user_count = 1

    dept_id = department_id or getattr(requester, "department_id", None)
    dept = db.session.get(Department, dept_id) if dept_id else getattr(requester, "department", None)
    dept_name = dept.name if dept else getattr(requester, "department_name", None)
    is_vip = getattr(requester, "is_vip", False)
    job_title = getattr(requester, "job_title", None)

    # 1. Run rule-based priority engine
    priority_res = calculate_priority(
        category=category,
        business_impact=impact,
        urgency=urgency,
        affected_users_count=user_count,
        requester_department=dept_name,
        is_vip=is_vip,
        job_title=job_title,
    )
    rec_priority = priority_res.recommended_priority

    # Admin may override priority on creation
    if manual_priority and requester.is_admin() and manual_priority in Priority.ALL:
        final_priority = manual_priority
    else:
        final_priority = rec_priority

    created_at = utcnow()
    deadline = calculate_sla_deadline(final_priority, start_time=created_at)
    ticket_num = _generate_ticket_number()

    ticket = Ticket(
        ticket_number=ticket_num,
        title=title.strip(),
        description=description.strip(),
        category=category,
        business_impact=impact,
        urgency=urgency,
        affected_users_count=user_count,
        recommended_priority=rec_priority,
        final_priority=final_priority,
        status=TicketStatus.OPEN,
        requester_id=requester.id,
        department_id=dept_id,
        sla_deadline=deadline,
        sla_breached=False,
        created_at=created_at,
    )
    db.session.add(ticket)
    db.session.flush()  # Assigns ticket.id

    # Record initial creation and priority history audit entries
    h_create = TicketHistory(
        ticket_id=ticket.id,
        user_id=requester.id,
        action="created",
        field_name="status",
        old_value=None,
        new_value=TicketStatus.OPEN,
        created_at=created_at,
    )
    h_priority = TicketHistory(
        ticket_id=ticket.id,
        user_id=requester.id,
        action="priority_evaluated",
        field_name="recommended_priority",
        old_value=priority_res.justification,
        new_value=f"Recommended: {rec_priority} | Final: {final_priority}",
        created_at=created_at,
    )
    db.session.add_all([h_create, h_priority])
    db.session.commit()

    # In-app notification to administrators
    notify_admins(
        title=f"New Ticket: {ticket.ticket_number}",
        body=f"Ticket '{ticket.title}' submitted by {requester.full_name} ({final_priority} priority).",
        notification_type="ticket_created",
        ticket_id=ticket.id,
    )

    return ticket


def get_ticket_for_user(ticket_id: int, user: User) -> Ticket:
    """Retrieve ticket ensuring role-based access control."""
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketError("Ticket not found", 404, "not_found")

    if user.is_admin():
        return ticket

    if user.is_technician():
        # Technicians can view tickets assigned to them or unassigned open tickets
        tech_profile = db.session.scalar(select(Technician).where(Technician.user_id == user.id))
        if tech_profile and ticket.assigned_technician_id == tech_profile.id:
            return ticket
        if ticket.status in (TicketStatus.OPEN, TicketStatus.ASSIGNED):
            return ticket
        # Or if they are the requester
        if ticket.requester_id == user.id:
            return ticket
        raise TicketError("You do not have permission to view this ticket", 403, "forbidden")

    # Regular employees can only view their own tickets
    if ticket.requester_id != user.id:
        raise TicketError("You do not have permission to view this ticket", 403, "forbidden")

    return ticket


def list_tickets_for_user(
    user: User,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Ticket]:
    """Query tickets with role filtering and optional search filters."""
    query = select(Ticket)

    # Role boundaries
    if user.role == Role.EMPLOYEE:
        query = query.where(Ticket.requester_id == user.id)
    elif user.role == Role.TECHNICIAN:
        tech = db.session.scalar(select(Technician).where(Technician.user_id == user.id))
        if tech:
            query = query.where(
                (Ticket.assigned_technician_id == tech.id)
                | (Ticket.assigned_technician_id.is_(None))
                | (Ticket.requester_id == user.id)
            )
    # Admin sees all

    if status and status in TicketStatus.ALL:
        query = query.where(Ticket.status == status)
    if priority and priority in Priority.ALL:
        query = query.where(Ticket.final_priority == priority)
    if category and category in TicketCategory.ALL:
        query = query.where(Ticket.category == category)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            (Ticket.title.ilike(term))
            | (Ticket.ticket_number.ilike(term))
            | (Ticket.description.ilike(term))
        )

    query = query.order_by(Ticket.created_at.desc())
    return db.session.scalars(query).all()


def update_ticket_status(ticket: Ticket, new_status: str, user: User, note: Optional[str] = None) -> Ticket:
    """Transition ticket status with permission checks and history logging."""
    if new_status not in TicketStatus.ALL:
        raise TicketError(f"Invalid status: {new_status}", 422, "validation_error")

    old_status = ticket.status
    if old_status == new_status:
        return ticket

    # Permissions
    if user.role == Role.EMPLOYEE:
        if old_status in (TicketStatus.RESOLVED, TicketStatus.CLOSED) and new_status == TicketStatus.OPEN:
            pass  # Allowed to reopen
        elif old_status == TicketStatus.RESOLVED and new_status == TicketStatus.CLOSED:
            pass  # Allowed to close
        else:
            raise TicketError("Employees cannot perform this status transition", 403, "forbidden")
    elif user.role == Role.TECHNICIAN:
        if new_status == TicketStatus.CLOSED and not user.is_admin():
            raise TicketError("Only administrators and requesters may close tickets", 403, "forbidden")

    now = utcnow()
    ticket.status = new_status
    if new_status == TicketStatus.RESOLVED:
        ticket.resolved_at = now
    elif new_status == TicketStatus.CLOSED:
        ticket.closed_at = now
    elif new_status == TicketStatus.OPEN and old_status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
        ticket.resolved_at = None
        ticket.closed_at = None

    history_entry = TicketHistory(
        ticket_id=ticket.id,
        user_id=user.id,
        action="status_changed",
        field_name="status",
        old_value=old_status,
        new_value=new_status,
        created_at=now,
    )
    db.session.add(history_entry)

    if note and note.strip():
        comment = TicketComment(
            ticket_id=ticket.id,
            user_id=user.id,
            body=f"Status changed to {new_status}: {note.strip()}",
            created_at=now,
        )
        db.session.add(comment)

    db.session.commit()

    # Notify stakeholders
    notify_ticket_stakeholders(
        ticket=ticket,
        title=f"Ticket {ticket.ticket_number} Updated",
        body=f"Ticket status changed from '{old_status}' to '{new_status}' by {user.full_name}.",
        notification_type="status_changed",
        exclude_user_id=user.id,
    )

    return ticket


def add_ticket_comment(ticket: Ticket, user: User, body: str) -> TicketComment:
    """Add a new comment to a ticket thread."""
    if not body or not body.strip():
        raise TicketError("Comment body is required", 422, "validation_error")

    get_ticket_for_user(ticket.id, user)

    now = utcnow()
    comment = TicketComment(
        ticket_id=ticket.id,
        user_id=user.id,
        body=body.strip(),
        created_at=now,
    )
    history_entry = TicketHistory(
        ticket_id=ticket.id,
        user_id=user.id,
        action="comment_added",
        field_name="comments",
        old_value=None,
        new_value=body.strip()[:100],
        created_at=now,
    )
    db.session.add_all([comment, history_entry])
    db.session.commit()

    notify_ticket_stakeholders(
        ticket=ticket,
        title=f"New comment on {ticket.ticket_number}",
        body=f"{user.full_name} commented: {body.strip()[:120]}...",
        notification_type="comment_added",
        exclude_user_id=user.id,
    )

    return comment


def override_ticket_priority(ticket: Ticket, new_priority: str, admin_user: User, reason: str) -> Ticket:
    """Allow Administrator to manually override ticket priority and record audit."""
    if not admin_user.is_admin():
        raise TicketError("Only administrators can override ticket priority", 403, "forbidden")
    if new_priority not in Priority.ALL:
        raise TicketError(f"Invalid priority: {new_priority}", 422, "validation_error")
    if not reason or not reason.strip():
        raise TicketError("Reason is required when overriding ticket priority", 422, "validation_error")

    old_priority = ticket.final_priority
    ticket.final_priority = new_priority
    ticket.sla_deadline = calculate_sla_deadline(new_priority, start_time=ticket.created_at)

    now = utcnow()
    history_entry = TicketHistory(
        ticket_id=ticket.id,
        user_id=admin_user.id,
        action="priority_overridden",
        field_name="final_priority",
        old_value=f"{old_priority} (Reason: {reason.strip()})",
        new_value=new_priority,
        created_at=now,
    )
    db.session.add(history_entry)
    db.session.commit()

    notify_ticket_stakeholders(
        ticket=ticket,
        title=f"Priority Changed: {ticket.ticket_number}",
        body=f"Priority adjusted to '{new_priority}' by Administrator {admin_user.full_name}.",
        notification_type="priority_override",
        exclude_user_id=admin_user.id,
    )

    return ticket

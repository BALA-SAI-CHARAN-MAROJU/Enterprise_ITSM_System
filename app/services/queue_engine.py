"""Technician Dynamic Work Queue & Dispatch Priority Engine.

Calculates the exact operational priority order for a technician's assigned tickets.
When new issues arrive or deadlines approach, the technician's queue dynamically
re-ranks tickets based on:
1. Incident Severity (Critical/High/Medium/Low)
2. SLA Urgency & Time Remaining
3. Requester Department & VIP / Executive Role Criticality
4. Affected User Volume
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select

from app.constants import Priority, TicketStatus
from app.extensions import db
from app.models import Technician, Ticket, User
from app.utils.datetime import ensure_utc, utcnow


@dataclass
class QueueItem:
    ticket_id: int
    ticket_number: str
    title: str
    category: str
    final_priority: str
    status: str
    sla_deadline: Optional[datetime]
    sla_breached: bool
    time_remaining_str: str
    requester_name: str
    requester_role: str
    requester_department: str
    is_vip: bool
    queue_score: int
    queue_rank: int = 0
    reasons: List[str] = field(default_factory=list)

    @property
    def queue_justification(self) -> str:
        return " | ".join(self.reasons)

    def to_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "ticket_number": self.ticket_number,
            "title": self.title,
            "category": self.category,
            "final_priority": self.final_priority,
            "status": self.status,
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "sla_breached": self.sla_breached,
            "time_remaining_str": self.time_remaining_str,
            "requester_name": self.requester_name,
            "requester_role": self.requester_role,
            "requester_department": self.requester_department,
            "is_vip": self.is_vip,
            "queue_score": self.queue_score,
            "queue_rank": self.queue_rank,
            "reasons": self.reasons,
            "queue_justification": self.queue_justification,
        }


def evaluate_ticket_queue_score(ticket: Ticket, now: Optional[datetime] = None) -> tuple[int, str, List[str]]:
    """Compute dynamic dispatch score and explainable reasons for an active ticket."""
    now_dt = ensure_utc(now or utcnow())
    reasons: List[str] = []
    score = 0

    # 1. Base Priority Weight (0 - 40 pts)
    pri_weights = {
        Priority.CRITICAL: 40,
        Priority.HIGH: 30,
        Priority.MEDIUM: 20,
        Priority.LOW: 10,
    }
    p_score = pri_weights.get(ticket.final_priority, 10)
    score += p_score
    reasons.append(f"{ticket.final_priority} priority (+{p_score} pts)")

    # 2. SLA Breach Urgency (0 - 40 pts)
    time_remaining_str = "No SLA"
    if ticket.sla_breached:
        score += 40
        time_remaining_str = "BREACHED"
        reasons.append("SLA breached: Immediate mitigation required (+40 pts)")
    elif ticket.sla_deadline:
        deadline = ensure_utc(ticket.sla_deadline)
        diff = deadline - now_dt
        total_seconds = diff.total_seconds()

        if total_seconds <= 0:
            score += 40
            time_remaining_str = "BREACHED"
            reasons.append("SLA deadline expired (+40 pts)")
        else:
            hours_left = total_seconds / 3600.0
            if hours_left <= 2.0:
                score += 30
                time_remaining_str = f"{int(total_seconds // 60)} mins left"
                reasons.append(f"Imminent SLA breach ({time_remaining_str}: +30 pts)")
            elif hours_left <= 6.0:
                score += 18
                time_remaining_str = f"{hours_left:.1f} hrs left"
                reasons.append(f"SLA warning window ({time_remaining_str}: +18 pts)")
            else:
                score += 5
                time_remaining_str = f"{hours_left:.1f} hrs left"
                reasons.append(f"Standard SLA window ({time_remaining_str}: +5 pts)")

    # 3. Requester Department & VIP Status (0 - 20 pts)
    requester = ticket.requester
    is_vip = getattr(requester, "is_vip", False) if requester else False
    dept_name = ticket.department.name if ticket.department else (requester.department_name if requester else "General")

    if is_vip:
        score += 15
        reasons.append("VIP / Executive requester priority (+15 pts)")
    elif "executive" in dept_name.lower():
        score += 15
        reasons.append(f"Executive Department issue (+15 pts)")
    elif "finance" in dept_name.lower():
        score += 12
        reasons.append(f"Finance Department payroll/reporting impact (+12 pts)")
    elif "engineering" in dept_name.lower():
        score += 8
        reasons.append(f"Engineering Department production impact (+8 pts)")
    else:
        score += 3
        reasons.append(f"Department '{dept_name}' (+3 pts)")

    # 4. User Impact Scale (0 - 10 pts)
    users = ticket.affected_users_count or 1
    if users >= 50:
        score += 10
        reasons.append(f"Widespread impact ({users} users: +10 pts)")
    elif users >= 10:
        score += 6
        reasons.append(f"Team impact ({users} users: +6 pts)")
    elif users >= 2:
        score += 3
        reasons.append(f"Multiple users ({users} users: +3 pts)")
    else:
        score += 1
        reasons.append("Single user (+1 pt)")

    return score, time_remaining_str, reasons


def get_technician_prioritized_work_queue(technician_id: int) -> List[QueueItem]:
    """Retrieve all active tickets for a technician, dynamically ordered by dispatch priority.
    
    Active statuses: Assigned, In Progress, Pending, On Hold.
    Tickets are scored, sorted by descending queue_score, and given a dynamic rank (1, 2, 3...).
    """
    active_statuses = (TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.PENDING, TicketStatus.ON_HOLD)
    stmt = (
        select(Ticket)
        .where(Ticket.assigned_technician_id == technician_id)
        .where(Ticket.status.in_(active_statuses))
    )
    tickets = db.session.scalars(stmt).all()

    now_dt = utcnow()
    items: List[QueueItem] = []

    for t in tickets:
        score, time_str, reasons = evaluate_ticket_queue_score(t, now=now_dt)
        req = t.requester
        items.append(
            QueueItem(
                ticket_id=t.id,
                ticket_number=t.ticket_number,
                title=t.title,
                category=t.category,
                final_priority=t.final_priority,
                status=t.status,
                sla_deadline=t.sla_deadline,
                sla_breached=t.sla_breached,
                time_remaining_str=time_str,
                requester_name=req.full_name if req else "Unknown",
                requester_role=req.job_title if (req and req.job_title) else "Employee",
                requester_department=t.department.name if t.department else (req.department_name if req else "General"),
                is_vip=getattr(req, "is_vip", False) if req else False,
                queue_score=score,
                reasons=reasons,
            )
        )

    # Sort descending by score, tie-break by SLA deadline ascending (earliest deadline first)
    def sort_key(item: QueueItem):
        deadline_ts = item.sla_deadline.timestamp() if item.sla_deadline else float("inf")
        return (-item.queue_score, deadline_ts)

    items.sort(key=sort_key)

    # Assign queue ranks
    for idx, item in enumerate(items, start=1):
        item.queue_rank = idx

    return items

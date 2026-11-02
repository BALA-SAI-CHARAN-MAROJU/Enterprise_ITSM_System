"""Technician Recommendation and Assignment Engine.

Scores and ranks suitable technicians based on technical expertise,
current active workload, availability status, and concurrent ticket capacity.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy import func, select

from app.constants import Availability, Role, TicketStatus
from app.extensions import db
from app.models import Technician, TechnicianSkill, Ticket, TicketHistory, User
from app.services.notification_service import create_notification
from app.utils.datetime import utcnow


@dataclass
class CandidateEvaluation:
    technician_id: int
    user_id: int
    technician_name: str
    availability_status: str
    has_matching_skill: bool
    active_tickets_count: int
    max_concurrent_tickets: int
    utilization_percent: float
    total_score: float
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "technician_id": self.technician_id,
            "user_id": self.user_id,
            "technician_name": self.technician_name,
            "availability_status": self.availability_status,
            "has_matching_skill": self.has_matching_skill,
            "active_tickets_count": self.active_tickets_count,
            "max_concurrent_tickets": self.max_concurrent_tickets,
            "utilization_percent": round(self.utilization_percent, 1),
            "total_score": round(self.total_score, 1),
            "reasons": self.reasons,
        }


@dataclass
class RecommendationResult:
    recommended_technician_id: Optional[int]
    recommended_technician_name: Optional[str]
    justification: str
    candidates: List[CandidateEvaluation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "recommended_technician_id": self.recommended_technician_id,
            "recommended_technician_name": self.recommended_technician_name,
            "justification": self.justification,
            "candidates": [c.to_dict() for c in self.candidates],
        }


def get_active_workload_counts() -> dict[int, int]:
    """Calculate active ticket count per technician using an aggregate query."""
    active_statuses = (TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.PENDING, TicketStatus.ON_HOLD)
    stmt = (
        select(Ticket.assigned_technician_id, func.count(Ticket.id))
        .where(Ticket.status.in_(active_statuses))
        .where(Ticket.assigned_technician_id.is_not(None))
        .group_by(Ticket.assigned_technician_id)
    )
    rows = db.session.execute(stmt).all()
    return {tech_id: count for tech_id, count in rows}


def recommend_technician_for_ticket(ticket: Ticket) -> RecommendationResult:
    """Evaluate and rank technicians for a given ticket."""
    category = ticket.category
    workloads = get_active_workload_counts()

    stmt = select(Technician).join(Technician.user).where(User.is_active.is_(True))
    technicians = db.session.scalars(stmt).all()

    if not technicians:
        return RecommendationResult(
            recommended_technician_id=None,
            recommended_technician_name=None,
            justification="No registered technicians found in system.",
            candidates=[],
        )

    candidates: List[CandidateEvaluation] = []

    for tech in technicians:
        tech_name = tech.user.full_name if tech.user else f"Tech #{tech.id}"
        reasons: List[str] = []
        is_eligible = True

        # 1. Availability check
        if tech.availability_status != Availability.AVAILABLE:
            reasons.append(f"Status is '{tech.availability_status}' (not available)")
            is_eligible = False
        else:
            reasons.append("Status is 'available'")

        # 2. Workload & capacity check
        active_count = workloads.get(tech.id, 0)
        max_cap = max(1, tech.max_concurrent_tickets)
        utilization = (active_count / max_cap) * 100.0

        if active_count >= max_cap:
            reasons.append(f"Capacity exceeded: {active_count}/{max_cap} tickets active")
            is_eligible = False
        else:
            reasons.append(f"Active workload: {active_count}/{max_cap} tickets ({utilization:.0f}% capacity)")

        # 3. Expertise check
        skill_categories = [s.category for s in tech.skills]
        has_skill = category in skill_categories
        if has_skill:
            reasons.append(f"Has verified expertise in '{category}' (+50 pts)")
        else:
            reasons.append(f"No specialized certification in '{category}' (+0 pts)")

        # Calculate score (only if eligible)
        if not is_eligible:
            total_score = -1.0
        else:
            exp_score = 50.0 if has_skill else 0.0
            workload_score = max(0.0, (1.0 - (active_count / max_cap)) * 50.0)
            total_score = exp_score + workload_score
            reasons.append(f"Calculated match score: {total_score:.1f}/100")

        candidates.append(
            CandidateEvaluation(
                technician_id=tech.id,
                user_id=tech.user_id,
                technician_name=tech_name,
                availability_status=tech.availability_status,
                has_matching_skill=has_skill,
                active_tickets_count=active_count,
                max_concurrent_tickets=max_cap,
                utilization_percent=utilization,
                total_score=total_score,
                reasons=reasons,
            )
        )

    candidates.sort(key=lambda c: (c.total_score, -c.active_tickets_count), reverse=True)

    top = next((c for c in candidates if c.total_score >= 0), None)

    if top is None:
        justification = f"No available technician with available capacity found for category '{category}'."
        return RecommendationResult(
            recommended_technician_id=None,
            recommended_technician_name=None,
            justification=justification,
            candidates=candidates,
        )

    skill_str = "with matching expertise" if top.has_matching_skill else "with general availability"
    justification = (
        f"Recommended {top.technician_name} ({top.total_score:.0f} pts) {skill_str} "
        f"and lowest active workload ({top.active_tickets_count}/{top.max_concurrent_tickets} tickets)."
    )

    return RecommendationResult(
        recommended_technician_id=top.technician_id,
        recommended_technician_name=top.technician_name,
        justification=justification,
        candidates=candidates,
    )


def assign_technician(
    ticket: Ticket,
    technician_id: int,
    assigned_by: User,
    is_override: bool = False,
    override_reason: Optional[str] = None,
) -> Ticket:
    """Assign or override ticket technician assignment and record audit."""
    technician = db.session.get(Technician, technician_id)
    if not technician:
        raise ValueError(f"Technician with ID {technician_id} does not exist")

    old_tech = ticket.assigned_technician.user.full_name if ticket.assigned_technician and ticket.assigned_technician.user else "Unassigned"
    new_tech = technician.user.full_name if technician.user else f"Tech #{technician.id}"

    ticket.assigned_technician_id = technician.id
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.ASSIGNED

    now = utcnow()
    action = "technician_overridden" if is_override else "technician_assigned"
    details = f"{old_tech} -> {new_tech}"
    if override_reason:
        details += f" (Reason: {override_reason.strip()})"

    history_entry = TicketHistory(
        ticket_id=ticket.id,
        user_id=assigned_by.id,
        action=action,
        field_name="assigned_technician_id",
        old_value=old_tech,
        new_value=details,
        created_at=now,
    )
    db.session.add(history_entry)
    db.session.commit()

    # Notify technician
    if technician.user_id:
        create_notification(
            user_id=technician.user_id,
            title=f"Assigned: {ticket.ticket_number}",
            body=f"You have been assigned to handle '{ticket.title}' ({ticket.final_priority} priority).",
            notification_type="ticket_assigned",
            ticket_id=ticket.id,
        )

    # Notify requester
    if ticket.requester_id:
        create_notification(
            user_id=ticket.requester_id,
            title=f"Technician Assigned: {ticket.ticket_number}",
            body=f"Technician {new_tech} has been assigned to investigate your issue.",
            notification_type="ticket_assigned",
            ticket_id=ticket.id,
        )

    return ticket

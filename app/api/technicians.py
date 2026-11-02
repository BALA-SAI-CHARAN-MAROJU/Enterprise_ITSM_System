"""REST API routes for Technicians and Automated Assignment."""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import select

from app.auth.decorators import jwt_roles_required
from app.constants import Availability, Role
from app.extensions import csrf, db
from app.models import Technician, Ticket, User
from app.services.assignment_engine import (
    assign_technician,
    get_active_workload_counts,
    recommend_technician_for_ticket,
)
from app.utils.errors import api_error

api_technicians_bp = Blueprint("api_technicians", __name__)
csrf.exempt(api_technicians_bp)


def _current_api_user() -> User:
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if user_id else None
    if user is None:
        raise ValueError("User not found or inactive")
    return user


@api_technicians_bp.get("")
@jwt_required()
def list_technicians():
    """List all registered technicians with active workload count."""
    workloads = get_active_workload_counts()
    technicians = db.session.scalars(select(Technician)).all()
    results = []
    for t in technicians:
        d = t.to_dict()
        d["active_tickets_count"] = workloads.get(t.id, 0)
        results.append(d)
    return {"technicians": results, "count": len(results)}, 200


@api_technicians_bp.get("/recommendations")
@jwt_required()
def get_recommendations():
    """Get technician recommendation and candidate ranking for a specific ticket."""
    ticket_id = request.args.get("ticket_id", type=int)
    if not ticket_id:
        return api_error("ticket_id parameter is required", 422, "validation_error")

    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        return api_error("Ticket not found", 404, "not_found")

    result = recommend_technician_for_ticket(ticket)
    return {"recommendation": result.to_dict(), "ticket_id": ticket.id}, 200


@api_technicians_bp.post("/assign")
@jwt_required()
@jwt_roles_required(Role.ADMIN)
def assign():
    """Assign or override a technician assignment for a ticket (Admin only)."""
    payload = request.get_json(silent=True) or {}
    ticket_id = payload.get("ticket_id")
    technician_id = payload.get("technician_id")
    is_override = bool(payload.get("is_override", False))
    override_reason = payload.get("override_reason")

    if not ticket_id or not technician_id:
        return api_error("ticket_id and technician_id are required", 422, "validation_error")

    ticket = db.session.get(Ticket, int(ticket_id))
    if not ticket:
        return api_error("Ticket not found", 404, "not_found")

    try:
        user = _current_api_user()
        updated_ticket = assign_technician(
            ticket=ticket,
            technician_id=int(technician_id),
            assigned_by=user,
            is_override=is_override,
            override_reason=override_reason,
        )
    except ValueError as exc:
        return api_error(str(exc), 400, "bad_request")

    return {
        "message": "Technician assigned successfully",
        "ticket": updated_ticket.to_dict(include_history=True),
    }, 200


@api_technicians_bp.put("/<int:tech_id>/availability")
@jwt_required()
def update_availability(tech_id: int):
    """Update technician availability status."""
    user = _current_api_user()
    tech = db.session.get(Technician, tech_id)
    if not tech:
        return api_error("Technician not found", 404, "not_found")

    # Only the technician themselves or an admin can update status
    if tech.user_id != user.id and not user.is_admin():
        return api_error("Permission denied", 403, "forbidden")

    payload = request.get_json(silent=True) or {}
    status = (payload.get("availability_status") or "").strip().lower()
    if status not in Availability.ALL:
        return api_error(f"Invalid availability status: {status}", 422, "validation_error")

    tech.availability_status = status
    db.session.commit()
    return {"technician": tech.to_dict()}, 200


@api_technicians_bp.get("/<int:tech_id>/queue")
@jwt_required()
def get_technician_queue(tech_id: int):
    """Retrieve dynamic prioritized work queue for a specific technician."""
    tech = db.session.get(Technician, tech_id)
    if not tech:
        return api_error("Technician not found", 404, "not_found")
    from app.services.queue_engine import get_technician_prioritized_work_queue
    queue = get_technician_prioritized_work_queue(tech.id)
    return {
        "technician_id": tech.id,
        "technician_name": tech.user.full_name,
        "queue_count": len(queue),
        "queue": [item.to_dict() for item in queue]
    }, 200

"""REST API routes for Ticket Management."""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.constants import Role
from app.extensions import csrf, db
from app.models import User
from app.services.priority_engine import calculate_priority
from app.services.ticket_service import (
    TicketError,
    add_ticket_comment,
    create_ticket,
    get_ticket_for_user,
    list_tickets_for_user,
    override_ticket_priority,
    update_ticket_status,
)
from app.utils.errors import api_error

api_tickets_bp = Blueprint("api_tickets", __name__)
csrf.exempt(api_tickets_bp)


def _current_api_user() -> User:
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if user_id else None
    if user is None:
        raise TicketError("User not found or inactive", 401, "unauthorized")
    return user


@api_tickets_bp.get("")
@jwt_required()
def list_tickets():
    try:
        user = _current_api_user()
        status = request.args.get("status")
        priority = request.args.get("priority")
        category = request.args.get("category")
        search = request.args.get("search")
        tickets = list_tickets_for_user(
            user=user,
            status=status,
            priority=priority,
            category=category,
            search=search,
        )
    except TicketError as exc:
        return api_error(exc.message, exc.status_code, exc.code)
    return {"tickets": [t.to_dict() for t in tickets], "count": len(tickets)}, 200


@api_tickets_bp.post("")
@jwt_required()
def create():
    try:
        user = _current_api_user()
        payload = request.get_json(silent=True) or {}
        ticket = create_ticket(
            requester=user,
            title=payload.get("title"),
            description=payload.get("description"),
            category=payload.get("category"),
            business_impact=payload.get("business_impact"),
            urgency=payload.get("urgency"),
            affected_users_count=payload.get("affected_users_count", 1),
            department_id=payload.get("department_id"),
            manual_priority=payload.get("priority"),
        )
    except TicketError as exc:
        return api_error(exc.message, exc.status_code, exc.code)
    return {"ticket": ticket.to_dict(include_history=True)}, 201


@api_tickets_bp.get("/<int:ticket_id>")
@jwt_required()
def get_one(ticket_id: int):
    try:
        user = _current_api_user()
        ticket = get_ticket_for_user(ticket_id, user)
    except TicketError as exc:
        return api_error(exc.message, exc.status_code, exc.code)
    return {"ticket": ticket.to_dict(include_comments=True, include_history=True)}, 200


@api_tickets_bp.post("/<int:ticket_id>/comments")
@jwt_required()
def add_comment(ticket_id: int):
    try:
        user = _current_api_user()
        ticket = get_ticket_for_user(ticket_id, user)
        payload = request.get_json(silent=True) or {}
        comment = add_ticket_comment(ticket, user, payload.get("body"))
    except TicketError as exc:
        return api_error(exc.message, exc.status_code, exc.code)
    return {"comment": comment.to_dict()}, 201


@api_tickets_bp.put("/<int:ticket_id>/status")
@jwt_required()
def change_status(ticket_id: int):
    try:
        user = _current_api_user()
        ticket = get_ticket_for_user(ticket_id, user)
        payload = request.get_json(silent=True) or {}
        new_status = payload.get("status")
        note = payload.get("note")
        ticket = update_ticket_status(ticket, new_status, user, note=note)
    except TicketError as exc:
        return api_error(exc.message, exc.status_code, exc.code)
    return {"ticket": ticket.to_dict(include_history=True)}, 200


@api_tickets_bp.put("/<int:ticket_id>/priority")
@jwt_required()
def override_priority(ticket_id: int):
    try:
        user = _current_api_user()
        ticket = get_ticket_for_user(ticket_id, user)
        payload = request.get_json(silent=True) or {}
        new_priority = payload.get("priority")
        reason = payload.get("reason")
        ticket = override_ticket_priority(ticket, new_priority, user, reason=reason)
    except TicketError as exc:
        return api_error(exc.message, exc.status_code, exc.code)
    return {"ticket": ticket.to_dict(include_history=True)}, 200


@api_tickets_bp.post("/preview-priority")
@jwt_required()
def preview_priority():
    """Allow client to preview priority engine calculation and reasoning."""
    payload = request.get_json(silent=True) or {}
    result = calculate_priority(
        category=payload.get("category"),
        business_impact=payload.get("business_impact"),
        urgency=payload.get("urgency"),
        affected_users_count=payload.get("affected_users_count", 1),
    )
    return {
        "recommended_priority": result.recommended_priority,
        "total_score": result.total_score,
        "reasons": result.reasons,
        "justification": result.justification,
    }, 200

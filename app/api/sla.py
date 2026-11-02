"""REST API routes for SLA Management."""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import select

from app.auth.decorators import jwt_roles_required
from app.constants import EscalationLevel, Role
from app.extensions import csrf, db
from app.models import Escalation, Ticket
from app.services.sla_engine import get_sla_rules, scan_all_active_tickets_sla, update_sla_rule
from app.utils.errors import api_error

api_sla_bp = Blueprint("api_sla", __name__)
csrf.exempt(api_sla_bp)


@api_sla_bp.get("/rules")
@jwt_required()
def list_rules():
    rules = get_sla_rules()
    return {
        "rules": [
            {
                "priority": r.priority,
                "resolution_hours": float(r.resolution_hours),
                "warning_percent": r.warning_percent,
                "clock_start": r.clock_start,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rules
        ]
    }, 200


@api_sla_bp.put("/rules/<priority>")
@jwt_required()
@jwt_roles_required(Role.ADMIN)
def update_rule(priority: str):
    payload = request.get_json(silent=True) or {}
    hours = payload.get("resolution_hours")
    warning_percent = payload.get("warning_percent", 80)

    if hours is None:
        return api_error("resolution_hours is required", 422, "validation_error")

    try:
        rule = update_sla_rule(
            priority=priority,
            resolution_hours=float(hours),
            warning_percent=int(warning_percent),
        )
    except ValueError as exc:
        return api_error(str(exc), 422, "validation_error")

    return {
        "message": f"SLA rule for {priority} updated",
        "rule": {
            "priority": rule.priority,
            "resolution_hours": float(rule.resolution_hours),
            "warning_percent": rule.warning_percent,
        },
    }, 200


@api_sla_bp.post("/scan")
@jwt_required()
@jwt_roles_required(Role.ADMIN)
def trigger_scan():
    """Trigger manual SLA scan of all active tickets."""
    stats = scan_all_active_tickets_sla()
    return {"message": "SLA scan complete", "stats": stats}, 200


@api_sla_bp.get("/escalations")
@jwt_required()
def list_escalations():
    level = request.args.get("level")
    query = select(Escalation)
    if level and level in EscalationLevel.ALL:
        query = query.where(Escalation.level == level)
    query = query.order_by(Escalation.created_at.desc())
    escalations = db.session.scalars(query).all()
    return {"escalations": [e.to_dict() for e in escalations], "count": len(escalations)}, 200

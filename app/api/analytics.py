"""REST API routes for Operational Analytics and Incident Analysis."""

from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.auth.decorators import jwt_roles_required
from app.constants import Role
from app.extensions import csrf
from app.services.analytics import get_admin_dashboard_metrics, get_technician_performance_analytics
from app.services.incident_analysis import analyze_recurring_incidents

api_analytics_bp = Blueprint("api_analytics", __name__)
csrf.exempt(api_analytics_bp)


@api_analytics_bp.get("/dashboard")
@jwt_required()
@jwt_roles_required(Role.ADMIN)
def admin_dashboard():
    data = get_admin_dashboard_metrics()
    return data, 200


@api_analytics_bp.get("/technicians")
@jwt_required()
@jwt_roles_required(Role.ADMIN)
def technician_performance():
    data = get_technician_performance_analytics()
    return {"technicians": data, "count": len(data)}, 200


@api_analytics_bp.get("/incidents")
@jwt_required()
@jwt_roles_required(Role.ADMIN)
def incident_analysis():
    data = analyze_recurring_incidents()
    return data, 200

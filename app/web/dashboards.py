"""Web views for Dashboards and Analytics Visualizations."""

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.constants import Role, TicketStatus
from app.services.analytics import get_admin_dashboard_metrics, get_technician_performance_analytics
from app.services.incident_analysis import analyze_recurring_incidents
from app.services.ticket_service import list_tickets_for_user

web_dashboards_bp = Blueprint("web_dashboards", __name__)


@web_dashboards_bp.route("/")
def index():
    if current_user.is_authenticated:
        return home()
    return render_template("auth/welcome.html")


@web_dashboards_bp.route("/dashboard")
@login_required
def home():
    tickets = list_tickets_for_user(current_user)
    open_count = sum(1 for t in tickets if t.status in (TicketStatus.OPEN, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.PENDING, TicketStatus.ON_HOLD))
    resolved_count = sum(1 for t in tickets if t.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED))
    critical_count = sum(1 for t in tickets if t.final_priority == "Critical" and t.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED))
    recent_tickets = tickets[:10]

    # Admin Dashboard Extra Analytics & Visualizations
    admin_data = None
    incident_data = None
    tech_performance = None
    tech_queue = None

    if current_user.is_admin():
        admin_data = get_admin_dashboard_metrics()
        incident_data = analyze_recurring_incidents()
        tech_performance = get_technician_performance_analytics()
    elif current_user.is_technician() and current_user.technician_profile:
        from app.services.queue_engine import get_technician_prioritized_work_queue
        tech_queue = get_technician_prioritized_work_queue(current_user.technician_profile.id)

    return render_template(
        "dashboards/home.html",
        total_tickets=len(tickets),
        open_count=open_count,
        resolved_count=resolved_count,
        critical_count=critical_count,
        recent_tickets=recent_tickets,
        admin_data=admin_data,
        incident_data=incident_data,
        tech_performance=tech_performance,
        tech_queue=tech_queue,
    )

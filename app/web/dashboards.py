from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.constants import TicketStatus
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

    recent_tickets = tickets[:5]
    return render_template(
        "dashboards/home.html",
        total_tickets=len(tickets),
        open_count=open_count,
        resolved_count=resolved_count,
        critical_count=critical_count,
        recent_tickets=recent_tickets,
    )

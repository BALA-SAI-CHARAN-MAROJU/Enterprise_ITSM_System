from app.web.admin import web_admin_bp
from app.web.auth import web_auth_bp
from app.web.dashboards import web_dashboards_bp
from app.web.notifications import web_notifications_bp
from app.web.tickets import web_tickets_bp

__all__ = ["web_admin_bp", "web_auth_bp", "web_dashboards_bp", "web_tickets_bp", "web_notifications_bp"]

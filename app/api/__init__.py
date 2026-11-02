from flask import Blueprint

from app.api.analytics import api_analytics_bp
from app.api.auth import api_auth_bp
from app.api.notifications import api_notifications_bp
from app.api.sla import api_sla_bp
from app.api.technicians import api_technicians_bp
from app.api.tickets import api_tickets_bp
from app.api.users import api_users_bp


def create_api_blueprint():
    api_bp = Blueprint("api", __name__)
    api_bp.register_blueprint(api_auth_bp, url_prefix="/auth")
    api_bp.register_blueprint(api_tickets_bp, url_prefix="/tickets")
    api_bp.register_blueprint(api_technicians_bp, url_prefix="/technicians")
    api_bp.register_blueprint(api_sla_bp, url_prefix="/sla")
    api_bp.register_blueprint(api_notifications_bp, url_prefix="/notifications")
    api_bp.register_blueprint(api_analytics_bp, url_prefix="/analytics")
    api_bp.register_blueprint(api_users_bp)
    return api_bp

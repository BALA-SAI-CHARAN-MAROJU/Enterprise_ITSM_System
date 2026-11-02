from flask import Blueprint

from app.api.auth import api_auth_bp


def create_api_blueprint():
    api_bp = Blueprint("api", __name__)
    api_bp.register_blueprint(api_auth_bp, url_prefix="/auth")
    return api_bp

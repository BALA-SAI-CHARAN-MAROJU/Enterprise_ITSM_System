from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager

from app.config import get_config
from app.extensions import csrf, db, jwt, login_manager, migrate
from app.utils.errors import register_error_handlers


def create_app(config_name=None):
    load_dotenv()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(get_config(config_name))
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
        seconds=app.config.get("JWT_ACCESS_TOKEN_EXPIRES_SECONDS", 3600)
    )

    _register_extensions(app)
    _register_blueprints(app)
    _register_cli(app)
    register_error_handlers(app)

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "service": "enterprise-itsm",
            }
        )

    return app


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)

    import app.models  # noqa: F401 — register metadata for Alembic
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @jwt.unauthorized_loader
    def missing_token(_reason):
        from app.utils.errors import api_error

        return api_error("Missing or invalid authorization token", 401, "unauthorized")

    @jwt.invalid_token_loader
    def invalid_token(_reason):
        from app.utils.errors import api_error

        return api_error("Invalid authorization token", 401, "unauthorized")

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        from app.utils.errors import api_error

        return api_error("Authorization token has expired", 401, "unauthorized")


def _register_blueprints(app: Flask) -> None:
    from app.api import create_api_blueprint
    from app.web import web_auth_bp, web_dashboards_bp, web_notifications_bp, web_tickets_bp

    api_bp = create_api_blueprint()
    csrf.exempt(api_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(web_dashboards_bp)
    app.register_blueprint(web_auth_bp)
    app.register_blueprint(web_tickets_bp)
    app.register_blueprint(web_notifications_bp)


def _register_cli(app: Flask) -> None:
    @app.cli.command("seed-defaults")
    def seed_defaults_command():
        """Insert default SLA rules if they are missing."""
        from app.services.defaults import seed_default_sla_rules

        seed_default_sla_rules()
        print("Default SLA rules ensured.")

    @app.cli.command("sla-scan")
    def sla_scan_command():
        """Scan active tickets and apply SLA warnings and breach escalations."""
        from app.services.sla_engine import scan_all_active_tickets_sla

        stats = scan_all_active_tickets_sla()
        print(f"SLA scan completed: {stats['scanned']} tickets scanned, {stats['warnings']} warnings, {stats['breaches']} breaches.")


# Imported so Flask-Migrate / type checkers can see JWTManager on the extension.
__all__ = ["create_app", "JWTManager"]

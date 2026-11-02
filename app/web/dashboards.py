from flask import Blueprint, render_template
from flask_login import current_user, login_required

web_dashboards_bp = Blueprint("web_dashboards", __name__)


@web_dashboards_bp.route("/")
def index():
    if current_user.is_authenticated:
        return render_template("dashboards/home.html")
    return render_template("auth/welcome.html")


@web_dashboards_bp.route("/dashboard")
@login_required
def home():
    return render_template("dashboards/home.html")

"""Web views for Notifications."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.services.notification_service import (
    get_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)

web_notifications_bp = Blueprint("web_notifications", __name__, url_prefix="/notifications")


@web_notifications_bp.route("", methods=["GET"])
@login_required
def list_notifications():
    notifications = get_user_notifications(user_id=current_user.id, limit=50)
    return render_template("notifications/list.html", notifications=notifications)


@web_notifications_bp.route("/<int:notif_id>/read", methods=["POST"])
@login_required
def mark_read(notif_id: int):
    mark_notification_read(notif_id, current_user.id)
    return redirect(url_for("web_notifications.list_notifications"))


@web_notifications_bp.route("/read-all", methods=["POST"])
@login_required
def read_all():
    count = mark_all_notifications_read(current_user.id)
    flash(f"Marked {count} notifications as read.", "info")
    return redirect(url_for("web_notifications.list_notifications"))

"""REST API routes for Notifications."""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import csrf
from app.services.notification_service import (
    get_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from app.utils.errors import api_error

api_notifications_bp = Blueprint("api_notifications", __name__)
csrf.exempt(api_notifications_bp)


@api_notifications_bp.get("")
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    unread_only = request.args.get("unread", "false").lower() == "true"
    limit = min(request.args.get("limit", 50, type=int), 100)
    notifs = get_user_notifications(user_id=user_id, unread_only=unread_only, limit=limit)
    return {"notifications": [n.to_dict() for n in notifs], "count": len(notifs)}, 200


@api_notifications_bp.put("/<int:notif_id>/read")
@jwt_required()
def mark_read(notif_id: int):
    user_id = int(get_jwt_identity())
    success = mark_notification_read(notif_id, user_id)
    if not success:
        return api_error("Notification not found or access denied", 404, "not_found")
    return {"message": "Notification marked as read"}, 200


@api_notifications_bp.put("/read-all")
@jwt_required()
def read_all():
    user_id = int(get_jwt_identity())
    count = mark_all_notifications_read(user_id)
    return {"message": f"{count} notifications marked as read"}, 200

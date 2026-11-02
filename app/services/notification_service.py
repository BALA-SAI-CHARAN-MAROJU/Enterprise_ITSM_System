"""In-App Notification Service.

Creates, queries, and manages in-app notifications for ticket events
(creation, assignment, status updates, SLA warnings, and breaches).
"""

from typing import List, Optional

from sqlalchemy import select

from app.constants import Role
from app.extensions import db
from app.models import Notification, Ticket, User
from app.utils.datetime import utcnow


def create_notification(
    user_id: int,
    title: str,
    body: str,
    notification_type: str,
    ticket_id: Optional[int] = None,
) -> Notification:
    """Create a single in-app notification for a user."""
    notif = Notification(
        user_id=user_id,
        type=notification_type,
        title=title.strip(),
        body=body.strip(),
        ticket_id=ticket_id,
        is_read=False,
        created_at=utcnow(),
    )
    db.session.add(notif)
    db.session.commit()
    return notif


def notify_admins(
    title: str,
    body: str,
    notification_type: str,
    ticket_id: Optional[int] = None,
) -> List[Notification]:
    """Broadcast an in-app notification to all active administrators."""
    admins = db.session.scalars(select(User).where(User.role == Role.ADMIN, User.is_active.is_(True))).all()
    created = []
    now = utcnow()
    for admin in admins:
        notif = Notification(
            user_id=admin.id,
            type=notification_type,
            title=title.strip(),
            body=body.strip(),
            ticket_id=ticket_id,
            is_read=False,
            created_at=now,
        )
        db.session.add(notif)
        created.append(notif)
    if created:
        db.session.commit()
    return created


def notify_ticket_stakeholders(
    ticket: Ticket,
    title: str,
    body: str,
    notification_type: str,
    exclude_user_id: Optional[int] = None,
) -> List[Notification]:
    """Notify the ticket requester, assigned technician, and admins."""
    target_user_ids = set()

    # Requester
    if ticket.requester_id and ticket.requester_id != exclude_user_id:
        target_user_ids.add(ticket.requester_id)

    # Assigned Technician
    if ticket.assigned_technician and ticket.assigned_technician.user_id:
        if ticket.assigned_technician.user_id != exclude_user_id:
            target_user_ids.add(ticket.assigned_technician.user_id)

    # If Critical or Breached, include all admins
    if ticket.final_priority == "Critical" or "breach" in notification_type.lower():
        admin_ids = db.session.scalars(select(User.id).where(User.role == Role.ADMIN, User.is_active.is_(True))).all()
        for a_id in admin_ids:
            if a_id != exclude_user_id:
                target_user_ids.add(a_id)

    now = utcnow()
    created = []
    for uid in target_user_ids:
        notif = Notification(
            user_id=uid,
            type=notification_type,
            title=title.strip(),
            body=body.strip(),
            ticket_id=ticket.id,
            is_read=False,
            created_at=now,
        )
        db.session.add(notif)
        created.append(notif)

    if created:
        db.session.commit()
    return created


def get_user_notifications(user_id: int, unread_only: bool = False, limit: int = 50) -> List[Notification]:
    """Retrieve notifications for a user."""
    query = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
    query = query.order_by(Notification.created_at.desc()).limit(limit)
    return db.session.scalars(query).all()


def mark_notification_read(notification_id: int, user_id: int) -> bool:
    """Mark a notification as read."""
    notif = db.session.get(Notification, notification_id)
    if notif and notif.user_id == user_id:
        notif.is_read = True
        db.session.commit()
        return True
    return False


def mark_all_notifications_read(user_id: int) -> int:
    """Mark all unread notifications for a user as read."""
    notifs = db.session.scalars(
        select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
    ).all()
    count = len(notifs)
    for n in notifs:
        n.is_read = True
    if count > 0:
        db.session.commit()
    return count

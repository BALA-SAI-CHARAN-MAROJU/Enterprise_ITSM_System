from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import TicketStatus
from app.extensions import db
from app.utils.datetime import utcnow


class Ticket(db.Model):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    business_impact: Mapped[str] = mapped_column(String(20), nullable=False)
    urgency: Mapped[str] = mapped_column(String(20), nullable=False)
    affected_users_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    recommended_priority: Mapped[str] = mapped_column(String(20), nullable=False)
    final_priority: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default=TicketStatus.OPEN, nullable=False, index=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    assigned_technician_id: Mapped[int | None] = mapped_column(
        ForeignKey("technicians.id"), index=True
    )
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    requester = relationship("User", back_populates="requested_tickets", foreign_keys=[requester_id])
    assigned_technician = relationship("Technician", back_populates="assigned_tickets")
    department = relationship("Department", back_populates="tickets")
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketComment.created_at.asc()")
    history = relationship("TicketHistory", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketHistory.created_at.desc()")
    escalations = relationship("Escalation", back_populates="ticket", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="ticket")

    def to_dict(self, include_comments: bool = False, include_history: bool = False) -> dict:
        data = {
            "id": self.id,
            "ticket_number": self.ticket_number,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "business_impact": self.business_impact,
            "urgency": self.urgency,
            "affected_users_count": self.affected_users_count,
            "recommended_priority": self.recommended_priority,
            "final_priority": self.final_priority,
            "status": self.status,
            "requester_id": self.requester_id,
            "requester_name": self.requester.full_name if self.requester else None,
            "requester_email": self.requester.email if self.requester else None,
            "assigned_technician_id": self.assigned_technician_id,
            "assigned_technician_name": (
                self.assigned_technician.user.full_name
                if self.assigned_technician and self.assigned_technician.user
                else None
            ),
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "sla_breached": self.sla_breached,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_comments:
            data["comments"] = [comment.to_dict() for comment in self.comments]
        if include_history:
            data["history"] = [entry.to_dict() for entry in self.history]
        return data


class TicketComment(db.Model):
    __tablename__ = "ticket_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User", back_populates="comments")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "author_name": self.author.full_name if self.author else "Unknown",
            "author_role": self.author.role if self.author else None,
            "body": self.body,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TicketHistory(db.Model):
    __tablename__ = "ticket_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(80))
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    ticket = relationship("Ticket", back_populates="history")
    user = relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else "System",
            "action": self.action,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

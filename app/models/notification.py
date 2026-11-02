from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.utils.datetime import utcnow


class Notification(db.Model):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("tickets.id"))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="notifications")
    ticket = relationship("Ticket", back_populates="notifications")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "body": self.body,
            "ticket_id": self.ticket_id,
            "ticket_number": self.ticket.ticket_number if self.ticket else None,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.utils.datetime import utcnow


class Escalation(db.Model):
    __tablename__ = "escalations"
    __table_args__ = (UniqueConstraint("ticket_id", "level", name="uq_ticket_escalation_level"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ticket = relationship("Ticket", back_populates="escalations")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "ticket_number": self.ticket.ticket_number if self.ticket else None,
            "level": self.level,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
        }

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.utils.datetime import utcnow


class SlaRule(db.Model):
    __tablename__ = "sla_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    priority: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    resolution_hours: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    warning_percent: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    clock_start: Mapped[str] = mapped_column(String(20), default="created", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    updated_by = relationship("User")

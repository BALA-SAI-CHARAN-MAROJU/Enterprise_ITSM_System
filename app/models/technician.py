from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants import Availability
from app.extensions import db
from app.utils.datetime import utcnow


class Technician(db.Model):
    __tablename__ = "technicians"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    availability_status: Mapped[str] = mapped_column(
        String(20), default=Availability.AVAILABLE, nullable=False
    )
    max_concurrent_tickets: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="technician_profile")
    skills = relationship("TechnicianSkill", back_populates="technician", cascade="all, delete-orphan")
    assigned_tickets = relationship("Ticket", back_populates="assigned_technician")


class TechnicianSkill(db.Model):
    __tablename__ = "technician_skills"
    __table_args__ = (UniqueConstraint("technician_id", "category", name="uq_technician_category"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    technician_id: Mapped[int] = mapped_column(ForeignKey("technicians.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)

    technician = relationship("Technician", back_populates="skills")

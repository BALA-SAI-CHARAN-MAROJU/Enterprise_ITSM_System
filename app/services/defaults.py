from sqlalchemy import select

from app.constants import DEFAULT_SLA_HOURS
from app.extensions import db
from app.models import SlaRule


def seed_default_sla_rules() -> None:
    """Insert default SLA targets when the table is empty. Safe to run repeatedly."""
    existing = db.session.scalars(select(SlaRule.priority)).all()
    existing_set = set(existing)
    for priority, hours in DEFAULT_SLA_HOURS.items():
        if priority in existing_set:
            continue
        db.session.add(
            SlaRule(
                priority=priority,
                resolution_hours=hours,
                warning_percent=80,
                clock_start="created",
            )
        )
    db.session.commit()

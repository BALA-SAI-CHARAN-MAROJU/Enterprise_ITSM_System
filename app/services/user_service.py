"""User and Corporate Role Management Service.

Provides administrative capabilities to view employees, assign designated
departments, corporate job titles, VIP executive status, and configure
technician specializations and certified skills.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.constants import Availability, Role, TicketCategory
from app.extensions import db
from app.models import Department, Technician, TechnicianSkill, User


class UserServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "bad_request"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def list_all_users() -> List[User]:
    """Retrieve all corporate users with eager loading of departments and technician profiles."""
    stmt = (
        select(User)
        .options(
            selectinload(User.department),
            selectinload(User.technician_profile).selectinload(Technician.skills),
        )
        .order_by(User.id.asc())
    )
    return db.session.scalars(stmt).all()


def get_user_by_id(user_id: int) -> Optional[User]:
    """Retrieve single user by ID with department and technician profile loaded."""
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.department),
            selectinload(User.technician_profile).selectinload(Technician.skills),
        )
    )
    return db.session.scalar(stmt)


def list_departments() -> List[Department]:
    """Retrieve all available corporate departments."""
    stmt = select(Department).order_by(Department.name.asc())
    return db.session.scalars(stmt).all()


def update_employee_role_and_assignment(
    user_id: int,
    role: str,
    department_id: Optional[int],
    job_title: Optional[str] = None,
    is_vip: bool = False,
    is_active: bool = True,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    tier: int = 1,
    specialization: Optional[str] = None,
    skills: Optional[List[str]] = None,
) -> User:
    """Admin function to assign or modify an employee's designated corporate role.
    
    Updates job title, corporate department, VIP status, system role,
    and configures technician tier and skills if promoted to technician.
    """
    user = db.session.get(User, user_id)
    if not user:
        raise UserServiceError(f"User with ID {user_id} not found", 404, "not_found")

    role_norm = (role or "").strip().lower()
    if role_norm not in Role.ALL:
        raise UserServiceError(f"Invalid role '{role}'. Allowed: {list(Role.ALL)}", 422, "validation_error")

    if department_id:
        dept = db.session.get(Department, department_id)
        if not dept:
            raise UserServiceError(f"Department ID {department_id} does not exist", 422, "validation_error")
        user.department_id = dept.id
    else:
        user.department_id = None

    user.role = role_norm
    if job_title is not None:
        user.job_title = job_title.strip() or "Employee"
    user.is_vip = bool(is_vip)
    user.is_active = bool(is_active)

    if first_name and first_name.strip():
        user.first_name = first_name.strip()
    if last_name and last_name.strip():
        user.last_name = last_name.strip()

    # If role is technician, ensure technician profile and skills are configured
    if role_norm == Role.TECHNICIAN:
        tech = user.technician_profile
        if not tech:
            tech = Technician(
                user_id=user.id,
                availability_status=Availability.AVAILABLE,
                max_concurrent_tickets=10,
                tier=max(1, min(3, int(tier))),
                specialization=specialization.strip() if specialization else "General IT Support",
            )
            db.session.add(tech)
            db.session.flush()
        else:
            tech.tier = max(1, min(3, int(tier)))
            if specialization:
                tech.specialization = specialization.strip()

        # Update skills if provided
        if skills is not None:
            # Delete previous skills
            stmt = select(TechnicianSkill).where(TechnicianSkill.technician_id == tech.id)
            for old_skill in db.session.scalars(stmt).all():
                db.session.delete(old_skill)
            db.session.flush()

            for sk in skills:
                if sk in TicketCategory.ALL:
                    db.session.add(TechnicianSkill(technician_id=tech.id, category=sk))

    db.session.commit()
    return user

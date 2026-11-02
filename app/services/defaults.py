from sqlalchemy import select

from app.constants import Availability, DEFAULT_SLA_HOURS, Role, TicketCategory
from app.extensions import db
from app.models import Department, SlaRule, Technician, TechnicianSkill, User


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


def seed_organization_data() -> None:
    """Seed enterprise departments, differentiated employee roles, and specialized technicians.
    
    Safe to run repeatedly (idempotent).
    """
    seed_default_sla_rules()

    # 1. Seed Departments
    departments_data = [
        {"name": "Executive", "description": "C-Suite & Board Leadership (Highest Organizational Priority)"},
        {"name": "Finance & Accounting", "description": "Financial Operations, Billing, ERP & Payroll Systems"},
        {"name": "Software Engineering", "description": "Core Platform Engineering, DevOps & Cloud Services"},
        {"name": "Human Resources", "description": "People Operations, Talent Acquisition & Benefits"},
        {"name": "Sales & Client Success", "description": "Enterprise Revenue Operations & CRM Infrastructure"},
        {"name": "Operations", "description": "Global Workplace Operations, Logistics & Facilities"},
    ]

    dept_map: dict[str, Department] = {}
    for d_data in departments_data:
        dept = db.session.scalar(select(Department).where(Department.name == d_data["name"]))
        if not dept:
            dept = Department(name=d_data["name"], description=d_data["description"])
            db.session.add(dept)
            db.session.flush()
        dept_map[d_data["name"]] = dept

    # 2. Seed Specialized Employees
    users_data = [
        {
            "email": "admin@itsm.local",
            "first_name": "System",
            "last_name": "Admin",
            "role": Role.ADMIN,
            "job_title": "IT Director & System Administrator",
            "is_vip": True,
            "department": dept_map["Executive"],
            "password": "AdminPass123!",
        },
        {
            "email": "ceo@itsm.local",
            "first_name": "John",
            "last_name": "Vance",
            "role": Role.EMPLOYEE,
            "job_title": "Chief Executive Officer (CEO)",
            "is_vip": True,
            "department": dept_map["Executive"],
            "password": "CeoPass123!",
        },
        {
            "email": "cfo@itsm.local",
            "first_name": "Sarah",
            "last_name": "Jenkins",
            "role": Role.EMPLOYEE,
            "job_title": "Chief Financial Officer (CFO)",
            "is_vip": True,
            "department": dept_map["Finance & Accounting"],
            "password": "CfoPass123!",
        },
        {
            "email": "devops@itsm.local",
            "first_name": "Alex",
            "last_name": "Rivera",
            "role": Role.EMPLOYEE,
            "job_title": "Lead Cloud Infrastructure Engineer",
            "is_vip": False,
            "department": dept_map["Software Engineering"],
            "password": "DevPass123!",
        },
        {
            "email": "emp.carol@itsm.local",
            "first_name": "Carol",
            "last_name": "Danvers",
            "role": Role.EMPLOYEE,
            "job_title": "HR Operations Specialist",
            "is_vip": False,
            "department": dept_map["Human Resources"],
            "password": "EmpPass123!",
        },
    ]

    for u_data in users_data:
        user = db.session.scalar(select(User).where(User.email == u_data["email"]))
        if not user:
            user = User(
                email=u_data["email"],
                first_name=u_data["first_name"],
                last_name=u_data["last_name"],
                role=u_data["role"],
                job_title=u_data["job_title"],
                is_vip=u_data["is_vip"],
                department_id=u_data["department"].id if u_data.get("department") else None,
                is_active=True,
            )
            user.set_password(u_data["password"])
            db.session.add(user)
            db.session.flush()

    # 3. Seed Specialized Problem-Solver Technicians
    tech_data = [
        {
            "email": "tech.alice@itsm.local",
            "first_name": "Alice",
            "last_name": "Walker",
            "job_title": "Tier 3 Senior Cybersecurity & Database Specialist",
            "tier": 3,
            "specialization": "Security & Database Architecture",
            "skills": [TicketCategory.SECURITY, TicketCategory.DATABASE],
            "max_tickets": 8,
            "password": "TechPass123!",
        },
        {
            "email": "tech.bob@itsm.local",
            "first_name": "Bob",
            "last_name": "Martin",
            "job_title": "Tier 2 Network & Systems Infrastructure Specialist",
            "tier": 2,
            "specialization": "Network Outages & Hardware Infrastructure",
            "skills": [TicketCategory.NETWORK, TicketCategory.HARDWARE],
            "max_tickets": 10,
            "password": "TechPass123!",
        },
        {
            "email": "tech.charlie@itsm.local",
            "first_name": "Charlie",
            "last_name": "Davis",
            "job_title": "Tier 1 Application Support Specialist",
            "tier": 1,
            "specialization": "Software Applications & End-User Support",
            "skills": [TicketCategory.SOFTWARE, TicketCategory.OTHER],
            "max_tickets": 12,
            "password": "TechPass123!",
        },
    ]

    for t_data in tech_data:
        u = db.session.scalar(select(User).where(User.email == t_data["email"]))
        if not u:
            u = User(
                email=t_data["email"],
                first_name=t_data["first_name"],
                last_name=t_data["last_name"],
                role=Role.TECHNICIAN,
                job_title=t_data["job_title"],
                is_vip=False,
                department_id=dept_map["Operations"].id,
                is_active=True,
            )
            u.set_password(t_data["password"])
            db.session.add(u)
            db.session.flush()

        tech = db.session.scalar(select(Technician).where(Technician.user_id == u.id))
        if not tech:
            tech = Technician(
                user_id=u.id,
                availability_status=Availability.AVAILABLE,
                max_concurrent_tickets=t_data["max_tickets"],
                tier=t_data["tier"],
                specialization=t_data["specialization"],
            )
            db.session.add(tech)
            db.session.flush()

            for sk in t_data["skills"]:
                db.session.add(TechnicianSkill(technician_id=tech.id, category=sk))

    db.session.commit()

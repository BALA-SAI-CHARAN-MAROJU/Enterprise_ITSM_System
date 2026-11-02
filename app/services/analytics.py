"""Analytics and Metrics Aggregation Service.

Computes system-wide operational metrics, technician performance analytics,
SLA compliance percentages, and data formatted for Chart.js dashboards.
"""

from datetime import timedelta
from typing import Any, Dict, List

from sqlalchemy import func, select

from app.constants import Priority, Role, TicketCategory, TicketStatus
from app.extensions import db
from app.models import Technician, Ticket, User
from app.utils.datetime import ensure_utc, utcnow


def get_admin_dashboard_metrics() -> Dict[str, Any]:
    """Aggregate high-level KPIs and chart series for the Admin Dashboard."""
    # 1. High-level status and priority counts
    total_tickets = db.session.scalar(select(func.count(Ticket.id))) or 0

    open_statuses = (TicketStatus.OPEN, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.PENDING, TicketStatus.ON_HOLD)
    open_tickets = db.session.scalar(select(func.count(Ticket.id)).where(Ticket.status.in_(open_statuses))) or 0

    resolved_statuses = (TicketStatus.RESOLVED, TicketStatus.CLOSED)
    resolved_tickets = db.session.scalar(select(func.count(Ticket.id)).where(Ticket.status.in_(resolved_statuses))) or 0

    critical_active = db.session.scalar(
        select(func.count(Ticket.id))
        .where(Ticket.final_priority == Priority.CRITICAL)
        .where(Ticket.status.in_(open_statuses))
    ) or 0

    sla_breaches_total = db.session.scalar(select(func.count(Ticket.id)).where(Ticket.sla_breached.is_(True))) or 0

    # Overall SLA Compliance Rate for resolved tickets
    resolved_all = db.session.scalars(select(Ticket).where(Ticket.status.in_(resolved_statuses))).all()
    if resolved_all:
        on_time_count = sum(1 for t in resolved_all if not t.sla_breached)
        sla_compliance_rate = round((on_time_count / len(resolved_all)) * 100.0, 1)
    else:
        sla_compliance_rate = 100.0

    # 2. Category Distribution (for Chart.js doughnut chart)
    # Equivalent SQL: SELECT category, COUNT(id) FROM tickets GROUP BY category;
    cat_stmt = select(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category)
    cat_rows = db.session.execute(cat_stmt).all()
    cat_dict = {cat: 0 for cat in TicketCategory.ALL}
    for cat, count in cat_rows:
        cat_dict[cat] = count

    category_labels = list(cat_dict.keys())
    category_data = [cat_dict[k] for k in category_labels]

    # 3. Priority Distribution
    pri_stmt = select(Ticket.final_priority, func.count(Ticket.id)).group_by(Ticket.final_priority)
    pri_rows = db.session.execute(pri_stmt).all()
    pri_dict = {p: 0 for p in Priority.ALL}
    for p, count in pri_rows:
        pri_dict[p] = count

    priority_labels = list(pri_dict.keys())
    priority_data = [pri_dict[k] for k in priority_labels]

    # 4. 7-Day Ticket Creation Trend
    now = utcnow()
    trend_labels = []
    trend_created = []
    trend_resolved = []

    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_str = day_start.strftime("%b %d")
        trend_labels.append(day_str)

        created_c = db.session.scalar(
            select(func.count(Ticket.id))
            .where(Ticket.created_at >= day_start)
            .where(Ticket.created_at < day_end)
        ) or 0
        trend_created.append(created_c)

        resolved_c = db.session.scalar(
            select(func.count(Ticket.id))
            .where(Ticket.resolved_at >= day_start)
            .where(Ticket.resolved_at < day_end)
        ) or 0
        trend_resolved.append(resolved_c)

    # 5. Technician Workload Bar Data
    techs = db.session.scalars(select(Technician).join(Technician.user).where(User.is_active.is_(True))).all()
    tech_labels = []
    tech_active_loads = []
    tech_capacities = []

    for t in techs:
        t_name = t.user.full_name if t.user else f"Tech #{t.id}"
        t_active = sum(1 for ticket in t.assigned_tickets if ticket.status in open_statuses)
        tech_labels.append(t_name)
        tech_active_loads.append(t_active)
        tech_capacities.append(t.max_concurrent_tickets)

    return {
        "kpis": {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "resolved_tickets": resolved_tickets,
            "critical_active": critical_active,
            "sla_breaches": sla_breaches_total,
            "sla_compliance_rate": sla_compliance_rate,
        },
        "charts": {
            "categories": {
                "labels": category_labels,
                "data": category_data,
            },
            "priorities": {
                "labels": priority_labels,
                "data": priority_data,
            },
            "trends": {
                "labels": trend_labels,
                "created": trend_created,
                "resolved": trend_resolved,
            },
            "workloads": {
                "labels": tech_labels,
                "active": tech_active_loads,
                "capacity": tech_capacities,
            },
        },
    }


def get_technician_performance_analytics() -> List[Dict[str, Any]]:
    """Compute individual KPI metrics and SLA compliance rates per technician."""
    techs = db.session.scalars(select(Technician).join(Technician.user)).all()
    results = []

    for tech in techs:
        tech_user = tech.user
        assigned_tickets = tech.assigned_tickets

        total_assigned = len(assigned_tickets)
        resolved_tickets = [t for t in assigned_tickets if t.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED)]
        resolved_count = len(resolved_tickets)
        pending_count = sum(1 for t in assigned_tickets if t.status in (TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.PENDING, TicketStatus.ON_HOLD))

        # Average resolution time in hours
        total_res_seconds = 0.0
        resolved_with_time = 0
        resolved_within_sla = 0

        for t in resolved_tickets:
            if not t.sla_breached:
                resolved_within_sla += 1
            if t.resolved_at and t.created_at:
                res_time = (ensure_utc(t.resolved_at) - ensure_utc(t.created_at)).total_seconds()
                if res_time > 0:
                    total_res_seconds += res_time
                    resolved_with_time += 1

        if resolved_with_time > 0:
            avg_res_hours = round(total_res_seconds / (resolved_with_time * 3600.0), 1)
        else:
            avg_res_hours = 0.0

        if resolved_count > 0:
            compliance_rate = round((resolved_within_sla / resolved_count) * 100.0, 1)
        else:
            compliance_rate = 100.0

        results.append({
            "technician_id": tech.id,
            "name": tech_user.full_name if tech_user else "Unknown",
            "email": tech_user.email if tech_user else "",
            "availability_status": tech.availability_status,
            "skills": [s.category for s in tech.skills],
            "total_assigned": total_assigned,
            "active_tickets": pending_count,
            "resolved_tickets": resolved_count,
            "avg_resolution_hours": avg_res_hours,
            "sla_compliance_rate": compliance_rate,
            "max_concurrent_tickets": tech.max_concurrent_tickets,
        })

    return results

"""Shared enumerations. Keep values stable; they are stored in the database."""


class Role:
    ADMIN = "admin"
    TECHNICIAN = "technician"
    EMPLOYEE = "employee"
    ALL = (ADMIN, TECHNICIAN, EMPLOYEE)


class TicketStatus:
    OPEN = "Open"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    PENDING = "Pending"
    ON_HOLD = "On Hold"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    ALL = (OPEN, ASSIGNED, IN_PROGRESS, PENDING, ON_HOLD, RESOLVED, CLOSED)


class TicketCategory:
    NETWORK = "Network"
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    DATABASE = "Database"
    SECURITY = "Security"
    OTHER = "Other"
    ALL = (NETWORK, HARDWARE, SOFTWARE, DATABASE, SECURITY, OTHER)


class Priority:
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    ALL = (CRITICAL, HIGH, MEDIUM, LOW)


class ImpactLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    ALL = (LOW, MEDIUM, HIGH, CRITICAL)


class UrgencyLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    ALL = (LOW, MEDIUM, HIGH, CRITICAL)


class Availability:
    AVAILABLE = "available"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"
    ALL = (AVAILABLE, BUSY, UNAVAILABLE)


class EscalationLevel:
    WARNING = "warning"
    BREACH = "breach"
    ALL = (WARNING, BREACH)


DEFAULT_SLA_HOURS = {
    Priority.CRITICAL: 2,
    Priority.HIGH: 6,
    Priority.MEDIUM: 24,
    Priority.LOW: 48,
}

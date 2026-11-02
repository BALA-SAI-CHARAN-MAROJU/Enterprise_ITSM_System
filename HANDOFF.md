# Agent Handoff — Enterprise IT Service Management System

Another agent must be able to continue from this file alone. Do not rely on chat history.

## 1. Project Overview
Enterprise IT Service Management (ITSM) web application with intelligent rule-based ticket prioritization, automated technician assignment, SLA monitoring, and performance analytics.

- **Stack:** Python 3.14, Flask 3.1.1, SQLAlchemy 2.0.44 ORM, Flask-Migrate / Alembic, PostgreSQL 16 (SQLite for local dev & testing), Jinja2 + Bootstrap 5.3 + Plus Jakarta Sans + Chart.js, Pytest 8.3.4, Docker & Docker Compose.
- **Architecture:** Modular monolith using application factory (`create_app`), Blueprints (`/api` and web), and dedicated service layer (`app/services`).

## 2. Current Development Phase & Status
- **Current State:** **All 9 functional modules are fully implemented, enhanced with Admin Corporate Role Management, Problem-Based Assignment, and Dynamic Technician Priority Queue Re-ordering, verified by 51 automated tests.**
- **Overall Completion:** **100% Core Functionality, Executive UI, Admin Role Management & Dynamic Queue Engine Complete**
- **Automated Test Results:** **51 passed (100% pass rate)**

## 3. What Has Been Implemented and Verified
1. **Module 1: Authentication & User Management:**
   - Registration, login, logout, profile update.
   - Dual authentication: Web session cookies (Flask-Login + CSRF) and REST API (Flask-JWT-Extended).
   - Role-Based Access Control (`admin`, `technician`, `employee`).
   - Corporate employee role differentiation: Job titles, Departments (`Executive`, `Finance & Accounting`, `Software Engineering`, `Human Resources`, `Sales & Client Success`, `Operations`), and `is_vip` Executive flag.
   - **Admin Employee Directory & Role Assignment Module (`/admin/users`, `/admin/users/<id>/edit`, and REST API `/api/users/*`)**: allows administrators to view all personnel and designate their corporate department, job title, VIP priority status, system access role, and configure technician tiers and problem-solving skills.
2. **Module 2: Ticket Management:**
   - Sequential ticket numbering format: `INC-YYYY-XXXXX`.
   - SLA deadline automatically calculated from priority.
   - Full lifecycle status transitions: `Open` -> `Assigned` -> `In Progress` -> `Pending` -> `Resolved` -> `Closed`.
   - Employee reopening capability.
   - Threaded comments (`TicketComment`) and chronological audit trail (`TicketHistory`).
   - Web views (`/tickets`, `/tickets/new`, `/tickets/<id>`) and REST endpoints (`/api/tickets/*`).
3. **Module 3: Intelligent Ticket Prioritization Engine:**
   - Deterministic rule engine in `app/services/priority_engine.py`.
   - Weighs business impact (0–40 pts), urgency (0–30 pts), affected users (0–20 pts), category modifiers (Security +10, Database +8, Network +8), Department business continuity weighting (`Executive` +15, `Finance` +10, `Engineering` +8), and VIP Requester status (+15 pts).
   - Generates human-readable justification reasons and assigns recommended priority (`Critical`, `High`, `Medium`, `Low`).
   - Admin override supported with mandatory justification audit log.
4. **Module 4: Automated Technician Recommendation & Dynamic Work Queue Re-ordering:**
   - Matches specific problem domain to certified technician skill category (`technician_skills`).
   - Workload balance calculation and availability check (`available`, `busy`, `unavailable`).
   - Technician tiers (Tier 1 Support, Tier 2 Systems, Tier 3 Senior Specialist).
   - **Dynamic Work Queue Priority Engine (`app/services/queue_engine.py`)**: calculates a technician's dynamic dispatch score (0-100+) based on incident severity, SLA countdown, and VIP/Department impact. Re-orders tickets dynamically (Rank #1, #2, #3...) when higher urgency or VIP issues arrive.
   - REST API endpoint: `GET /api/technicians/<tech_id>/queue`.
   - Admin manual assignment and override workflow.
5. **Module 5: SLA Monitoring & Escalation:**
   - Configurable SLA priority rules (Critical: 2h, High: 6h, Medium: 24h, Low: 48h).
   - SLA warning threshold detection (80% elapsed time) and overdue breach detection.
   - Idempotent escalation logging (`escalations` table) and CLI scanner command (`flask sla-scan`).
6. **Module 6: Incident Analysis:**
   - Heuristic recurring incident detection in `app/services/incident_analysis.py`.
   - Tokenizes issue titles/descriptions, extracts frequent keyword patterns, and generates explainable hypotheses.
7. **Module 7: Technician Performance Analytics:**
   - Tracks total assigned tickets, active workload, resolved tickets, average resolution time (hours), and SLA compliance rate.
8. **Module 8: Admin Dashboard Visualizations:**
   - Real-time KPI summary cards.
   - Chart.js visualizations for 7-day volume trends, category distribution, priority breakdown, and technician workloads.
   - Incident analysis table with hypotheses.
9. **Module 9: In-App Notifications:**
   - Event-driven notifications for ticket creation, technician assignment, status changes, SLA warnings, and breaches.
   - Notification inbox web view (`/notifications`) and REST endpoints (`/api/notifications/*`).
10. **Docker Implementation:**
    - `Dockerfile` (Python 3.12-slim base, non-root user `appuser`, healthcheck, Gunicorn).
    - `docker-compose.yml` (multi-container orchestration: Flask web app + PostgreSQL 16 container with persistent named volume `postgres_data`).
    - `.dockerignore` and updated `.env.example`.

## 4. Key File Locations
- Application Factory: `app/__init__.py`
- Configuration: `app/config.py`
- Enums & Constants: `app/constants.py`
- Database Models: `app/models/` (`user.py`, `ticket.py`, `technician.py`, `sla.py`, `department.py`, `escalation.py`, `notification.py`)
- Business Services: `app/services/`
  - Priority Engine: `app/services/priority_engine.py`
  - Assignment Engine: `app/services/assignment_engine.py`
  - Ticket Service: `app/services/ticket_service.py`
  - SLA Engine: `app/services/sla_engine.py`
  - Analytics Service: `app/services/analytics.py`
  - Incident Analysis: `app/services/incident_analysis.py`
  - Notification Service: `app/services/notification_service.py`
  - Default Seeder: `app/services/defaults.py`
  - Auth Service: `app/services/auth_service.py`
- REST APIs: `app/api/` (`auth.py`, `tickets.py`, `technicians.py`, `sla.py`, `notifications.py`, `analytics.py`)
- Web Views: `app/web/` (`auth.py`, `tickets.py`, `notifications.py`, `dashboards.py`, `forms.py`)
- Templates: `app/templates/` (`base.html`, `tickets/`, `notifications/`, `auth/`, `dashboards/`)
- Tests: `tests/` (`test_auth.py`, `test_tickets.py`, `test_priority.py`, `test_assignment.py`, `test_sla.py`, `test_analytics.py`, `test_health.py`, `test_security.py`)
- Containers: `Dockerfile`, `docker-compose.yml`, `.dockerignore`

## 5. How to Run Application and Tests
### Run Tests:
```powershell
.\.venv\Scripts\pytest.exe -v
```

### Run Web Application Locally:
```powershell
$env:FLASK_APP = "wsgi.py"
$env:FLASK_CONFIG = "development"
.\.venv\Scripts\flask.exe run --port 5000
```

### Run with Docker Compose:
```bash
docker compose up --build
```

### Run SLA Background Scan:
```powershell
.\.venv\Scripts\flask.exe sla-scan
```

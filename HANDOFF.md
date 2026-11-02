# Agent Handoff — Enterprise IT Service Management System

Another agent must be able to continue from this file alone. Do not rely on chat history.

## 1. Project Overview
Enterprise IT Service Management (ITSM) web application with intelligent rule-based ticket prioritization, automated technician assignment, SLA monitoring, and performance analytics.

- **Stack:** Python 3.14, Flask, SQLAlchemy 2.0 ORM, Flask-Migrate / Alembic, PostgreSQL (SQLite for local dev & testing), Jinja2 + Bootstrap 5 + Chart.js, Pytest.
- **Architecture:** Modular monolith using application factory (`create_app`), Blueprints (`/api` and web), and dedicated service layer (`app/services`).

## 2. Current Development Phase & Status
- **Current State:** Modules 1, 2, and 3 are fully completed, integrated with both REST API and Web UI, and covered by automated tests.
- **Overall Completion:** ~50%
- **Automated Test Results:** **28 passing tests** (0 failures).

## 3. What Has Been Implemented and Verified
1. **Module 1: Authentication & User Management:**
   - Registration, login, logout, profile update.
   - Password hashing with PBKDF2:SHA256.
   - Dual authentication: Web session cookies (Flask-Login + CSRF) and REST API (Flask-JWT-Extended).
   - Role-Based Access Control (`admin`, `technician`, `employee`).
2. **Module 3: Intelligent Ticket Prioritization Engine:**
   - Deterministic rule engine in `app/services/priority_engine.py`.
   - Weighs business impact (0–40 pts), urgency (0–30 pts), affected users (0–20 pts), and category modifiers (e.g., Security +10, Database +8, Network +8).
   - Generates human-readable justification reasons and assigns recommended priority (`Critical`, `High`, `Medium`, `Low`).
   - Admin override supported with mandatory justification audit log.
3. **Module 2: Ticket Management:**
   - Service in `app/services/ticket_service.py`.
   - Sequential ticket numbering format: `INC-YYYY-XXXXX`.
   - SLA deadline automatically calculated from priority.
   - Full lifecycle status transitions: `Open` -> `Assigned` -> `In Progress` -> `Pending` -> `Resolved` -> `Closed`.
   - Employee reopening capability.
   - Threaded comments (`TicketComment`) and chronological audit trail (`TicketHistory`).
   - Web views (`/tickets`, `/tickets/new`, `/tickets/<id>`) and REST endpoints (`/api/tickets/*`).
4. **Interactive UI:**
   - Bootstrap 5 responsive shell (`app/templates/base.html`).
   - Live interactive priority estimation on ticket creation page (`tickets/create.html`).
   - Dashboard with ticket count metrics (`dashboards/home.html`).

## 4. Key File Locations
- Application Factory: `app/__init__.py`
- Configuration: `app/config.py`
- Enums & Constants: `app/constants.py`
- Database Models: `app/models/` (`user.py`, `ticket.py`, `technician.py`, `sla.py`, `department.py`, `escalation.py`, `notification.py`)
- Business Services: `app/services/`
  - Priority Engine: `app/services/priority_engine.py`
  - Ticket Service: `app/services/ticket_service.py`
  - Default Seeder: `app/services/defaults.py`
  - Auth Service: `app/services/auth_service.py`
- REST APIs: `app/api/` (`auth.py`, `tickets.py`)
- Web Views: `app/web/` (`auth.py`, `tickets.py`, `dashboards.py`, `forms.py`)
- Templates: `app/templates/` (`base.html`, `tickets/`, `auth/`, `dashboards/`)
- Tests: `tests/` (`test_auth.py`, `test_tickets.py`, `test_priority.py`, `test_health.py`, `test_security.py`)

## 5. How to Run Application and Tests
### Run Tests:
```powershell
.\.venv\Scripts\pytest.exe -v
```

### Run Web Application:
```powershell
$env:FLASK_APP = "wsgi.py"
$env:FLASK_CONFIG = "development"
.\.venv\Scripts\flask.exe run --port 5000
```

## 6. Exact Next Development Task
Proceed to **Module 4: Automated Technician Recommendation & Assignment Engine**:
1. Implement `app/services/assignment_engine.py`:
   - Match eligible technicians based on `TechnicianSkill.category == ticket.category`.
   - Filter by `availability_status == 'available'`.
   - Rank technicians by lowest active ticket workload (tickets in `Open`, `Assigned`, `In Progress`, `Pending`).
   - Respect `max_concurrent_tickets` cap.
   - Return recommended technician along with an explainable justification score and reason.
2. Implement assignment APIs & web actions:
   - `GET /api/technicians/recommendations?ticket_id=<id>`
   - `POST /api/technicians/assign` (Admin assign or auto-assign with manual override).
   - Display recommended technician and assignment controls on ticket detail page.
3. Write Pytest tests in `tests/test_assignment.py` and verify all tests pass.

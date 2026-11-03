# Enterprise IT Service Management System

Intelligent ticket prioritization and automated service delivery for internal IT support — a **modular Flask monolith** with PostgreSQL, REST APIs, Docker, and cloud-portable configuration.

This project is built to demonstrate enterprise application development, security, testing, and deployment skills (IBM Delivery Consultant style). Ticket priority and technician assignment are **rule-based decision engines**, not machine learning, ensuring complete operational transparency and auditability.

**Status:** **Fully Implemented and Tested (42/42 Tests Passing)**

---

## 1. Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | Python 3, Flask, Blueprints | Application factory pattern (`create_app`), modular service architecture |
| **Database** | PostgreSQL 16 & SQLAlchemy ORM | Declarative mapping, foreign key cascades, transaction integrity |
| **Migrations** | Flask-Migrate & Alembic | Schema migration and versioning |
| **Authentication** | Flask-Login & Flask-JWT-Extended | Session authentication with CSRF for Web UI; Bearer tokens for REST APIs |
| **Security** | Werkzeug PBKDF2:SHA256 | Cryptographic password hashing, role-based decorators (`Role.ADMIN`, `Role.TECHNICIAN`, `Role.EMPLOYEE`) |
| **Frontend** | HTML5, Bootstrap 5.3, Chart.js | Responsive enterprise UI with interactive live priority estimators and charts |
| **Testing** | Pytest | 42 unit, integration, and security tests |
| **Containers** | Docker & Docker Compose | Multi-container setup (`web` app + `db` PostgreSQL with persistent volume) |
| **WSGI Server** | Gunicorn | Production-ready HTTP application server |

---

## 2. Core Functional Modules

### Module 1: Authentication and User Management
- Secure user registration, login, and session logout.
- Dual-mode authentication: browser sessions (cookies with CSRF protection) and REST API (JWT bearer tokens).
- Role-Based Access Control (Admin, Employee, and Technician).
- User profile management with password modification.

### Module 2: Ticket Management
- Sequential human-readable ticket numbers: `INC-YYYY-XXXXX`.
- Ticket creation with automatic priority calculation and SLA deadline computation.
- Complete lifecycle status transitions: `Open` $\rightarrow$ `Assigned` $\rightarrow$ `In Progress` $\rightarrow$ `Pending` $\rightarrow$ `Resolved` $\rightarrow$ `Closed`.
- Employee ticket reopening workflow.
- Threaded ticket discussion comments and complete chronological audit history trail.
- Role-based visibility isolation (employees see own requests; technicians see assigned queue; admins see all).

### Module 3: Intelligent Ticket Prioritization Engine
- Rule-based evaluation matrix based on 4 dimensions:
  1. **Business Impact:** Critical (40 pts), High (30 pts), Medium (20 pts), Low (10 pts).
  2. **Urgency:** Critical (30 pts), High (22 pts), Medium (14 pts), Low (6 pts).
  3. **Affected Users:** $\ge 50$ (20 pts), 11–49 (15 pts), 2–10 (10 pts), 1 user (5 pts).
  4. **Category Modifiers:** Security (+10), Database (+8), Network (+8), Hardware (+4), Software (+0).
- Transparent priority output: **Critical**, **High**, **Medium**, or **Low** with point-by-point explainable reasons.
- Admin manual override with required audit justification logging.

### Module 4: Automated Technician Recommendation
- Intelligent technician match ranking:
  - Technical skills qualification (matching category in `technician_skills`).
  - Active workload balance (tickets in `Assigned`, `In Progress`, `Pending`).
  - Availability status (`available` vs `busy` / `unavailable`).
  - Maximum concurrent ticket capacity limits.
- Generates score and recommendation reason with full admin manual assignment override.

### Module 5: SLA Monitoring & Escalation
- SLA targets per priority: Critical (2 hours), High (6 hours), Medium (24 hours), Low (48 hours).
- Automatic SLA deadline calculation at ticket creation.
- Warning threshold detection (e.g. 80% time elapsed) and overdue breach detection.
- Background SLA scanner command: `flask sla-scan`.
- Idempotent escalation logging (`escalations` table).

### Module 6: Incident Analysis
- Pattern analysis identifying recurring technical failures across categories and departments.
- Title and description tokenization with stop-word filtering to surface keyword clusters (e.g. repeated VPN dropouts or printer hardware failures).
- Automated hypothesis generation detailing affected departments, frequency, and sample tickets.

### Module 7: Technician Performance Analytics
- Tracks total assigned tickets, active tickets, and resolved tickets per technician.
- Calculates average resolution time in hours.
- Computes SLA compliance rate percentage for each technician.

### Module 8: Admin Dashboard Visualizations
- Real-time KPI summary cards (Total Tickets, Active Issues, Critical Tickets, Resolved Tickets, SLA Compliance Rate).
- Interactive Chart.js visualizations:
  - **7-Day Ticket Activity Trend** (Line Chart comparing Created vs. Resolved volume).
  - **Ticket Category Distribution** (Doughnut Chart).
  - **Priority Breakdown** (Bar Chart).
  - **Technician Workload vs Capacity** (Bar Chart).
- Incident analysis table and technician performance scorecard.

### Module 9: In-App Notifications
- Event-driven notifications triggered on ticket creation, technician assignment, status transitions, SLA warnings, and breaches.
- User notification inbox view (`/notifications`) with read / mark-all-read capabilities.

---

## 3. Installation and Running

### Local Development (without Docker)

1. **Activate virtual environment:**
   ```powershell
   # Windows PowerShell
   .\.venv\Scripts\activate
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```
3. **Configure Environment:**
   Copy `.env.example` to `.env` (SQLite is configured by default for development):
   ```bash
   cp .env.example .env
   ```
4. **Seed default SLA rules:**
   ```bash
   flask seed-defaults
   ```
5. **Start Flask development server:**
   ```bash
   flask run --port 5000
   ```
   Open your browser at: `http://localhost:5000`

---

## 4. Docker Implementation

The system is fully containerized with Docker and Docker Compose, orchestrating the web application and a PostgreSQL 16 database.

### Docker Commands

1. **Build and start all containers:**
   ```bash
   docker compose up --build
   ```
2. **Run in detached (background) mode:**
   ```bash
   docker compose up -d
   ```
3. **View live container logs:**
   ```bash
   docker compose logs -f web
   ```
4. **Run database migrations inside the container:**
   ```bash
   docker compose exec web flask db upgrade
   docker compose exec web flask seed-defaults
   ```
5. **Run background SLA scan inside the container:**
   ```bash
   docker compose exec web flask sla-scan
   ```
6. **Stop containers (persisting database volume):**
   ```bash
   docker compose down
   ```
7. **Stop containers and remove volumes:**
   ```bash
   docker compose down -v
   ```

---

## 5. Automated Testing

The project includes 42 automated tests covering all modules:

```powershell
.\.venv\Scripts\pytest.exe -v
```

**Test Coverage Summary:**
- `tests/test_priority.py`: 5 tests (rule weights, category boosts, safety overrides).
- `tests/test_tickets.py`: 7 tests (ticket API creation, validations, role isolation, comments, lifecycle transitions, reopen).
- `tests/test_assignment.py`: 5 tests (skill match, workload ranking, availability filtering, admin assignment RBAC).
- `tests/test_sla.py`: 5 tests (warning threshold, breach detection, scan engine, SLA rules API, notifications flow).
- `tests/test_analytics.py`: 4 tests (KPI aggregation, technician performance metrics, recurring incident keyword detection, API RBAC).
- `tests/test_auth.py` & `tests/test_security.py`: 14 tests (registration, password hashing, JWT bearer tokens, profile updates, production secret enforcement).
- `tests/test_health.py`: 2 tests (health check endpoint, app config).

---

## 6. Cloud Deployment Readiness (AWS / IBM Cloud)

The application is structured for cloud deployment:
- **Stateless Web Application:** Sessions are stored via client-side signed cookies, and APIs use stateless JWTs.
- **Environment-based Configuration:** All sensitive secrets (`SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL`) are read from environment variables; `ProductionConfig` refuses to start with default insecure keys.
- **Production WSGI:** Gunicorn is configured in `Dockerfile` and `wsgi.py`.
- **Database Portability:** Uses SQLAlchemy with PostgreSQL (`psycopg` v3 driver) compatible with AWS RDS, IBM Cloud Databases for PostgreSQL, or containerized Docker Compose.
- **Container Portability:** Compatible with AWS App Runner, AWS ECS, IBM Cloud Code Engine, or a standalone Linux VM.
#   E n t e r p r i s e _ I T S M _ S y s t e m  
 
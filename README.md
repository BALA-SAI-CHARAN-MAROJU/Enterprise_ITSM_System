# 🚀 Enterprise IT Service Management System (ITSM)

**Intelligent Ticket Prioritization | Automated Technician Assignment | SLA Monitoring**

An enterprise-style IT Service Management application designed to streamline internal IT support operations through intelligent, rule-based ticket prioritization, automated technician recommendations, SLA monitoring, and operational analytics.

Built using a **modular Flask monolith architecture** with PostgreSQL, REST APIs, Docker, and cloud-portable configuration.

The project demonstrates enterprise application development practices, including secure authentication, role-based access control, database management, automated testing, containerization, and deployment readiness.

> **Note:** Ticket prioritization and technician assignment use transparent, rule-based decision engines rather than machine learning, ensuring explainability, operational transparency, and auditability.

<p align="center">

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Framework-black?logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)
![Tests](https://img.shields.io/badge/Tests-51%2F51%20Passing-brightgreen)
![Architecture](https://img.shields.io/badge/Architecture-Modular%20Monolith-orange)

</p>

<details>
<summary><strong>📑 Table of Contents</strong></summary>

- [Project Overview](#-project-overview)
- [Technology Stack](#-technology-stack)
- [Core Functional Modules](#-core-functional-modules)
  - [Authentication and User Management](#1-authentication-and-user-management)
  - [Ticket Management](#2-ticket-management)
  - [Intelligent Ticket Prioritization](#3-intelligent-ticket-prioritization-engine)
  - [Automated Technician Recommendation](#4-automated-technician-recommendation)
  - [SLA Monitoring and Escalation](#5-sla-monitoring--escalation)
  - [Incident Analysis](#6-incident-analysis)
  - [Technician Performance Analytics](#7-technician-performance-analytics)
  - [Admin Dashboard](#8-admin-dashboard-and-visualizations)
  - [In-App Notifications](#9-in-app-notifications)
- [Architecture and Design](#-architecture-and-design)
- [Installation and Setup](#-installation-and-setup)
- [Docker Implementation](#-docker-implementation)
- [Automated Testing](#-automated-testing)
- [Cloud Deployment Readiness](#-cloud-deployment-readiness)
- [Future Scope](#-future-scope)

</details>

---

## 📌 Project Overview

Enterprise IT Service Management System is a web-based application that helps organizations manage internal IT support requests, track incidents, assign technicians, and monitor service-level agreements.

The system provides three primary user roles:

| Role | Responsibilities |
|---|---|
| **Admin** | Manage users, view all tickets, assign technicians, override priorities, and monitor system analytics. |
| **Technician** | View assigned tickets, update ticket statuses, communicate with employees, and resolve incidents. |
| **Employee** | Create support requests, track ticket progress, communicate with technicians, and reopen resolved tickets. |

### Key Highlights

- Rule-based ticket prioritization with explainable scoring.
- Automated technician recommendations based on skills, workload, and availability.
- SLA deadline calculation, warning detection, and escalation.
- Role-based access control and secure authentication.
- Recurring incident identification and technician performance analytics.
- Interactive administrative dashboard.
- Docker-based application and database orchestration.
- Automated test suite with **51 passing tests**.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
|---|---|---|
| Backend | Python 3, Flask, Blueprints | Application factory pattern and modular service architecture |
| Database | PostgreSQL 16, SQLAlchemy ORM | Relational database management and transaction integrity |
| Migrations | Flask-Migrate, Alembic | Database schema migration and versioning |
| Authentication | Flask-Login, Flask-JWT-Extended | Session authentication and JWT-based REST API authentication |
| Security | Werkzeug PBKDF2:SHA256 | Password hashing and role-based authorization |
| Frontend | HTML5, Bootstrap 5.3 | Responsive user interface |
| Visualization | Chart.js | Interactive dashboard charts |
| Testing | Pytest | Unit, integration, and security testing |
| Containers | Docker, Docker Compose | Multi-container application deployment |
| WSGI Server | Gunicorn | Production-ready application server |

---

## ⚙️ Core Functional Modules

### 1. Authentication and User Management

Implements secure authentication and user access management.

**Features:**
- User registration, login, and logout.
- Session-based authentication for the web interface.
- JWT bearer token authentication for REST APIs.
- CSRF protection for browser sessions.
- Role-Based Access Control (RBAC).
- Three user roles: Admin, Technician, and Employee.
- User profile management and password modification.
- Secure password hashing using PBKDF2:SHA256.

### 2. Ticket Management

Provides complete incident and support request lifecycle management.

**Features:**
- Sequential human-readable ticket IDs.

  ```text
  INC-YYYY-XXXXX
  ```

- Ticket creation with automatic priority calculation.
- Automatic SLA deadline assignment.
- Complete ticket lifecycle management:

  ```text
  Open → Assigned → In Progress → Pending → Resolved → Closed
  ```

- Employee ticket reopening workflow.
- Threaded ticket discussion and comments.
- Chronological audit history.
- Role-based ticket visibility:
  - Employees can view their own requests.
  - Technicians can view their assigned tickets.
  - Administrators can access all tickets.

### 3. Intelligent Ticket Prioritization Engine

A transparent, rule-based scoring engine that determines ticket priority based on business impact, urgency, affected users, and ticket category.

**Priority Evaluation Matrix**

| Evaluation Factor | Condition | Score |
|---|---|---:|
| Business Impact | Critical | 40 |
| | High | 30 |
| | Medium | 20 |
| | Low | 10 |
| Urgency | Critical | 30 |
| | High | 22 |
| | Medium | 14 |
| | Low | 6 |
| Affected Users | 50 or more | 20 |
| | 11–49 | 15 |
| | 2–10 | 10 |
| | 1 user | 5 |

**Category Modifiers**

| Category | Additional Points |
|---|---:|
| Security | +10 |
| Database | +8 |
| Network | +8 |
| Hardware | +4 |
| Software | +0 |

**Features:**
- Automatic ticket priority calculation.
- Four priority levels: Critical, High, Medium, and Low.
- Point-by-point explanation of priority decisions.
- Administrator priority override.
- Mandatory audit justification for manual overrides.

### 4. Automated Technician Recommendation

Recommends suitable technicians using a rule-based matching and ranking mechanism.

**Evaluation Factors:**

- **Technical Skills:** Matches ticket categories against technician expertise.
- **Workload Balance:** Considers active tickets in Assigned, In Progress, and Pending states.
- **Availability:** Checks whether technicians are available, busy, or unavailable.
- **Capacity Limits:** Considers maximum concurrent ticket capacity.

**Features:**
- Technician recommendation and ranking.
- Recommendation scores and explanations.
- Workload-aware assignment.
- Availability-based filtering.
- Administrator-controlled manual assignment override.

### 5. SLA Monitoring & Escalation

Monitors service-level agreements and identifies tickets approaching or exceeding their resolution deadlines.

**SLA Targets**

| Priority | Resolution Target |
|---|---:|
| Critical | 2 Hours |
| High | 6 Hours |
| Medium | 24 Hours |
| Low | 48 Hours |

**Features:**
- Automatic SLA deadline calculation during ticket creation.
- SLA warning detection at configurable thresholds (e.g., 80% of the allotted time).
- Overdue ticket and breach detection.
- Background SLA scanning command.
- Idempotent escalation logging to prevent duplicate escalation records.

**SLA Scanner Command**

```bash
flask sla-scan
```

### 6. Incident Analysis

Identifies recurring technical problems and patterns across departments and ticket categories.

**Features:**
- Analyses ticket titles and descriptions.
- Tokenization and stop-word filtering.
- Identifies recurring technical issue keywords.
- Detects patterns such as repeated VPN disconnections and printer failures.
- Generates incident hypotheses.
- Displays affected departments, issue frequency, and sample tickets.

### 7. Technician Performance Analytics

Provides insights into technician productivity and service resolution performance.

**Metrics Tracked:**
- Total assigned tickets.
- Active tickets.
- Resolved tickets.
- Average ticket resolution time in hours.
- SLA compliance percentage.

### 8. Admin Dashboard and Visualizations

Provides administrators with a centralized view of IT support operations.

**Dashboard KPI Cards:**
- Total Tickets.
- Active Issues.
- Critical Tickets.
- Resolved Tickets.
- SLA Compliance Rate.

**Interactive Chart.js Visualizations:**

| Visualization | Purpose |
|---|---|
| 7-Day Ticket Activity Trend | Compares created and resolved ticket volumes |
| Ticket Category Distribution | Displays ticket distribution by category |
| Priority Breakdown | Shows ticket distribution across priority levels |
| Technician Workload vs Capacity | Compares technician workload against available capacity |

Additional dashboard features:
- Incident analysis table.
- Technician performance scorecard.
- Operational KPI monitoring.

### 9. In-App Notifications

Provides event-driven notifications to keep users informed about ticket activity.

**Notification Triggers:**
- Ticket creation.
- Technician assignment.
- Ticket status transitions.
- SLA warnings.
- SLA breaches.

**Features:**
- User notification inbox.
- Individual notification read status.
- Mark-all-as-read functionality.

---

## 🏗️ Architecture and Design

The application follows a **Modular Monolith Architecture** using Flask Blueprints and the application factory pattern.

### Architectural Principles

- Separation of application modules and responsibilities.
- Centralized application configuration.
- SQLAlchemy-based database access.
- REST API endpoints for application operations.
- Role-based authorization.
- Environment-driven configuration.
- Reusable services and business logic.
- Containerized deployment.

The modular monolith approach keeps the application maintainable while avoiding unnecessary microservice complexity.

---

## 💻 Installation and Setup

### Prerequisites

Make sure the following tools are installed:

- Python 3
- PostgreSQL 16 (for PostgreSQL-based configuration)
- Git
- Docker and Docker Compose (for containerized execution)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Enterprise_ITSM_System
```

### 2. Create and Activate a Virtual Environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements-dev.txt
```

### 4. Configure Environment Variables

Create your environment configuration file from the example:

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

**Linux / macOS**

```bash
cp .env.example .env
```

SQLite is configured by default for local development. Configure the appropriate database connection through environment variables when using PostgreSQL.

### 5. Seed Default SLA Rules

```bash
flask seed-defaults
```

### 6. Start the Flask Application

```bash
flask run --port 5000
```

Open the application in your browser:

```text
http://localhost:5000
```

---

## 🐳 Docker Implementation

The application is fully containerized using Docker and Docker Compose.

The setup orchestrates:

| Container | Responsibility |
|---|---|
| `web` | Flask application |
| `db` | PostgreSQL 16 database |

A persistent Docker volume is used to retain database data across container restarts.

### Docker Commands

**1. Build and start all containers**

```bash
docker compose up --build
```

**2. Start containers in detached mode**

```bash
docker compose up -d
```

**3. View application logs**

```bash
docker compose logs -f web
```

**4. Run database migrations**

```bash
docker compose exec web flask db upgrade
```

**5. Seed default SLA rules**

```bash
docker compose exec web flask seed-defaults
```

**6. Run the SLA scanner**

```bash
docker compose exec web flask sla-scan
```

**7. Stop containers while preserving database data**

```bash
docker compose down
```

**8. Stop containers and remove persistent volumes**

```bash
docker compose down -v
```

> ⚠️ The final command removes Docker volumes and their stored database data. Use it carefully.

---

## 🧪 Automated Testing

The project includes **51 automated tests** covering core application functionality, business logic, API behavior, authentication, and security.

<details>
<summary><strong>View Test Coverage Breakdown</strong></summary>

| Test File | Tests | Coverage |
|---|---:|---|
| `test_priority.py` | 5 | Priority weights, category modifiers, safety overrides |
| `test_tickets.py` | 7 | Ticket creation, validation, role isolation, comments, lifecycle transitions, reopening |
| `test_assignment.py` | 5 | Skill matching, workload ranking, availability filtering, assignment authorization |
| `test_sla.py` | 5 | Warning thresholds, breach detection, SLA scanning, API rules, notifications |
| `test_analytics.py` | 4 | KPI aggregation, technician performance, recurring incident detection, API authorization |
| `test_roles_and_queue.py` | 4 | Corporate roles, problem-based assignment, dynamic queue priority re-ordering |
| `test_admin_roles.py` | 5 | Admin employee directory, role assignments, VIP status, technician promotions |
| `test_auth.py` and `test_security.py` | 14 | Registration, password hashing, JWT authentication, profile updates, production secret enforcement |
| `test_health.py` | 2 | Health check endpoint and application configuration |
| **Total** | **51** | **All tests passing** |

</details>

### Run the Test Suite

**Windows PowerShell**

```powershell
.\.venv\Scripts\pytest.exe -v
```

**Expected Result**

```text
51 passed
```

<blockquote>
<strong>Test Status:</strong> All 51 automated tests are passing.
</blockquote>

---

## ☁️ Cloud Deployment Readiness

The application is designed with cloud portability in mind and can be adapted for deployment on AWS or IBM Cloud.

### Deployment Considerations

**1. Stateless Web Application**
- Uses client-side signed cookies for browser sessions.
- Uses stateless JWT bearer tokens for REST API authentication.

**2. Environment-Based Configuration**
- Sensitive configuration values are managed through environment variables.
- Includes `SECRET_KEY`, `JWT_SECRET_KEY`, and `DATABASE_URL`.
- Production configuration rejects default insecure secret keys.

**3. Production WSGI Server**
- Uses Gunicorn as the production WSGI application server.
- Configured through the Dockerfile and `wsgi.py`.

**4. Database Portability**
- Uses SQLAlchemy ORM.
- Supports PostgreSQL through the Psycopg v3 driver.
- Can be configured for AWS RDS or IBM Cloud Databases for PostgreSQL.

**5. Container Portability**

The Dockerized application is suitable for deployment using platforms such as:

| Cloud Platform | Potential Deployment Service |
|---|---|
| AWS | AWS App Runner |
| AWS | Amazon ECS |
| IBM Cloud | IBM Cloud Code Engine |
| General | Standalone Linux VM |

---

## 🔮 Future Scope

Potential areas for further development include:

- Deployment to AWS or IBM Cloud.
- Automated scheduled SLA scanning.
- Email-based notification integration.
- Advanced operational reporting.
- Additional integrations with enterprise IT support tools.

---

## 📌 Project Status

<p align="center">

**FULLY IMPLEMENTED AND TESTED**

### 51 / 51 Tests Passing

</p>

The project demonstrates a complete modular enterprise-style application with authentication, ticket management, rule-based decision engines, SLA monitoring, analytics, REST APIs, Docker containerization, and automated testing.

---

## 👨‍💻 Author

**Maroju Bala Sai Charan**

B.Tech – Computer Science and Engineering

[GitHub](https://github.com/BALA-SAI-CHARAN-MAROJU) · [LinkedIn](https://linkedin.com/in/balasaicharanmaroju23022)

---

<p align="center">
<strong>Built to demonstrate enterprise application development, operational transparency, and cloud-ready engineering practices.</strong>
</p>
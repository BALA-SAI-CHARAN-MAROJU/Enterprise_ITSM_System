# Enterprise IT Service Management System

Intelligent ticket prioritization and automated service delivery for internal IT support — a **modular Flask monolith** with PostgreSQL, REST APIs, Docker, and cloud-portable configuration.

This project is built to demonstrate enterprise application development, security, testing, and deployment skills (IBM Delivery Consultant internship style). Ticket priority and technician assignment are **rule-based decision engines**, not machine learning.

**Status:** Architecture and planning complete. Application code starts after architecture approval.

---

## Features (target)

- Role-based access: **Admin**, **Technician**, **Employee**
- Ticket lifecycle (Open → Assigned → In Progress → On Hold → Resolved → Closed)
- Rule-based priority recommendation with admin override (recommended vs final priority stored separately)
- Technician recommendation from expertise, availability, and workload
- Configurable SLA targets, warnings, breaches, and escalation history
- Recurring-incident analysis (explainable heuristics, not claimed root-cause AI)
- Technician performance analytics and Chart.js dashboards
- In-app notifications
- REST JSON API plus server-rendered Bootstrap 5 UI
- Docker Compose (Flask + PostgreSQL) and Gunicorn-ready production config

---

## Technologies

| Area | Choice |
| ---- | ------ |
| Backend | Python 3, Flask, Blueprints, SQLAlchemy, Flask-Migrate |
| Auth | Flask-Login (web sessions), Flask-JWT-Extended (API), Werkzeug password hashing, CSRF on forms |
| Database | PostgreSQL |
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js |
| Tests | Pytest, Flask test client |
| Containers | Docker, Docker Compose |
| Production | Gunicorn, env-based config, `/health` |

---

## Architecture (short)

Five layers: presentation, REST API, business logic, database, authentication/authorization. See [ARCHITECTURE.md](ARCHITECTURE.md) for folder layout, ER diagram, engine rules, and deployment shape.

Task tracking: [TASKS.md](TASKS.md). Agent continuation: [HANDOFF.md](HANDOFF.md).

---

## Installation and running

Application packages are **not implemented yet**. After implementation, the intended flow is:

### Local (without Docker)

1. Install Python 3.11+ and PostgreSQL.
2. Create a virtual environment and install `requirements.txt`.
3. Copy `.env.example` to `.env` and set `SECRET_KEY`, `JWT_SECRET_KEY`, and `DATABASE_URL`. Never hardcode secrets.
4. Run migrations: `flask db upgrade`.
5. Start: `flask run` (development) or `gunicorn wsgi:app` (production-style).

### Docker

```bash
docker compose up --build
```

Compose will include a Flask/Gunicorn service, PostgreSQL, a persistent volume, and a database healthcheck. Exact files land in Phase 4.

---

## API overview

Planned prefix `/api`. Examples:

- `POST /api/auth/login`, `POST /api/auth/register`
- `GET|POST /api/tickets`, `GET|PUT|DELETE /api/tickets/<id>`
- `GET /api/technicians`, `POST /api/technicians/assign`
- `GET /api/analytics/dashboard`, `GET /api/analytics/technicians`
- `GET /api/sla/rules`, `GET /api/sla/breaches`
- `GET /health`

Full request/response documentation will live in `docs/API.md` after endpoints exist.

---

## Deployment

The app is portable: configuration via environment variables, no cloud vendor SDK required for the core product.

Affordable approaches (no assumption of paid managed services):

- A single VM (AWS Lightsail / small EC2 / IBM Cloud VSI) running Docker Compose
- A container platform (IBM Cloud Code Engine, AWS App Runner, or similar) plus a PostgreSQL instance

See ARCHITECTURE.md §10 and the future production section of this README after Phase 6.

---

## Tests

```bash
pytest
```

No tests exist until Phase 5 / early Phase 2 foundation tests.

---

## License

Not specified. Add a license only if the project owner requests one.

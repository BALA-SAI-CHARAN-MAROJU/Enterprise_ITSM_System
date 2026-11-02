# Agent Handoff — Enterprise IT Service Management System

Another agent must be able to continue from this file alone. Do not rely on chat history.

## 1. What the project does

Enterprise IT Service Management (ITSM) web application: employees create support tickets; a **rule-based** (not ML) engine recommends priority; admins assign technicians using a workload/expertise recommender; SLA timers drive warnings and escalations; dashboards show analytics and recurring-incident hypotheses.

Target audience: IBM Delivery Consultant internship demonstration of enterprise application development and deployment.

## 2. Technologies used (planned)

Python 3, Flask (blueprints, application factory), SQLAlchemy, Flask-Migrate/Alembic, PostgreSQL, Flask-Login + Flask-WTF CSRF (browser), Flask-JWT-Extended (REST), Jinja2 + Bootstrap 5 + Chart.js, Pytest, Docker Compose, Gunicorn for production.

## 3. Current development phase

**Phase 1 complete as planning artifacts only.** Waiting for **user approval** before writing application code.

Overall completion: planning only (~8%).

Last updated: 2026-11-02.

## 4. What has been implemented

Documentation only:

- `README.md` — overview and future run instructions
- `ARCHITECTURE.md` — layers, folder tree, ER design, engines, Docker/cloud, security
- `TASKS.md` — checklist
- `HANDOFF.md` — this file

No Python package, no Docker files, no database, no tests yet.

## 5. What is currently working

Nothing runnable. Workspace had no prior source code.

## 6. What remains incomplete

Everything in Phases 2–7 of `TASKS.md`: Flask app, models, auth, tickets, engines, UI, Docker, tests, production config, API docs, screenshots.

## 7. Known errors and bugs

None in code. Open product decisions (already recorded in ARCHITECTURE.md):

- Integer primary keys; human `ticket_number`.
- SLA clock starts at ticket **creation** (`clock_start=created`).
- Default resolution hours: Critical 2, High 6, Medium 24, Low 48.
- Public registration creates **employee** only; admins create technicians/admins.
- Hard delete of tickets discouraged; admin closes tickets. Exact DELETE API behavior: prefer 405 or close-only unless admin force-delete is required later.
- Email notifications optional (`MAIL_ENABLED`); in-app first.
- Scheduler: single replica with `ENABLE_SCHEDULER=true` + PostgreSQL advisory lock.
- Web sessions for UI; JWT for `/api/*`.

## 8. Important file locations

```
ARCHITECTURE.md     system design
TASKS.md            checklist (mark [x] only after verified work)
HANDOFF.md          this handoff
README.md           user-facing overview
```

Proposed code root after approval: `app/` as described in ARCHITECTURE.md.

## 9. How to start the application

Not applicable until Phase 2+. After implementation, expected commands (do not assume they exist yet):

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # then edit
flask db upgrade
flask run
```

Docker (planned):

```bash
docker compose up --build
```

## 10. How to run tests

Not applicable yet. Planned:

```bash
pip install -r requirements-dev.txt
pytest
```

## 11. Database setup instructions

Planned: PostgreSQL 16. `DATABASE_URL=postgresql+psycopg://user:pass@host:5432/itsm`.

Migrations via Flask-Migrate. No schema exists until models + `flask db init/migrate/upgrade`.

## 12. Docker commands

Not created. See ARCHITECTURE.md section 10 for intended Compose layout (`web` + `db`, volume, healthcheck).

## 13. Environment variables required (planned)

Do not commit real values.

| Variable | Purpose |
| -------- | ------- |
| SECRET_KEY | Flask sessions / CSRF |
| JWT_SECRET_KEY | API tokens |
| DATABASE_URL | SQLAlchemy URL |
| FLASK_ENV / FLASK_CONFIG | development / production / testing |
| ENABLE_SCHEDULER | true on one web replica only |
| MAIL_ENABLED | false until email is implemented |

## 14. The exact next task to implement

**STOP if the user has not approved the architecture.**

After explicit approval, implement **Phase 2 foundation only**:

1. Create folder structure under `app/`.
2. `requirements.txt` with pinned reasonable versions.
3. `app/config.py`, `app/extensions.py`, `create_app`.
4. SQLAlchemy models matching ARCHITECTURE.md.
5. Flask-Migrate initial migration.
6. `/health` endpoint.
7. `.gitignore` and `.env.example`.
8. Minimal Pytest proving the app factory and health endpoint.
9. Update TASKS.md / HANDOFF.md with what was actually verified.

Do **not** generate the entire application in one pass. Do **not** put logic in a single `app.py`. Preserve this architecture unless the user requests a change.

## Continuation summary

Inspect `ARCHITECTURE.md` and `TASKS.md` first. User instruction was: analyse, propose, document, **wait for approval**. Implementation has not started.

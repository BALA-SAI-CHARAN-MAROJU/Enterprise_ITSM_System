# REST API Documentation

Base URL: `/api`

### Error Envelope
All error responses return a standardized JSON format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Ticket title is required"
  }
}
```

Standard error codes: `validation_error` (422), `bad_request` (400), `unauthorized` (401), `forbidden` (403), `not_found` (404), `conflict` (409), `internal_error` (500).

---

## Endpoint Catalog

| Method | Path | Auth | Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Public | Implemented | Service health check |
| `POST` | `/api/auth/register` | Public | Implemented | Register new employee |
| `POST` | `/api/auth/login` | Public | Implemented | Authenticate and obtain JWT token |
| `POST` | `/api/auth/logout` | Optional Session | Implemented | Sign out session |
| `GET` | `/api/auth/me` | JWT | Implemented | Get current user profile |
| `PUT` | `/api/auth/me` | JWT | Implemented | Update profile names or password |
| `GET` | `/api/tickets` | JWT | Implemented | List tickets with filters (`status`, `priority`, `category`, `search`) |
| `POST` | `/api/tickets` | JWT | Implemented | Create ticket with intelligent priority engine |
| `GET` | `/api/tickets/<id>` | JWT | Implemented | Get ticket detail, comments, and audit history |
| `POST` | `/api/tickets/<id>/comments` | JWT | Implemented | Post a comment to ticket |
| `PUT` | `/api/tickets/<id>/status` | JWT | Implemented | Update ticket status (`Open`, `Assigned`, `In Progress`, `Pending`, `Resolved`, `Closed`) |
| `PUT` | `/api/tickets/<id>/priority` | JWT (Admin) | Implemented | Override priority with required justification reason |
| `POST` | `/api/tickets/preview-priority` | JWT | Implemented | Preview rule-based priority engine calculation & justification |
| `GET` | `/api/technicians` | JWT | Planned | List technicians and availability |
| `POST` | `/api/technicians/assign` | JWT (Admin) | Planned | Assign technician to ticket |
| `GET` | `/api/sla/rules` | JWT | Planned | Manage SLA thresholds |
| `GET` | `/api/analytics/dashboard` | JWT | Planned | Analytics aggregation |

---

## Authentication Endpoints

### `POST /api/auth/register`
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "secretpassword",
    "first_name": "Jane",
    "last_name": "Doe",
    "department_id": 1
  }
  ```
- **Response `201 Created`:**
  ```json
  {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "Jane",
      "last_name": "Doe",
      "full_name": "Jane Doe",
      "role": "employee"
    },
    "access_token": "<jwt-token>"
  }
  ```

### `POST /api/auth/login`
- **Request Body:**
  ```json
  {
    "email": "user@example.com",
    "password": "secretpassword"
  }
  ```
- **Response `200 OK`:** Returns user details and `access_token`.

---

## Ticket Endpoints

### `GET /api/tickets`
- **Headers:** `Authorization: Bearer <access_token>`
- **Query Parameters:**
  - `status` (e.g. `Open`, `In Progress`, `Resolved`)
  - `priority` (e.g. `Critical`, `High`, `Medium`, `Low`)
  - `category` (e.g. `Network`, `Database`, `Hardware`, `Software`, `Security`)
  - `search` (searches title, ticket number, and description)
- **Role Isolation:**
  - Employees only receive tickets they requested.
  - Technicians receive assigned tickets and open queue tickets.
  - Admins receive all tickets across the organization.

### `POST /api/tickets`
- **Headers:** `Authorization: Bearer <access_token>`
- **Request Body:**
  ```json
  {
    "title": "ERP Database query timeout during month end",
    "description": "Database query times out after 30 seconds when fetching payroll records.",
    "category": "Database",
    "business_impact": "high",
    "urgency": "high",
    "affected_users_count": 25
  }
  ```
- **Response `201 Created`:** Returns created ticket object with sequential `ticket_number` (`INC-2026-00001`), `recommended_priority`, `final_priority`, `sla_deadline`, and audit history.

### `POST /api/tickets/preview-priority`
- **Request Body:** `{ "category": "Security", "business_impact": "critical", "urgency": "high", "affected_users_count": 50 }`
- **Response `200 OK`:**
  ```json
  {
    "recommended_priority": "Critical",
    "total_score": 82,
    "reasons": [
      "Business impact is 'critical' (+40 pts)",
      "Urgency is 'high' (+22 pts)",
      "Affects widespread users (50 users: +20 pts)",
      "Category 'Security' carries an operational risk modifier (+10 pts)",
      "Total calculated score: 82 points -> Priority: Critical"
    ],
    "justification": "Business impact is 'critical' (+40 pts) | Urgency is 'high' (+22 pts) | ..."
  }
  ```

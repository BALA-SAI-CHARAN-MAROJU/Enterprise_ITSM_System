# REST API Documentation

Base URL: `/api`

### Standard Error Envelope
All error responses return a standardized JSON format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Ticket title is required"
  }
}
```

Standard error codes:
- `validation_error` (422)
- `bad_request` (400)
- `unauthorized` (401)
- `forbidden` (403)
- `not_found` (404)
- `conflict` (409)
- `internal_error` (500)

---

## Complete Endpoint Catalog

| Method | Path | Auth | Roles | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Public | All | System health check |
| `POST` | `/api/auth/register` | Public | All | Register new employee |
| `POST` | `/api/auth/login` | Public | All | Authenticate and obtain JWT access token |
| `POST` | `/api/auth/logout` | Optional | All | Sign out session |
| `GET` | `/api/auth/me` | JWT | All | Get current user profile |
| `PUT` | `/api/auth/me` | JWT | All | Update profile names or password |
| `GET` | `/api/tickets` | JWT | All | List tickets with filters (`status`, `priority`, `category`, `search`) |
| `POST` | `/api/tickets` | JWT | All | Create ticket with intelligent priority engine |
| `GET` | `/api/tickets/<id>` | JWT | All | Get ticket detail, comments, and audit history |
| `POST` | `/api/tickets/<id>/comments` | JWT | All | Post a comment to ticket thread |
| `PUT` | `/api/tickets/<id>/status` | JWT | All | Update ticket status (`Open`, `Assigned`, `In Progress`, `Pending`, `Resolved`, `Closed`) |
| `PUT` | `/api/tickets/<id>/priority` | JWT | Admin | Override priority with required justification reason |
| `POST` | `/api/tickets/preview-priority` | JWT | All | Preview rule-based priority engine calculation & justification |
| `GET` | `/api/technicians` | JWT | All | List all technicians with availability and active workload count |
| `GET` | `/api/technicians/recommendations` | JWT | All | Get recommended technician & candidate rankings for a ticket |
| `POST` | `/api/technicians/assign` | JWT | Admin | Assign or override technician for a ticket |
| `PUT` | `/api/technicians/<id>/availability`| JWT | Tech / Admin | Update availability (`available`, `busy`, `unavailable`) |
| `GET` | `/api/sla/rules` | JWT | All | List configured SLA priority resolution deadlines |
| `PUT` | `/api/sla/rules/<priority>` | JWT | Admin | Update SLA resolution hours or warning threshold |
| `POST` | `/api/sla/scan` | JWT | Admin | Trigger manual SLA scan across all active tickets |
| `GET` | `/api/sla/escalations` | JWT | All | List SLA escalations (`warning`, `breach`) |
| `GET` | `/api/notifications` | JWT | All | Get current user's in-app notifications |
| `PUT` | `/api/notifications/<id>/read` | JWT | All | Mark single notification as read |
| `PUT` | `/api/notifications/read-all` | JWT | All | Mark all notifications as read |
| `GET` | `/api/analytics/dashboard` | JWT | Admin | Aggregated KPIs and Chart.js series |
| `GET` | `/api/analytics/technicians` | JWT | Admin | Technician performance metrics and SLA compliance |
| `GET` | `/api/analytics/incidents` | JWT | Admin | Incident analysis & recurring failure patterns |

---

## Key Request & Response Examples

### 1. Create Ticket (`POST /api/tickets`)
- **Headers:** `Authorization: Bearer <access_token>`
- **Request Body:**
  ```json
  {
    "title": "ERP Database connection failure",
    "description": "Database query times out when fetching employee payroll records.",
    "category": "Database",
    "business_impact": "high",
    "urgency": "high",
    "affected_users_count": 30
  }
  ```
- **Response `201 Created`:**
  ```json
  {
    "ticket": {
      "id": 1,
      "ticket_number": "INC-2026-00001",
      "title": "ERP Database connection failure",
      "category": "Database",
      "recommended_priority": "High",
      "final_priority": "High",
      "status": "Open",
      "sla_deadline": "2026-11-03T05:48:26+00:00",
      "sla_breached": false
    }
  }
  ```

### 2. Technician Recommendation (`GET /api/technicians/recommendations?ticket_id=1`)
- **Response `200 OK`:**
  ```json
  {
    "recommendation": {
      "recommended_technician_id": 2,
      "recommended_technician_name": "Alice Tech",
      "justification": "Recommended Alice Tech (90 pts) with matching expertise and lowest active workload (1/10 tickets).",
      "candidates": [
        {
          "technician_id": 2,
          "technician_name": "Alice Tech",
          "availability_status": "available",
          "has_matching_skill": true,
          "active_tickets_count": 1,
          "total_score": 90.0,
          "reasons": [
            "Status is 'available'",
            "Active workload: 1/10 tickets (10% capacity)",
            "Has verified expertise in 'Database' (+50 pts)",
            "Calculated match score: 90.0/100"
          ]
        }
      ]
    }
  }
  ```

### 3. Admin Analytics Dashboard (`GET /api/analytics/dashboard`)
- **Response `200 OK`:**
  ```json
  {
    "kpis": {
      "total_tickets": 25,
      "open_tickets": 8,
      "resolved_tickets": 17,
      "critical_active": 2,
      "sla_breaches": 1,
      "sla_compliance_rate": 94.1
    },
    "charts": {
      "categories": { "labels": ["Network", "Database", "Software", ...], "data": [8, 6, 5, ...] },
      "priorities": { "labels": ["Critical", "High", "Medium", "Low"], "data": [3, 7, 10, 5] },
      "trends": { "labels": ["Oct 27", "Oct 28", ...], "created": [2, 4, 3, ...], "resolved": [1, 3, 4, ...] }
    }
  }
  ```

# REST API

Base URL: `/api`

Error envelope:

```json
{ "error": { "code": "validation_error", "message": "Password must be at least 8 characters" } }
```

| Method | Path | Auth | Status |
| ------ | ---- | ---- | ------ |
| GET | `/health` | public | Implemented |
| POST | `/api/auth/register` | public (employee only) | Implemented |
| POST | `/api/auth/login` | public | Implemented |
| POST | `/api/auth/logout` | optional session | Implemented |
| GET | `/api/auth/me` | JWT | Implemented |
| PUT | `/api/auth/me` | JWT | Implemented |
| GET/POST | `/api/tickets` | | Not implemented |
| GET | `/api/technicians` | | Not implemented |
| GET | `/api/analytics/dashboard` | | Not implemented |
| GET | `/api/sla/rules` | | Not implemented |

## Authentication

### POST `/api/auth/register`

Body: `{ "email", "password", "first_name", "last_name", "department_id?" }`

Role is always `employee`. Returns `201` with `user` and `access_token`.

### POST `/api/auth/login`

Body: `{ "email", "password" }`. Returns `200` with `user` and `access_token`.

Send `Authorization: Bearer <access_token>` on subsequent API calls.

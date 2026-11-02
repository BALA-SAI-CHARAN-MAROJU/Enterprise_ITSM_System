from functools import wraps

from flask import abort
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from flask_login import current_user

from app.constants import Role
from app.utils.errors import api_error


def roles_required(*roles):
    """Protect HTML views. Unauthenticated users hit Flask-Login; others get 403."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            if not current_user.is_active:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def jwt_roles_required(*roles):
    """Protect JSON API routes. Returns the project error envelope."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get("role")
            if claims.get("is_active") is False:
                return api_error("Account is disabled", 403, "forbidden")
            if roles and role not in roles:
                return api_error("You do not have permission to perform this action", 403, "forbidden")
            return view(*args, **kwargs)

        return wrapped

    return decorator


admin_required = roles_required(Role.ADMIN)
staff_required = roles_required(Role.ADMIN, Role.TECHNICIAN)

"""REST API routes for Administrative Management of Corporate Roles and Employee Assignments."""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.auth.decorators import jwt_roles_required
from app.constants import Role
from app.extensions import csrf
from app.services.user_service import (
    UserServiceError,
    get_user_by_id,
    list_all_users,
    update_employee_role_and_assignment,
)
from app.utils.errors import api_error

api_users_bp = Blueprint("api_users", __name__, url_prefix="/users")
csrf.exempt(api_users_bp)


@api_users_bp.get("")
@jwt_required()
@jwt_roles_required(Role.ADMIN)
def api_list_users():
    """Admin endpoint to list all corporate employees, departments, and roles."""
    users = list_all_users()
    data = []
    for u in users:
        d = u.to_public_dict()
        if u.technician_profile:
            d["technician"] = u.technician_profile.to_dict(include_skills=True)
        data.append(d)
    return {"users": data, "count": len(data)}, 200


@api_users_bp.get("/<int:user_id>")
@jwt_required()
@jwt_roles_required(Role.ADMIN)
def api_get_user(user_id: int):
    """Admin endpoint to get single corporate employee details."""
    u = get_user_by_id(user_id)
    if not u:
        return api_error("User not found", 404, "not_found")
    d = u.to_public_dict()
    if u.technician_profile:
        d["technician"] = u.technician_profile.to_dict(include_skills=True)
    return {"user": d}, 200


@api_users_bp.put("/<int:user_id>")
@jwt_required()
@jwt_roles_required(Role.ADMIN)
def api_update_user_role(user_id: int):
    """Admin endpoint to assign/update an employee's designated corporate role."""
    payload = request.get_json(silent=True) or {}
    try:
        user = update_employee_role_and_assignment(
            user_id=user_id,
            role=payload.get("role", Role.EMPLOYEE),
            department_id=payload.get("department_id"),
            job_title=payload.get("job_title"),
            is_vip=payload.get("is_vip", False),
            is_active=payload.get("is_active", True),
            first_name=payload.get("first_name"),
            last_name=payload.get("last_name"),
            tier=payload.get("tier", 1),
            specialization=payload.get("specialization"),
            skills=payload.get("skills"),
        )
        d = user.to_public_dict()
        if user.technician_profile:
            d["technician"] = user.technician_profile.to_dict(include_skills=True)
        return {"user": d, "message": f"Successfully updated designated role for {user.full_name}"}, 200
    except UserServiceError as exc:
        return api_error(exc.message, exc.status_code, exc.code)

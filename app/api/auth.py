from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from flask_login import login_user, logout_user

from app.extensions import csrf, db
from app.models import User
from app.services.auth_service import AuthError, authenticate, register_employee, update_profile
from app.utils.errors import api_error

api_auth_bp = Blueprint("api_auth", __name__)
csrf.exempt(api_auth_bp)


def _token_for(user: User) -> str:
    return create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "is_active": user.is_active},
    )


@api_auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    try:
        user = register_employee(
            email=payload.get("email"),
            password=payload.get("password"),
            first_name=payload.get("first_name"),
            last_name=payload.get("last_name"),
            department_id=payload.get("department_id"),
        )
    except AuthError as exc:
        return api_error(exc.message, exc.status_code, exc.code)
    return {"user": user.to_public_dict(), "access_token": _token_for(user)}, 201


@api_auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    try:
        user = authenticate(payload.get("email"), payload.get("password"))
    except AuthError as exc:
        return api_error(exc.message, exc.status_code, exc.code)
    login_user(user)
    return {"user": user.to_public_dict(), "access_token": _token_for(user)}, 200


@api_auth_bp.post("/logout")
def logout():
    logout_user()
    return {"message": "Logged out"}, 200


@api_auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return api_error("User not found", 404)
    return {"user": user.to_public_dict()}, 200


@api_auth_bp.put("/me")
@jwt_required()
def update_me():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return api_error("User not found", 404)
    payload = request.get_json(silent=True) or {}
    try:
        user = update_profile(
            user,
            first_name=payload.get("first_name"),
            last_name=payload.get("last_name"),
            password=payload.get("password"),
        )
    except AuthError as exc:
        return api_error(exc.message, exc.status_code, exc.code)
    return {"user": user.to_public_dict()}, 200

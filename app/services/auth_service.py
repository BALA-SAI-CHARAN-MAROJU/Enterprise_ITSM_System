from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select

from app.constants import Role
from app.extensions import db
from app.models import User


class AuthError(Exception):
    def __init__(self, message, status_code=400, code="bad_request"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def normalize_email(raw_email: str) -> str:
    if not raw_email or not str(raw_email).strip():
        raise AuthError("Email is required", 422, "validation_error")
    try:
        result = validate_email(str(raw_email).strip(), check_deliverability=False)
    except EmailNotValidError as exc:
        raise AuthError(str(exc), 422, "validation_error") from exc
    return result.normalized


def register_employee(email, password, first_name, last_name, department_id=None) -> User:
    email = normalize_email(email)
    _validate_profile_fields(first_name, last_name, password, require_password=True)
    if db.session.scalar(select(User).where(User.email == email)):
        raise AuthError("An account with this email already exists", 409, "conflict")

    user = User(
        email=email,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        role=Role.EMPLOYEE,
        department_id=department_id,
        is_active=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate(email, password) -> User:
    if not email or not password:
        raise AuthError("Email and password are required", 422, "validation_error")
    try:
        email = normalize_email(email)
    except AuthError:
        raise AuthError("Invalid email or password", 401, "unauthorized") from None

    user = db.session.scalar(select(User).where(User.email == email))
    if user is None or not user.check_password(password):
        raise AuthError("Invalid email or password", 401, "unauthorized")
    if not user.is_active:
        raise AuthError("Account is disabled", 403, "forbidden")
    return user


def update_profile(user: User, first_name=None, last_name=None, password=None) -> User:
    if first_name is not None:
        if not str(first_name).strip():
            raise AuthError("First name is required", 422, "validation_error")
        user.first_name = first_name.strip()
    if last_name is not None:
        if not str(last_name).strip():
            raise AuthError("Last name is required", 422, "validation_error")
        user.last_name = last_name.strip()
    if password:
        _validate_profile_fields(user.first_name, user.last_name, password, require_password=True)
        user.set_password(password)
    db.session.commit()
    return user


def _validate_profile_fields(first_name, last_name, password, require_password=False):
    if not first_name or not str(first_name).strip():
        raise AuthError("First name is required", 422, "validation_error")
    if not last_name or not str(last_name).strip():
        raise AuthError("Last name is required", 422, "validation_error")
    if require_password:
        if not password or len(password) < 8:
            raise AuthError("Password must be at least 8 characters", 422, "validation_error")

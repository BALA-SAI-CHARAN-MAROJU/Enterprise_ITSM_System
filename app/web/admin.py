"""Web views for Administrator Management of Corporate Roles and Employee Assignments."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.auth.decorators import admin_required
from app.constants import Role
from app.services.user_service import (
    UserServiceError,
    get_user_by_id,
    list_all_users,
    list_departments,
    update_employee_role_and_assignment,
)
from app.web.forms import AdminUserEditForm

web_admin_bp = Blueprint("web_admin", __name__, url_prefix="/admin")


@web_admin_bp.route("/users")
@login_required
@admin_required
def list_users():
    """Admin directory listing all corporate employees, departments, and assigned roles."""
    users = list_all_users()
    departments = list_departments()
    return render_template(
        "admin/users_list.html",
        users=users,
        departments=departments,
    )


@web_admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id: int):
    """Admin view to designate an employee's department, job title, VIP flag, and technician tier."""
    user = get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("web_admin.list_users"))

    departments = list_departments()
    dept_choices = [(d.id, d.name) for d in departments]

    form = AdminUserEditForm(obj=user)
    form.department_id.choices = [(0, "-- Select Department --")] + dept_choices

    # Populate technician fields on GET
    if request.method == "GET" and user.technician_profile:
        tech = user.technician_profile
        form.technician_tier.data = tech.tier
        form.technician_specialization.data = tech.specialization
        form.technician_skills.data = [s.category for s in tech.skills]
    elif request.method == "GET":
        form.technician_tier.data = 1
        form.technician_specialization.data = "General IT Support"
        form.technician_skills.data = []

    if request.method == "GET" and user.department_id:
        form.department_id.data = user.department_id

    if form.validate_on_submit():
        dept_id = form.department_id.data if form.department_id.data != 0 else None
        try:
            update_employee_role_and_assignment(
                user_id=user.id,
                role=form.role.data,
                department_id=dept_id,
                job_title=form.job_title.data,
                is_vip=form.is_vip.data,
                is_active=form.is_active.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                tier=form.technician_tier.data or 1,
                specialization=form.technician_specialization.data,
                skills=form.technician_skills.data if form.role.data == Role.TECHNICIAN else [],
            )
            flash(f"Successfully updated designated role and assignments for {user.full_name}.", "success")
            return redirect(url_for("web_admin.list_users"))
        except UserServiceError as exc:
            flash(exc.message, "danger")

    return render_template(
        "admin/user_edit.html",
        form=form,
        target_user=user,
        departments=departments,
    )

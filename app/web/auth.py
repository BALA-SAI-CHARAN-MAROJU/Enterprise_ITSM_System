from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.services.auth_service import AuthError, authenticate, register_employee, update_profile
from app.web.forms import LoginForm, ProfileForm, RegisterForm

web_auth_bp = Blueprint("web_auth", __name__)


@web_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web_dashboards.home"))
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = authenticate(form.email.data, form.password.data)
        except AuthError as exc:
            flash(exc.message, "danger")
        else:
            login_user(user)
            next_url = request.args.get("next")
            return redirect(next_url or url_for("web_dashboards.home"))
    return render_template("auth/login.html", form=form)


@web_auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("web_dashboards.home"))
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = register_employee(
                email=form.email.data,
                password=form.password.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
            )
        except AuthError as exc:
            flash(exc.message, "danger")
        else:
            login_user(user)
            flash("Account created. Welcome to the ITSM portal.", "success")
            return redirect(url_for("web_dashboards.home"))
    return render_template("auth/register.html", form=form)


@web_auth_bp.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("web_auth.login"))


@web_auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        try:
            update_profile(
                current_user,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                password=form.password.data or None,
            )
        except AuthError as exc:
            flash(exc.message, "danger")
        else:
            flash("Profile updated.", "success")
            return redirect(url_for("web_auth.profile"))
    return render_template("auth/profile.html", form=form)

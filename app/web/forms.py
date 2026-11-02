from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange

from app.constants import ImpactLevel, Priority, Role, TicketCategory, TicketStatus, UrgencyLevel


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class RegisterForm(FlaskForm):
    first_name = StringField("First name", validators=[DataRequired(), Length(max=80)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")],
    )
    submit = SubmitField("Create account")


class ProfileForm(FlaskForm):
    first_name = StringField("First name", validators=[DataRequired(), Length(max=80)])
    last_name = StringField("Last name", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("New password (optional)", validators=[Length(max=128)])
    submit = SubmitField("Save changes")


class TicketForm(FlaskForm):
    title = StringField("Issue Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Detailed Description", validators=[DataRequired(), Length(min=10)])
    category = SelectField(
        "Issue Category",
        choices=[(c, c) for c in TicketCategory.ALL],
        validators=[DataRequired()],
    )
    business_impact = SelectField(
        "Business Impact",
        choices=[
            (ImpactLevel.LOW, "Low - Minor inconvenience, normal operations continue"),
            (ImpactLevel.MEDIUM, "Medium - Partial slowdown or single department affected"),
            (ImpactLevel.HIGH, "High - Serious impairment of critical business work"),
            (ImpactLevel.CRITICAL, "Critical - Total organization or mission-critical outage"),
        ],
        validators=[DataRequired()],
    )
    urgency = SelectField(
        "Urgency",
        choices=[
            (UrgencyLevel.LOW, "Low - Can wait several business days"),
            (UrgencyLevel.MEDIUM, "Medium - Needs attention within 24 hours"),
            (UrgencyLevel.HIGH, "High - Needs attention within a few hours"),
            (UrgencyLevel.CRITICAL, "Critical - Requires immediate emergency intervention"),
        ],
        validators=[DataRequired()],
    )
    affected_users_count = IntegerField(
        "Number of Affected Users",
        default=1,
        validators=[DataRequired(), NumberRange(min=1, max=100000)],
    )
    submit = SubmitField("Submit Ticket")


class TicketCommentForm(FlaskForm):
    body = TextAreaField("Add a comment or update", validators=[DataRequired(), Length(min=2)])
    submit = SubmitField("Post Comment")


class TicketStatusForm(FlaskForm):
    status = SelectField("Update Status", validators=[DataRequired()])
    note = StringField("Status Change Note (optional)")
    submit = SubmitField("Update Status")


class TechnicianAssignForm(FlaskForm):
    technician_id = SelectField("Select Technician", coerce=int, validators=[DataRequired()])
    override_reason = StringField("Override Justification (if overriding recommendation)")
    submit = SubmitField("Confirm Assignment")


class AdminUserEditForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=80)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=80)])
    role = SelectField(
        "System Role",
        choices=[(Role.EMPLOYEE, "Employee"), (Role.TECHNICIAN, "Technician"), (Role.ADMIN, "Administrator")],
        validators=[DataRequired()],
    )
    department_id = SelectField("Corporate Department", coerce=int)
    job_title = StringField("Designated Job Title", validators=[Length(max=100)])
    is_vip = BooleanField("VIP Executive Status (Priority Escalation)")
    is_active = BooleanField("Account Active Status", default=True)
    # Technician-specific configuration
    technician_tier = SelectField(
        "Technician Tier Level",
        choices=[
            (1, "Tier 1 - General Helpdesk & App Support"),
            (2, "Tier 2 - Systems & Infrastructure Specialist"),
            (3, "Tier 3 - Senior Architecture & Incident Commander"),
        ],
        coerce=int,
        default=1,
    )
    technician_specialization = StringField("Specialization Focus", validators=[Length(max=100)])
    technician_skills = SelectMultipleField(
        "Certified Problem Categories",
        choices=[(c, c) for c in TicketCategory.ALL],
    )
    submit = SubmitField("Save Role & Assignments")

"""Web views for Ticket Management."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.constants import Priority, Role, TicketCategory, TicketStatus
from app.services.ticket_service import (
    TicketError,
    add_ticket_comment,
    create_ticket,
    get_ticket_for_user,
    list_tickets_for_user,
    update_ticket_status,
)
from app.web.forms import TicketCommentForm, TicketForm, TicketStatusForm

web_tickets_bp = Blueprint("web_tickets", __name__, url_prefix="/tickets")


@web_tickets_bp.route("", methods=["GET"])
@login_required
def list_tickets():
    status = request.args.get("status")
    priority = request.args.get("priority")
    category = request.args.get("category")
    search = request.args.get("search")

    tickets = list_tickets_for_user(
        user=current_user,
        status=status,
        priority=priority,
        category=category,
        search=search,
    )
    return render_template(
        "tickets/list.html",
        tickets=tickets,
        selected_status=status,
        selected_priority=priority,
        selected_category=category,
        search_query=search or "",
        all_statuses=TicketStatus.ALL,
        all_priorities=Priority.ALL,
        all_categories=TicketCategory.ALL,
    )


@web_tickets_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = TicketForm()
    if form.validate_on_submit():
        try:
            ticket = create_ticket(
                requester=current_user,
                title=form.title.data,
                description=form.description.data,
                category=form.category.data,
                business_impact=form.business_impact.data,
                urgency=form.urgency.data,
                affected_users_count=form.affected_users_count.data,
            )
            flash(
                f"Ticket {ticket.ticket_number} created successfully with recommended priority '{ticket.recommended_priority}'.",
                "success",
            )
            return redirect(url_for("web_tickets.detail", ticket_id=ticket.id))
        except TicketError as exc:
            flash(exc.message, "danger")

    return render_template("tickets/create.html", form=form)


@web_tickets_bp.route("/<int:ticket_id>", methods=["GET"])
@login_required
def detail(ticket_id: int):
    try:
        ticket = get_ticket_for_user(ticket_id, current_user)
    except TicketError as exc:
        flash(exc.message, "danger")
        return redirect(url_for("web_tickets.list_tickets"))

    comment_form = TicketCommentForm()
    status_form = TicketStatusForm()

    # Determine allowed next statuses based on role and current status
    allowed_statuses = []
    if current_user.is_admin():
        allowed_statuses = [s for s in TicketStatus.ALL if s != ticket.status]
    elif current_user.is_technician():
        allowed_statuses = [
            s for s in (TicketStatus.IN_PROGRESS, TicketStatus.PENDING, TicketStatus.RESOLVED)
            if s != ticket.status
        ]
    elif current_user.role == Role.EMPLOYEE:
        if ticket.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
            allowed_statuses = [TicketStatus.OPEN]
        elif ticket.status == TicketStatus.RESOLVED:
            allowed_statuses = [TicketStatus.CLOSED, TicketStatus.OPEN]

    status_form.status.choices = [(s, s) for s in allowed_statuses]

    return render_template(
        "tickets/detail.html",
        ticket=ticket,
        comment_form=comment_form,
        status_form=status_form,
        allowed_statuses=allowed_statuses,
    )


@web_tickets_bp.route("/<int:ticket_id>/comments", methods=["POST"])
@login_required
def post_comment(ticket_id: int):
    form = TicketCommentForm()
    if form.validate_on_submit():
        try:
            ticket = get_ticket_for_user(ticket_id, current_user)
            add_ticket_comment(ticket, current_user, form.body.data)
            flash("Comment posted successfully.", "success")
        except TicketError as exc:
            flash(exc.message, "danger")
    return redirect(url_for("web_tickets.detail", ticket_id=ticket_id))


@web_tickets_bp.route("/<int:ticket_id>/status", methods=["POST"])
@login_required
def change_status(ticket_id: int):
    form = TicketStatusForm()
    form.status.choices = [(s, s) for s in TicketStatus.ALL]
    if form.validate_on_submit():
        try:
            ticket = get_ticket_for_user(ticket_id, current_user)
            update_ticket_status(ticket, form.status.data, current_user, note=form.note.data)
            flash(f"Ticket status changed to '{form.status.data}'.", "success")
        except TicketError as exc:
            flash(exc.message, "danger")
    return redirect(url_for("web_tickets.detail", ticket_id=ticket_id))

# File: fastcars-admin/blueprints/users.py
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from utils.decorators import login_required
from utils.helpers import (
    AuthSessionExpired,
    api_request,
    auth_headers,
    ensure_response,
    normalize_booking_collection,
    normalize_user,
    normalize_user_collection,
    stringify_value,
)

users_bp = Blueprint("users", __name__)


def _load_users() -> tuple[list[dict], str]:
    response = api_request("GET", "/api/admin/users/", headers=auth_headers())
    ensure_response(response)
    users = normalize_user_collection(response.json())
    return [
        item
        for item in users
        if item.get("role") in {"", "user", "customer", "client", "member"}
    ], "Backend API"


def _load_user_detail(user_id: str) -> tuple[dict | None, str]:
    response = api_request("GET", f"/api/admin/users/{user_id}", headers=auth_headers())
    ensure_response(response)
    payload = response.json()
    if isinstance(payload, dict):
        if isinstance(payload.get("user"), dict):
            payload = payload["user"]
        elif isinstance(payload.get("data"), dict):
            payload = payload["data"]
        return normalize_user(payload), "Backend API"
    return None, "Backend API"


def _load_bookings() -> list[dict]:
    response = api_request("GET", "/api/admin/bookings/", headers=auth_headers())
    ensure_response(response)
    return normalize_booking_collection(response.json())


@users_bp.route("/users")
@login_required
def index():
    try:
        users, source = _load_users()
        bookings = _load_bookings()
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except Exception as exc:
        flash(f"Unable to load users: {exc}", "error")
        users, source = [], "Backend API"
        bookings = []

    selected_user_id = request.args.get("user_id") or (users[0]["id"] if users else "")
    selected_user = next((user for user in users if user.get("id") == selected_user_id), None)
    if not selected_user and users:
        selected_user = users[0]
        selected_user_id = selected_user["id"]
    detail = selected_user
    detail_source = source
    if selected_user:
        try:
            detail, detail_source = _load_user_detail(selected_user["id"])
            detail = detail or selected_user
        except AuthSessionExpired:
            session.clear()
            flash("Your admin session expired. Sign in again to continue.", "warning")
            return redirect(url_for("auth.login"))
        except Exception as exc:
            flash(f"Showing summary user details because the live detail request failed: {exc}", "warning")
            detail = selected_user
            detail_source = source

    booking_history = []
    if selected_user:
        selected_user_id = selected_user.get("id", "")
        selected_user_name = selected_user.get("name", "")
        selected_user_email = selected_user.get("email", "")
        booking_history = [
            booking
            for booking in bookings
            if stringify_value(booking.get("user_id")) == selected_user_id
            or booking.get("customer") == selected_user_name
            or booking.get("user_email") == selected_user_email
        ]

    return render_template(
        "users/index.html",
        page_title="User Management",
        page_kicker="Customer directory",
        source=source,
        detail_source=detail_source,
        users=users,
        selected_user=selected_user,
        user_detail=detail,
        booking_history=booking_history,
        total_users=len(users),
        active_users=sum(1 for user in users if user.get("status", "active") == "active"),
        inactive_users=sum(1 for user in users if user.get("status", "active") != "active"),
    )

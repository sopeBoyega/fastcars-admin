# File: fastcars-admin/blueprints/bookings.py
from __future__ import annotations

import requests
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from utils.decorators import login_required
from utils.helpers import (
    AuthSessionExpired,
    api_request,
    auth_headers,
    ensure_response,
    normalize_booking,
    normalize_booking_collection,
)

bookings_bp = Blueprint("bookings", __name__)


def _load_bookings() -> tuple[list[dict], str]:
    response = api_request("GET", "/api/admin/bookings/", headers=auth_headers())
    ensure_response(response)
    return normalize_booking_collection(response.json()), "Backend API"


def _load_booking_detail(booking_id: str) -> tuple[dict | None, str]:
    response = api_request("GET", f"/api/admin/bookings/{booking_id}", headers=auth_headers())
    ensure_response(response)
    payload = response.json()
    if isinstance(payload, dict):
        return normalize_booking(payload), "Backend API"
    return None, "Backend API"


@bookings_bp.route("/bookings")
@login_required
def index():
    try:
        all_bookings, source = _load_bookings()
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except Exception as exc:
        flash(f"Unable to load bookings: {exc}", "error")
        all_bookings, source = [], "Backend API"

    status_filter = request.args.get("status", "All")
    filtered_bookings = (
        all_bookings
        if status_filter == "All"
        else [item for item in all_bookings if item.get("status") == status_filter]
    )

    selected_booking_id = request.args.get("booking_id") or (
        filtered_bookings[0]["id"] if filtered_bookings else ""
    )
    selected_booking = next(
        (item for item in filtered_bookings if item.get("id") == selected_booking_id),
        None,
    )
    booking_detail = selected_booking
    detail_source = source
    if selected_booking:
        try:
            booking_detail, detail_source = _load_booking_detail(selected_booking["id"])
            booking_detail = booking_detail or selected_booking
        except AuthSessionExpired:
            session.clear()
            flash("Your admin session expired. Sign in again to continue.", "warning")
            return redirect(url_for("auth.login"))
        except Exception as exc:
            flash(f"Showing summary booking details because the live detail request failed: {exc}", "warning")
            booking_detail = selected_booking
            detail_source = source

    return render_template(
        "bookings/index.html",
        page_title="Booking Operations",
        page_kicker="Moderation queue",
        source=source,
        detail_source=detail_source,
        all_bookings=all_bookings,
        filtered_bookings=filtered_bookings,
        selected_booking=selected_booking,
        booking_detail=booking_detail,
        confirmed_revenue=sum(
            float(item.get("total_cost") or 0)
            for item in all_bookings
            if item.get("status") == "confirmed"
        ),
        status_filter=status_filter,
    )


@bookings_bp.route("/bookings/<booking_id>/confirm", methods=["POST"])
@login_required
def confirm(booking_id: str):
    try:
        response = api_request(
            "PATCH",
            f"/api/admin/bookings/{booking_id}/confirm",
            headers=auth_headers(),
        )
        ensure_response(response)
        flash(f"{request.form.get('booking_ref', 'Booking')} marked as confirmed.", "success")
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except requests.RequestException as exc:
        flash(f"Unable to reach the backend API: {exc}", "error")
    except Exception as exc:
        flash(f"Unable to confirm booking: {exc}", "error")
    return redirect(
        url_for(
            "bookings.index",
            status=request.form.get("return_status", "All"),
            booking_id=booking_id,
        )
    )


@bookings_bp.route("/bookings/<booking_id>/cancel", methods=["POST"])
@login_required
def cancel(booking_id: str):
    try:
        response = api_request(
            "PATCH",
            f"/api/admin/bookings/{booking_id}/cancel",
            headers=auth_headers(),
        )
        ensure_response(response)
        flash(f"{request.form.get('booking_ref', 'Booking')} marked as cancelled.", "success")
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except requests.RequestException as exc:
        flash(f"Unable to reach the backend API: {exc}", "error")
    except Exception as exc:
        flash(f"Unable to cancel booking: {exc}", "error")
    return redirect(
        url_for(
            "bookings.index",
            status=request.form.get("return_status", "All"),
            booking_id=booking_id,
        )
    )

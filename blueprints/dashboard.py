# File: fastcars-admin/blueprints/dashboard.py
from __future__ import annotations

from collections import Counter
from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, session, url_for

from utils.decorators import login_required
from utils.helpers import (
    AuthSessionExpired,
    api_request,
    auth_headers,
    build_bar_chart_html,
    ensure_response,
    normalize_booking_collection,
    normalize_car_rows,
    parse_dateish,
)

dashboard_bp = Blueprint("dashboard", __name__)


def _empty_summary() -> dict[str, int]:
    return {
        "users": 0,
        "cars": 0,
        "active_cars": 0,
        "bookings": 0,
        "pending_bookings": 0,
        "confirmed_revenue": 0,
        "subscribers": 0,
        "enquiries": 0,
        "unread_enquiries": 0,
        "testimonials": 0,
    }


@dashboard_bp.route("/")
@login_required
def index():
    source = "Backend API"
    summary = _empty_summary()
    bookings: list[dict] = []
    cars: list[dict] = []
    brands: list[dict] = []
    enquiries: list[dict] = []

    try:
        summary_response = api_request("GET", "/api/admin/dashboard", headers=auth_headers())
        ensure_response(summary_response)
        summary_payload = summary_response.json()
        payload = summary_payload if isinstance(summary_payload, dict) else {}
        summary = {
            "users": payload.get("users", 0),
            "cars": payload.get("cars", payload.get("active_cars", 0)),
            "active_cars": payload.get("active_cars", payload.get("cars", 0)),
            "bookings": payload.get("bookings", payload.get("total_bookings", 0)),
            "pending_bookings": payload.get("pending_bookings", 0),
            "confirmed_revenue": payload.get("confirmed_revenue", payload.get("revenue", 0)),
            "subscribers": payload.get("subscribers", 0),
            "enquiries": payload.get("enquiries", payload.get("queries", 0)),
            "unread_enquiries": payload.get("unread_enquiries", 0),
            "testimonials": payload.get("testimonials", 0),
        }

        brands_response = api_request("GET", "/api/admin/cars/brands", headers=auth_headers())
        ensure_response(brands_response)
        brands_payload = brands_response.json()
        if isinstance(brands_payload, list):
            brands = brands_payload

        bookings_response = api_request("GET", "/api/admin/bookings/", headers=auth_headers())
        ensure_response(bookings_response)
        bookings = normalize_booking_collection(bookings_response.json())
        summary["bookings"] = summary["bookings"] or len(bookings)
        summary["confirmed_revenue"] = summary["confirmed_revenue"] or sum(
            float(item.get("total_cost") or 0)
            for item in bookings
            if item.get("status") == "confirmed"
        )

        cars_response = api_request("GET", "/api/admin/cars/", headers=auth_headers())
        ensure_response(cars_response)
        cars_payload = cars_response.json()
        cars = normalize_car_rows(cars_payload if isinstance(cars_payload, list) else [], brands)
        summary["cars"] = summary["cars"] or len(cars)
        summary["active_cars"] = sum(1 for car in cars if car.get("status") == "active")

        enquiries_response = api_request("GET", "/api/admin/enquiries", headers=auth_headers())
        ensure_response(enquiries_response)
        enquiries_payload = enquiries_response.json()
        enquiries = enquiries_payload if isinstance(enquiries_payload, list) else []
        summary["enquiries"] = summary["enquiries"] or len(enquiries)
        summary["unread_enquiries"] = summary["unread_enquiries"] or sum(
            1 for item in enquiries if item.get("status", "unread") == "unread"
        )
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except Exception as exc:
        flash(f"Unable to load dashboard data: {exc}", "error")

    def _sort_key(item: dict) -> datetime:
        candidate = parse_dateish(item.get("created_at")) or parse_dateish(item.get("start_date"))
        if isinstance(candidate, datetime):
            return candidate
        if isinstance(candidate, date):
            return datetime.combine(candidate, datetime.min.time())
        return datetime.min

    booking_counter = Counter(item.get("status", "unknown").title() for item in bookings)
    fleet_counter = Counter(item.get("brand_name") or item.get("brand") or "Unknown" for item in cars)

    booking_chart = build_bar_chart_html(
        [{"status": status, "count": count} for status, count in booking_counter.items()],
        "status",
        "count",
        "Booking status",
        "#2563eb",
    )
    fleet_chart = build_bar_chart_html(
        [{"brand": brand, "vehicles": count} for brand, count in fleet_counter.items()],
        "brand",
        "vehicles",
        "Fleet by brand",
        "#0f172a",
    )

    recent_bookings = sorted(
        bookings,
        key=_sort_key,
        reverse=True,
    )[:5]

    return render_template(
        "dashboard/index.html",
        page_title="Operations Dashboard",
        page_kicker="Overview",
        source=source,
        summary=summary,
        recent_bookings=recent_bookings,
        booking_chart=booking_chart,
        fleet_chart=fleet_chart,
    )

# File: fastcars-admin/blueprints/testimonials.py
from __future__ import annotations

import requests
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from utils.decorators import login_required
from utils.helpers import AuthSessionExpired, api_request, auth_headers, ensure_response, item_identifier

testimonials_bp = Blueprint("testimonials", __name__)


def _load_testimonials() -> tuple[list[dict], str]:
    response = api_request("GET", "/api/admin/testimonials/", headers=auth_headers())
    ensure_response(response)
    payload = response.json()
    if isinstance(payload, list):
        testimonials = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            normalized = dict(item)
            normalized["id"] = item_identifier(item)
            normalized["_id"] = normalized["id"]
            normalized["user_name"] = item.get("user_name") or item.get("name") or "Customer"
            normalized["message"] = item.get("message") or ""
            normalized["rating"] = item.get("rating") or item.get("stars") or 5
            normalized["is_active"] = bool(item.get("is_active", item.get("active", False)))
            testimonials.append(normalized)
        return testimonials, "Backend API"
    return [], "Backend API"


@testimonials_bp.route("/testimonials")
@login_required
def index():
    try:
        testimonials, source = _load_testimonials()
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except Exception as exc:
        flash(f"Unable to load testimonials: {exc}", "error")
        testimonials, source = [], "Backend API"

    selected_testimonial_id = request.args.get("testimonial_id") or (
        str(testimonials[0].get("id") or testimonials[0].get("_id")) if testimonials else ""
    )
    selected_testimonial = next(
        (
            item
            for item in testimonials
            if str(item.get("id") or item.get("_id")) == selected_testimonial_id
        ),
        None,
    )

    return render_template(
        "testimonials/index.html",
        page_title="Testimonial Moderation",
        page_kicker="Reviews queue",
        source=source,
        testimonials=testimonials,
        selected_testimonial=selected_testimonial,
    )


@testimonials_bp.route("/testimonials/<testimonial_id>/status", methods=["POST"])
@login_required
def update_status(testimonial_id: str):
    desired_state = request.form.get("is_active", "false").lower() == "true"
    try:
        response = api_request(
            "PATCH",
            f"/api/admin/testimonials/{testimonial_id}",
            headers=auth_headers(),
            json={"is_active": desired_state},
        )
        ensure_response(response)
        flash(
            "Testimonial is now active." if desired_state else "Testimonial kept inactive.",
            "success",
        )
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except requests.RequestException as exc:
        flash(f"Unable to reach the backend API: {exc}", "error")
    except Exception as exc:
        flash(f"Unable to update testimonial: {exc}", "error")
    return redirect(url_for("testimonials.index", testimonial_id=testimonial_id))

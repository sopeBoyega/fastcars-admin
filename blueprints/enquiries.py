# File: fastcars-admin/blueprints/enquiries.py
from __future__ import annotations

import requests
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from utils.decorators import login_required
from utils.helpers import AuthSessionExpired, api_request, auth_headers, ensure_response

enquiries_bp = Blueprint("enquiries", __name__)


def _load_enquiries() -> tuple[list[dict], str]:
    response = api_request("GET", "/api/admin/enquiries", headers=auth_headers())
    ensure_response(response)
    payload = response.json()
    if isinstance(payload, list):
        return payload, "Backend API"
    return [], "Backend API"


@enquiries_bp.route("/enquiries")
@login_required
def index():
    try:
        all_enquiries, source = _load_enquiries()
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except Exception as exc:
        flash(f"Unable to load enquiries: {exc}", "error")
        all_enquiries, source = [], "Backend API"

    view_filter = request.args.get("view", "all")
    enquiries = list(all_enquiries)
    if view_filter != "all":
        enquiries = [item for item in enquiries if item.get("status", "unread") == view_filter]

    selected_enquiry_id = request.args.get("enquiry_id") or (
        str(enquiries[0].get("id") or enquiries[0].get("_id")) if enquiries else ""
    )
    selected_enquiry = next(
        (
            item
            for item in enquiries
            if str(item.get("id") or item.get("_id")) == selected_enquiry_id
        ),
        None,
    )

    return render_template(
        "enquiries/index.html",
        page_title="Customer Enquiries",
        page_kicker="Inbox",
        source=source,
        view_filter=view_filter,
        all_enquiries=all_enquiries,
        enquiries=enquiries,
        selected_enquiry=selected_enquiry,
    )


@enquiries_bp.route("/enquiries/<enquiry_id>/read", methods=["POST"])
@login_required
def mark_read(enquiry_id: str):
    view_filter = request.form.get("return_view", "all")
    try:
        response = api_request(
            "PATCH",
            f"/api/admin/enquiries/{enquiry_id}",
            headers=auth_headers(),
            json={"status": "read"},
        )
        ensure_response(response)
        flash("Enquiry marked as read.", "success")
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except requests.RequestException as exc:
        flash(f"Unable to reach the backend API: {exc}", "error")
    except Exception as exc:
        flash(f"Unable to update enquiry: {exc}", "error")
    return redirect(url_for("enquiries.index", view=view_filter, enquiry_id=enquiry_id))


@enquiries_bp.route("/enquiries/<enquiry_id>/delete", methods=["POST"])
@login_required
def delete(enquiry_id: str):
    view_filter = request.form.get("return_view", "all")
    try:
        response = api_request(
            "DELETE",
            f"/api/admin/enquiries/{enquiry_id}",
            headers=auth_headers(),
        )
        ensure_response(response)
        flash("Enquiry deleted.", "success")
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except requests.RequestException as exc:
        flash(f"Unable to reach the backend API: {exc}", "error")
    except Exception as exc:
        flash(f"Unable to delete enquiry: {exc}", "error")
    return redirect(url_for("enquiries.index", view=view_filter))

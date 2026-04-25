# File: fastcars-admin/blueprints/subscribers.py
from __future__ import annotations

import requests
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from utils.decorators import login_required
from utils.helpers import AuthSessionExpired, api_request, auth_headers, ensure_response, item_identifier

subscribers_bp = Blueprint("subscribers", __name__)


def _load_subscribers() -> tuple[list[dict], str]:
    response = api_request("GET", "/api/admin/subscribers", headers=auth_headers())
    ensure_response(response)
    payload = response.json()
    if isinstance(payload, list):
        subscribers = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            normalized = dict(item)
            normalized["id"] = item_identifier(item)
            normalized["_id"] = normalized["id"]
            normalized["segment"] = item.get("segment") or "General"
            subscribers.append(normalized)
        return subscribers, "Backend API"
    return [], "Backend API"


@subscribers_bp.route("/subscribers")
@login_required
def index():
    try:
        subscribers, source = _load_subscribers()
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except Exception as exc:
        flash(f"Unable to load subscribers: {exc}", "error")
        subscribers, source = [], "Backend API"

    segments = ["All"] + sorted({item.get("segment", "General") for item in subscribers})
    segment_filter = request.args.get("segment", "All")
    filtered_subscribers = (
        subscribers
        if segment_filter == "All"
        else [item for item in subscribers if item.get("segment", "General") == segment_filter]
    )

    selected_subscriber_id = request.args.get("subscriber_id") or (
        str(filtered_subscribers[0].get("id") or filtered_subscribers[0].get("_id"))
        if filtered_subscribers
        else ""
    )
    selected_subscriber = next(
        (
            item
            for item in filtered_subscribers
            if str(item.get("id") or item.get("_id")) == selected_subscriber_id
        ),
        None,
    )

    return render_template(
        "subscribers/index.html",
        page_title="Subscriber Management",
        page_kicker="Audience",
        source=source,
        subscribers=subscribers,
        filtered_subscribers=filtered_subscribers,
        selected_subscriber=selected_subscriber,
        segment_filter=segment_filter,
        segments=segments,
    )


@subscribers_bp.route("/subscribers/<subscriber_id>/delete", methods=["POST"])
@login_required
def delete(subscriber_id: str):
    segment_filter = request.form.get("return_segment", "All")
    try:
        response = api_request(
            "DELETE",
            f"/api/admin/subscribers/{subscriber_id}",
            headers=auth_headers(),
        )
        ensure_response(response)
        flash(f"{request.form.get('subscriber_email', 'Subscriber')} removed from the audience.", "success")
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except requests.RequestException as exc:
        flash(f"Unable to reach the backend API: {exc}", "error")
    except Exception as exc:
        flash(f"Unable to remove subscriber: {exc}", "error")
    return redirect(url_for("subscribers.index", segment=segment_filter))

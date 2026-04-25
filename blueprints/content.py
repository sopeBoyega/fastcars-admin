# File: fastcars-admin/blueprints/content.py
from __future__ import annotations

import requests
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from utils.decorators import login_required
from utils.helpers import AuthSessionExpired, api_request, auth_headers, ensure_response, normalize_site_content

content_bp = Blueprint("content", __name__)


CONTACT_CONTENT_FIELDS = [
    {"key": "contact_email", "label": "Contact email", "input_type": "email"},
    {"key": "contact_phone", "label": "Contact phone", "input_type": "text"},
    {"key": "contact_address", "label": "Contact address", "input_type": "text"},
    {"key": "contact_hours", "label": "Support hours", "input_type": "text"},
]


def _load_site_content() -> tuple[list[dict], str]:
    response = api_request("GET", "/api/admin/site-content", headers=auth_headers())
    ensure_response(response)
    return normalize_site_content(response.json()), "Backend API"


@content_bp.route("/content", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        mode = request.form.get("mode", "existing")
        if mode == "contact":
            updated_keys: list[str] = []
            try:
                for field in CONTACT_CONTENT_FIELDS:
                    value = request.form.get(field["key"], "").strip()
                    if not value:
                        continue
                    response = api_request(
                        "PATCH",
                        f"/api/admin/site-content/{field['key']}",
                        headers=auth_headers(),
                        json={"value": value},
                    )
                    ensure_response(response)
                    updated_keys.append(field["label"])

                if not updated_keys:
                    flash("Enter at least one contact detail before saving.", "error")
                else:
                    flash("Contact us details updated successfully.", "success")
                return redirect(url_for("content.index"))
            except AuthSessionExpired:
                session.clear()
                flash("Your admin session expired. Sign in again to continue.", "warning")
                return redirect(url_for("auth.login"))
            except requests.RequestException as exc:
                flash(f"Unable to reach the backend API: {exc}", "error")
                return redirect(url_for("content.index"))
            except Exception as exc:
                flash(f"Unable to save contact details: {exc}", "error")
                return redirect(url_for("content.index"))

        selected_key = (
            request.form.get("selected_key", "").strip()
            if mode == "existing"
            else request.form.get("custom_key", "").strip()
        )
        new_value = request.form.get("value", "")
        if not selected_key:
            flash("A content key is required.", "error")
            return redirect(url_for("content.index"))

        try:
            response = api_request(
                "PATCH",
                f"/api/admin/site-content/{selected_key}",
                headers=auth_headers(),
                json={"value": new_value},
            )
            ensure_response(response)
            payload = response.json() if response.content else {"key": selected_key, "value": new_value}
            flash(f"{payload['key']} updated successfully.", "success")
            return redirect(url_for("content.index", mode=mode, key=selected_key))
        except AuthSessionExpired:
            session.clear()
            flash("Your admin session expired. Sign in again to continue.", "warning")
            return redirect(url_for("auth.login"))
        except requests.RequestException as exc:
            flash(f"Unable to reach the backend API: {exc}", "error")
            return redirect(url_for("content.index", mode=mode, key=selected_key))
        except Exception as exc:
            flash(f"Unable to save content: {exc}", "error")
            return redirect(url_for("content.index", mode=mode, key=selected_key))

    try:
        items, source = _load_site_content()
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except Exception as exc:
        flash(f"Unable to load content: {exc}", "error")
        items, source = [], "Backend API"

    content_map = {item.get("key"): item.get("value", "") for item in items if item.get("key")}
    mode = request.args.get("mode", "existing")
    selected_key = request.args.get("key", "")
    if mode == "existing":
        if not selected_key and content_map:
            selected_key = next(iter(content_map))
    current_value = content_map.get(selected_key, "")

    return render_template(
        "content/index.html",
        page_title="Editable Site Content",
        page_kicker="CMS-lite",
        source=source,
        items=items,
        content_map=content_map,
        contact_fields=CONTACT_CONTENT_FIELDS,
        mode=mode,
        selected_key=selected_key,
        current_value=current_value,
    )

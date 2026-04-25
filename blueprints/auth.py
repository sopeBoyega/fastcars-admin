# File: fastcars-admin/blueprints/auth.py
from __future__ import annotations

import requests
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from utils.decorators import login_required
from utils.helpers import (
    AuthSessionExpired,
    api_enabled,
    api_request,
    auth_headers,
    display_name_from_email,
    ensure_response,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("token"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        next_path = request.form.get("next") or request.args.get("next") or url_for("dashboard.index")

        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("auth.login"))

        if not api_enabled():
            flash("Admin API is not configured. Set API_URL before signing in.", "error")
            return redirect(url_for("auth.login"))

        try:
            login_response = api_request(
                "POST",
                "/api/auth/login",
                json={"email": email, "password": password},
            )
            ensure_response(login_response)
            payload = login_response.json()
            token = payload.get("access_token")
            if not token:
                flash("Login succeeded but the API did not return an access token.", "error")
                return redirect(url_for("auth.login"))

            access_check = api_request(
                "GET",
                "/api/admin/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )
            ensure_response(access_check)

            session.clear()
            session["token"] = token
            session["admin_user"] = {
                "name": display_name_from_email(email),
                "email": email,
                "role": "Admin",
            }
            flash("Signed in successfully.", "success")
            return redirect(next_path)
        except requests.RequestException as exc:
            flash(f"Unable to reach the backend API: {exc}", "error")
        except Exception as exc:
            flash(f"Login failed: {exc}", "error")

    return render_template(
        "auth/login.html",
        page_title="Admin Sign In",
        page_kicker="FAST CARS Admin",
        next_path=request.args.get("next", ""),
    )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_password or not new_password or not confirm_password:
            flash("Current password, new password, and confirmation are required.", "error")
            return redirect(url_for("auth.change_password"))
        if new_password != confirm_password:
            flash("New password and confirmation must match.", "error")
            return redirect(url_for("auth.change_password"))
        if len(new_password) < 8:
            flash("New password must be at least 8 characters long.", "error")
            return redirect(url_for("auth.change_password"))

        try:
            response = api_request(
                "PATCH",
                "/api/users/me/password",
                headers=auth_headers(),
                json={
                    "current_password": current_password,
                    "new_password": new_password,
                },
            )
            ensure_response(response)
            flash("Your admin password was updated successfully.", "success")
            return redirect(url_for("auth.change_password"))
        except AuthSessionExpired:
            session.clear()
            flash("Your admin session expired. Sign in again to continue.", "warning")
            return redirect(url_for("auth.login"))
        except requests.RequestException as exc:
            flash(f"Unable to reach the backend API: {exc}", "error")
        except Exception as exc:
            flash(f"Unable to change password: {exc}", "error")

    return render_template(
        "auth/change_password.html",
        page_title="Change Password",
        page_kicker="Security",
    )

# File: fastcars-admin/utils/decorators.py
from __future__ import annotations

from functools import wraps

from flask import current_app, flash, redirect, request, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not current_app.config.get("API_URL"):
            session.clear()
            flash("Admin API is not configured. Set API_URL before using the admin workspace.", "error")
            return redirect(url_for("auth.login"))
        if "token" not in session:
            flash("Sign in to open the admin workspace.", "warning")
            next_path = request.path or url_for("dashboard.index")
            return redirect(url_for("auth.login", next=next_path))
        return view(*args, **kwargs)

    return wrapped_view

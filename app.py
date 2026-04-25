# File: fastcars-admin/app.py
from __future__ import annotations

import os
from datetime import date, datetime

from dotenv import load_dotenv
from flask import Flask, request

from blueprints.auth import auth_bp
from blueprints.bookings import bookings_bp
from blueprints.content import content_bp
from blueprints.dashboard import dashboard_bp
from blueprints.enquiries import enquiries_bp
from blueprints.subscribers import subscribers_bp
from blueprints.testimonials import testimonials_bp
from blueprints.users import users_bp
from blueprints.vehicles import vehicles_bp
from utils.helpers import parse_dateish

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fastcars-admin-dev-secret")
    app.config["API_URL"] = os.getenv("API_URL", "").rstrip("/")
    app.config["REQUEST_TIMEOUT"] = int(os.getenv("REQUEST_TIMEOUT", "20"))
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    register_filters(app)
    register_context(app)
    register_blueprints(app)

    return app


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(vehicles_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(testimonials_bp)
    app.register_blueprint(enquiries_bp)
    app.register_blueprint(subscribers_bp)
    app.register_blueprint(content_bp)


def register_context(app: Flask) -> None:
    navigation_items = [
        {"label": "Dashboard", "endpoint": "dashboard.index", "caption": "Overview"},
        {"label": "Vehicles", "endpoint": "vehicles.index", "caption": "Fleet"},
        {"label": "Brands", "endpoint": "vehicles.brands", "caption": "Taxonomy"},
        {"label": "Bookings", "endpoint": "bookings.index", "caption": "Queue"},
        {"label": "Users", "endpoint": "users.index", "caption": "Directory"},
        {"label": "Testimonials", "endpoint": "testimonials.index", "caption": "Reviews"},
        {"label": "Enquiries", "endpoint": "enquiries.index", "caption": "Inbox"},
        {"label": "Subscribers", "endpoint": "subscribers.index", "caption": "Audience"},
        {"label": "Content", "endpoint": "content.index", "caption": "CMS"},
        {"label": "Change Password", "endpoint": "auth.change_password", "caption": "Security"},
    ]

    @app.context_processor
    def inject_globals() -> dict[str, object]:
        api_configured = bool(app.config.get("API_URL"))
        return {
            "navigation_items": navigation_items,
            "current_year": datetime.now().year,
            "today_label": datetime.now().strftime("%b %d, %Y"),
            "has_live_api": api_configured,
            "api_status_label": "Backend API configured" if api_configured else "Backend API missing",
            "api_status_class": "is-positive" if api_configured else "is-warning",
            "current_endpoint": request.endpoint,
        }


def register_filters(app: Flask) -> None:
    @app.template_filter("currency")
    def currency_filter(value: object) -> str:
        try:
            amount = float(value or 0)
        except (TypeError, ValueError):
            amount = 0.0
        return f"NGN {amount:,.0f}"

    @app.template_filter("datefmt")
    def date_filter(value: object, fmt: str = "%b %d, %Y") -> str:
        parsed = parse_dateish(value)
        if isinstance(parsed, datetime):
            return parsed.strftime(fmt)
        if isinstance(parsed, date):
            return parsed.strftime(fmt)
        return str(value or "-")

    @app.template_filter("datetimefmt")
    def datetime_filter(value: object, fmt: str = "%b %d, %Y %H:%M") -> str:
        parsed = parse_dateish(value)
        if isinstance(parsed, datetime):
            return parsed.strftime(fmt)
        if isinstance(parsed, date):
            return parsed.strftime("%b %d, %Y")
        return str(value or "-")

    @app.template_filter("status_class")
    def status_class_filter(value: object) -> str:
        status = str(value or "").strip().lower()
        if status in {"confirmed", "active", "read"}:
            return "is-positive"
        if status in {"pending", "unread"}:
            return "is-warning"
        if status in {"cancelled", "inactive"}:
            return "is-danger"
        return "is-neutral"


app = create_app()


if __name__ == "__main__":
    app.run(debug=True,port=4000,host="0.0.0.0")

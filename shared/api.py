from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st

from shared.admin_data import (
    DEMO_ADMIN_EMAIL,
    DEMO_ADMIN_PASSWORD,
    booking_status_frame,
    dashboard_metrics,
    fleet_mix_frame,
    recent_bookings,
    store,
    to_frame,
)


def get_api_url() -> str:
    api_url = ""
    if "API_URL" in st.secrets:
        api_url = str(st.secrets["API_URL"])
    elif "api" in st.secrets and "url" in st.secrets["api"]:
        api_url = str(st.secrets["api"]["url"])
    else:
        api_url = os.getenv("API_URL", "")
    return api_url.rstrip("/")


def has_api() -> bool:
    return bool(get_api_url())


def auth_headers() -> dict[str, str]:
    token = st.session_state.get("admin_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _client() -> httpx.Client:
    return httpx.Client(base_url=get_api_url(), timeout=20.0)


def login_admin(email: str, password: str) -> tuple[bool, str]:
    if not has_api():
        if email == DEMO_ADMIN_EMAIL and password == DEMO_ADMIN_PASSWORD:
            st.session_state.admin_authenticated = True
            st.session_state.admin_token = "demo-token"
            st.session_state.auth_mode = "demo"
            return True, "Demo admin session started."
        return False, "Invalid demo credentials."

    try:
        with _client() as client:
            response = client.post("/api/auth/login", json={"email": email, "password": password})
            response.raise_for_status()
            payload = response.json()
            token = payload["access_token"]
            dashboard_response = client.get(
                "/api/admin/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )
            if dashboard_response.status_code == 403:
                return False, "This account is authenticated but does not have admin access."
            dashboard_response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        return False, f"Login failed: {detail}"
    except Exception as exc:
        return False, f"Unable to reach API: {exc}"

    st.session_state.admin_authenticated = True
    st.session_state.admin_token = token
    st.session_state.auth_mode = "live"
    st.session_state.admin_identity = {"name": email, "email": email, "role": "Admin"}
    return True, "Admin session started with live API."


def logout_admin() -> None:
    st.session_state.admin_authenticated = False
    st.session_state.admin_token = None
    st.session_state.auth_mode = "demo"


def get_dashboard_summary() -> tuple[dict[str, Any], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return dashboard_metrics(), "demo"
    with _client() as client:
        response = client.get("/api/admin/dashboard", headers=auth_headers())
        response.raise_for_status()
        return response.json(), "live"


def get_users() -> tuple[list[dict[str, Any]], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return [user for user in store()["users"] if user["role"] == "user"], "demo"
    with _client() as client:
        response = client.get("/api/admin/users/", headers=auth_headers())
        response.raise_for_status()
        return response.json(), "live"


def get_bookings() -> tuple[list[dict[str, Any]], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return store()["bookings"], "demo"
    with _client() as client:
        response = client.get("/api/admin/bookings/", headers=auth_headers())
        response.raise_for_status()
        return response.json(), "live"


def confirm_booking(booking_id: str) -> None:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        from shared.admin_data import update_booking_status

        update_booking_status(booking_id, "confirmed")
        return
    with _client() as client:
        response = client.patch(f"/api/admin/bookings/{booking_id}/confirm", headers=auth_headers())
        response.raise_for_status()


def cancel_booking(booking_id: str) -> None:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        from shared.admin_data import update_booking_status

        update_booking_status(booking_id, "cancelled")
        return
    with _client() as client:
        response = client.patch(f"/api/admin/bookings/{booking_id}/cancel", headers=auth_headers())
        response.raise_for_status()


def get_brands() -> tuple[list[dict[str, Any]], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return store()["brands"], "demo"
    with _client() as client:
        response = client.get("/api/admin/cars/brands", headers=auth_headers())
        response.raise_for_status()
        return response.json(), "live"


def create_brand(name: str, logo_url: str | None = None) -> None:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        from shared.admin_data import add_brand

        add_brand(name=name, country="Unknown", featured=False)
        return
    with _client() as client:
        response = client.post(
            "/api/admin/cars/brands",
            headers=auth_headers(),
            json={"name": name, "logo_url": logo_url},
        )
        response.raise_for_status()


def get_reference_cars() -> tuple[list[dict[str, Any]], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return store()["cars"], "demo"
    with _client() as client:
        response = client.get("/api/cars/", headers=auth_headers())
        response.raise_for_status()
        return response.json(), "live"


def create_car(payload: dict[str, Any]) -> None:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        from shared.admin_data import add_car

        add_car(payload)
        return
    with _client() as client:
        response = client.post("/api/admin/cars/", headers=auth_headers(), json=payload)
        response.raise_for_status()


def get_testimonials() -> tuple[list[dict[str, Any]], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return store()["testimonials"], "demo"
    with _client() as client:
        response = client.get("/api/admin/testimonials/", headers=auth_headers())
        response.raise_for_status()
        return response.json(), "live"


def set_testimonial_active(testimonial_id: str, is_active: bool) -> None:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        from shared.admin_data import toggle_testimonial

        toggle_testimonial(testimonial_id, "active" if is_active else "inactive")
        return
    with _client() as client:
        response = client.patch(
            f"/api/admin/testimonials/{testimonial_id}",
            headers=auth_headers(),
            json={"is_active": is_active},
        )
        response.raise_for_status()


def get_enquiries() -> tuple[list[dict[str, Any]], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return store()["enquiries"], "demo"
    with _client() as client:
        response = client.get("/api/admin/enquiries", headers=auth_headers())
        response.raise_for_status()
        return response.json(), "live"


def delete_enquiry(enquiry_id: str) -> None:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        store()["enquiries"] = [item for item in store()["enquiries"] if item["id"] != enquiry_id]
        return
    with _client() as client:
        response = client.delete(f"/api/admin/enquiries/{enquiry_id}", headers=auth_headers())
        response.raise_for_status()


def dashboard_booking_status() -> Any:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return booking_status_frame()
    bookings, _ = get_bookings()
    counts: dict[str, int] = {}
    for booking in bookings:
        key = booking.get("status", "unknown")
        counts[key] = counts.get(key, 0) + 1
    return to_frame([{"status": key.title(), "count": value} for key, value in counts.items()])


def dashboard_fleet_mix() -> Any:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return fleet_mix_frame()
    cars, _ = get_reference_cars()
    counts: dict[str, int] = {}
    for car in cars:
        brand = car.get("brand_name") or car.get("brand") or car.get("brand_id") or "Unknown"
        counts[brand] = counts.get(brand, 0) + 1
    return to_frame([{"brand": key, "vehicles": value} for key, value in counts.items()])


def dashboard_recent_bookings() -> Any:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return recent_bookings()
    bookings, _ = get_bookings()
    normalized = []
    for item in bookings:
        normalized.append(
            {
                "booking_ref": item.get("_id", "")[:8],
                "customer": item.get("user_id", "User"),
                "car_name": item.get("car_id", "Car"),
                "status": item.get("status"),
                "total_cost": item.get("total_price", 0),
                "created_at": item.get("created_at"),
            }
        )
    normalized.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
    return to_frame(normalized[:5])

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
    return get_setting("API_URL", nested_path=("api", "url")).rstrip("/")


def get_setting(*keys: str, nested_path: tuple[str, ...] | None = None, default: str = "") -> str:
    for key in keys:
        if key in st.secrets:
            value = st.secrets[key]
            if value not in (None, ""):
                return str(value)
        env_value = os.getenv(key)
        if env_value not in (None, ""):
            return env_value

    if nested_path:
        current: Any = st.secrets
        for part in nested_path:
            if part not in current:
                break
            current = current[part]
        else:
            if current not in (None, ""):
                return str(current)
    return default


def has_api() -> bool:
    return bool(get_api_url())


def auth_headers() -> dict[str, str]:
    token = st.session_state.get("admin_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _client() -> httpx.Client:
    return httpx.Client(base_url=get_api_url(), timeout=20.0)


def upload_car_images(files: list[Any]) -> list[str]:
    if not files:
        return []
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return [f"demo-upload://{getattr(file, 'name', 'image')}" for file in files]
    uploaded_urls: list[str] = []
    with _client() as client:
        for file in files:
            response = client.post(
                "/api/admin/cars/upload",
                headers=auth_headers(),
                files={
                    "file": (
                        getattr(file, "name", "upload.jpg"),
                        file.getvalue(),
                        getattr(file, "type", "application/octet-stream"),
                    )
                },
            )
            if response.status_code == 422:
                detail = response.json().get("detail", response.text)
                raise ValueError(f"Image upload failed: {detail}")
            response.raise_for_status()
            payload = response.json()
            image_url = payload.get("url")
            if not image_url:
                raise RuntimeError("Image upload succeeded but no URL was returned by the admin upload endpoint.")
            uploaded_urls.append(str(image_url))
    return uploaded_urls


def _booking_identifier(booking: dict[str, Any]) -> str:
    return str(
        booking.get("id")
        or booking.get("_id")
        or booking.get("booking_id")
        or booking.get("booking_ref")
        or ""
    )


def _normalize_booking(booking: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(booking)
    normalized["id"] = _booking_identifier(booking)
    normalized["booking_ref"] = booking.get("booking_ref") or normalized["id"] or "booking"
    normalized["customer"] = booking.get("customer") or booking.get("user_name") or booking.get("user_id") or "Unknown"
    normalized["car_name"] = booking.get("car_name") or booking.get("car_id") or "Unknown"
    normalized["start_date"] = booking.get("start_date")
    normalized["end_date"] = booking.get("end_date")
    normalized["status"] = booking.get("status", "unknown")
    normalized["total_cost"] = booking.get("total_cost", booking.get("total_price", 0))
    return normalized


def _normalize_booking_collection(payload: Any) -> list[dict[str, Any]]:
    items = payload.get("items", payload) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return []
    return [_normalize_booking(item) for item in items if isinstance(item, dict)]


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


def get_user_detail(user_id: str) -> tuple[dict[str, Any], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        user = next((item for item in store()["users"] if item.get("id") == user_id or item.get("_id") == user_id), {})
        return user, "demo"
    with _client() as client:
        response = client.get(f"/api/admin/users/{user_id}", headers=auth_headers())
        response.raise_for_status()
        return response.json(), "live"


def get_bookings() -> tuple[list[dict[str, Any]], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return _normalize_booking_collection(store()["bookings"]), "demo"
    with _client() as client:
        response = client.get("/api/admin/bookings/", headers=auth_headers())
        response.raise_for_status()
        return _normalize_booking_collection(response.json()), "live"


def get_booking_detail(booking_id: str) -> tuple[dict[str, Any], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        booking = next(
            (item for item in store()["bookings"] if _booking_identifier(item) == booking_id),
            {},
        )
        return _normalize_booking(booking) if booking else {}, "demo"
    with _client() as client:
        response = client.get(f"/api/admin/bookings/{booking_id}", headers=auth_headers())
        response.raise_for_status()
        payload = response.json()
        return _normalize_booking(payload) if isinstance(payload, dict) else {}, "live"


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


def get_admin_cars() -> tuple[list[dict[str, Any]], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return store()["cars"], "demo"
    with _client() as client:
        response = client.get("/api/admin/cars/", headers=auth_headers())
        response.raise_for_status()
        return response.json(), "live"


def _sanitize_car_payload(payload: dict[str, Any]) -> dict[str, Any]:
    allowed_fields = {
        "brand_id",
        "name",
        "category",
        "description",
        "images",
        "daily_rate",
        "seats",
        "transmission",
        "fuel_type",
        "status",
    }
    return {key: value for key, value in payload.items() if key in allowed_fields}


def create_car(payload: dict[str, Any]) -> None:
    sanitized_payload = _sanitize_car_payload(payload)

    if not has_api() or st.session_state.get("auth_mode") != "live":
        from shared.admin_data import add_car

        add_car(sanitized_payload)
        return
    with _client() as client:
        response = client.post("/api/admin/cars/", headers=auth_headers(), json=sanitized_payload)
        if response.status_code == 422:
            detail = response.json().get("detail", response.text)
            raise ValueError(f"Validation failed: {detail}")
        response.raise_for_status()


def update_car(car_id: str, payload: dict[str, Any]) -> None:
    sanitized_payload = _sanitize_car_payload(payload)

    if not has_api() or st.session_state.get("auth_mode") != "live":
        from shared.admin_data import update_car_record

        update_car_record(car_id, sanitized_payload)
        return
    with _client() as client:
        response = client.put(f"/api/admin/cars/{car_id}", headers=auth_headers(), json=sanitized_payload)
        if response.status_code == 422:
            detail = response.json().get("detail", response.text)
            raise ValueError(f"Validation failed: {detail}")
        response.raise_for_status()


def delete_car(car_id: str) -> None:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        from shared.admin_data import delete_car_record

        delete_car_record(car_id)
        return
    with _client() as client:
        response = client.delete(f"/api/admin/cars/{car_id}", headers=auth_headers())
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


def mark_enquiry_read(enquiry_id: str) -> None:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        from shared.admin_data import mark_enquiry_status

        mark_enquiry_status(enquiry_id, "read")
        return
    with _client() as client:
        response = client.patch(
            f"/api/admin/enquiries/{enquiry_id}",
            headers=auth_headers(),
            json={"status": "read"},
        )
        response.raise_for_status()


def get_subscribers() -> tuple[list[dict[str, Any]], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return store()["subscribers"], "demo"
    with _client() as client:
        response = client.get("/api/admin/subscribers", headers=auth_headers())
        response.raise_for_status()
        return response.json(), "live"


def remove_subscriber(subscriber_id: str) -> None:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        from shared.admin_data import delete_subscriber

        delete_subscriber(subscriber_id)
        return
    with _client() as client:
        response = client.delete(f"/api/admin/subscribers/{subscriber_id}", headers=auth_headers())
        response.raise_for_status()


def upsert_site_content(key: str, value: str) -> tuple[dict[str, Any], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        from shared.admin_data import save_site_content

        save_site_content(key, value)
        return {"key": key, "value": value}, "demo"
    with _client() as client:
        response = client.patch(
            f"/api/admin/site-content/{key}",
            headers=auth_headers(),
            json={"value": value},
        )
        response.raise_for_status()
        return response.json(), "live"


def get_site_content() -> tuple[list[dict[str, Any]], str]:
    if not has_api() or st.session_state.get("auth_mode") != "live":
        return [{"key": key, "value": value} for key, value in store()["site_content"].items()], "demo"
    with _client() as client:
        response = client.get("/api/admin/site-content", headers=auth_headers())
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            if "items" in payload and isinstance(payload["items"], list):
                return payload["items"], "live"
            return [{"key": key, "value": value} for key, value in payload.items()], "live"
        return payload, "live"


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
    cars, _ = get_admin_cars()
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
                "booking_ref": item.get("booking_ref", "booking"),
                "customer": item.get("customer", "Unknown"),
                "car_name": item.get("car_name", "Unknown"),
                "status": item.get("status"),
                "total_cost": item.get("total_cost", 0),
                "created_at": item.get("created_at"),
            }
        )
    normalized.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
    return to_frame(normalized[:5])

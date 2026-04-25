# File: fastcars-admin/utils/helpers.py
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import plotly.express as px
import requests
from flask import current_app, session


class AuthSessionExpired(RuntimeError):
    """Raised when the backend rejects the stored admin token."""


def api_enabled() -> bool:
    return bool(current_app.config.get("API_URL"))


def auth_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = dict(extra or {})
    token = session.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def api_request(method: str, path: str, **kwargs) -> requests.Response:
    api_url = current_app.config.get("API_URL", "").rstrip("/")
    if not api_url:
        raise RuntimeError("API_URL is not configured.")
    timeout = kwargs.pop("timeout", current_app.config.get("REQUEST_TIMEOUT", 20))
    return requests.request(method.upper(), f"{api_url}{path}", timeout=timeout, **kwargs)


def extract_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip() or f"Request failed with status {response.status_code}."

    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, list):
            parts: list[str] = []
            for item in detail:
                if isinstance(item, dict):
                    parts.append(str(item.get("msg") or item.get("message") or item))
                else:
                    parts.append(str(item))
            return "; ".join(parts)
        if detail:
            return str(detail)
        message = payload.get("message") or payload.get("error")
        if message:
            return str(message)
    return response.text.strip() or f"Request failed with status {response.status_code}."


def ensure_response(
    response: requests.Response,
    acceptable: tuple[int, ...] = (200, 201, 202, 204),
) -> requests.Response:
    if response.status_code in acceptable:
        return response
    message = extract_error_message(response)
    if response.status_code in (401, 403):
        raise AuthSessionExpired(message or "Your admin session expired.")
    raise RuntimeError(message)


def parse_dateish(value: Any) -> datetime | date | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        candidate = candidate.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            try:
                return date.fromisoformat(candidate)
            except ValueError:
                return None
    return None


def display_name_from_email(email: str) -> str:
    stem = (email or "Admin").split("@", 1)[0]
    clean = stem.replace(".", " ").replace("_", " ").replace("-", " ")
    return " ".join(part.capitalize() for part in clean.split()) or "Admin"


def stringify_value(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("$oid", "$id", "oid", "id", "_id", "value"):
            candidate = stringify_value(value.get(key))
            if candidate:
                return candidate
        return ""
    return str(value)


def item_identifier(item: dict[str, Any]) -> str:
    for key in ("id", "_id", "booking_id", "booking_ref"):
        candidate = stringify_value(item.get(key))
        if candidate:
            return candidate
    return ""


def normalize_user(item: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(item)
    email = str(
        item.get("email")
        or item.get("user_email")
        or item.get("mail")
        or ""
    ).strip()
    first_name = str(item.get("first_name") or item.get("firstname") or "").strip()
    last_name = str(item.get("last_name") or item.get("lastname") or "").strip()
    full_name = " ".join(part for part in (first_name, last_name) if part).strip()
    role = str(item.get("role") or item.get("user_type") or "user").strip().lower()
    status = item.get("status")
    if isinstance(status, str) and status.strip():
        normalized_status = status.strip().lower()
    else:
        normalized_status = "active" if item.get("is_active", True) else "inactive"

    normalized["id"] = item_identifier(item)
    normalized["_id"] = normalized["id"]
    normalized["email"] = email
    normalized["name"] = (
        str(item.get("name") or item.get("full_name") or full_name).strip()
        or display_name_from_email(email)
    )
    normalized["phone"] = str(
        item.get("phone")
        or item.get("phone_number")
        or item.get("mobile")
        or ""
    ).strip()
    normalized["role"] = role or "user"
    normalized["status"] = normalized_status
    normalized["created_at"] = (
        item.get("created_at")
        or item.get("createdAt")
        or item.get("joined_at")
        or item.get("date_joined")
    )
    normalized["last_seen"] = (
        item.get("last_seen")
        or item.get("last_login")
        or item.get("updated_at")
        or item.get("updatedAt")
    )
    return normalized


def normalize_user_collection(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        items = (
            payload.get("items")
            or payload.get("results")
            or payload.get("users")
            or payload.get("data")
            or payload
        )
    else:
        items = payload
    if not isinstance(items, list):
        return []
    return [normalize_user(item) for item in items if isinstance(item, dict)]


def normalize_booking(item: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(item)
    normalized["id"] = item_identifier(item)
    normalized["booking_ref"] = item.get("booking_ref") or normalized["id"] or "booking"
    normalized["customer"] = item.get("customer") or item.get("user_name") or item.get("user_id") or "Unknown"
    normalized["car_name"] = item.get("car_name") or item.get("car_id") or "Unknown"
    normalized["status"] = item.get("status", "unknown")
    normalized["total_cost"] = item.get("total_cost", item.get("total_price", 0))
    normalized["start_date"] = item.get("start_date")
    normalized["end_date"] = item.get("end_date")
    return normalized


def normalize_booking_collection(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        items = payload.get("items", payload.get("results", payload))
    else:
        items = payload
    if not isinstance(items, list):
        return []
    return [normalize_booking(item) for item in items if isinstance(item, dict)]


def normalize_site_content(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
        return [{"key": key, "value": value} for key, value in payload.items()]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def resolve_brand_name(car: dict[str, Any], brands: list[dict[str, Any]]) -> str:
    if car.get("brand_name"):
        return str(car["brand_name"])
    if car.get("brand"):
        return str(car["brand"])
    brand_id = car.get("brand_id")
    if brand_id:
        for brand in brands:
            if brand.get("id") == brand_id or brand.get("_id") == brand_id:
                return str(brand.get("name", brand_id))
        return str(brand_id)
    return "Unknown"


def normalize_car_rows(cars: list[dict[str, Any]], brands: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for car in cars:
        entry = dict(car)
        entry["id"] = item_identifier(car)
        entry["brand_name"] = resolve_brand_name(car, brands)
        images = car.get("images") or ([car.get("image_url")] if car.get("image_url") else [])
        entry["images"] = [image for image in images if image]
        entry["image_url"] = entry["images"][0] if entry["images"] else ""
        entry["status"] = str(car.get("status", "active")).lower()
        entry["featured"] = bool(car.get("featured"))
        normalized.append(entry)
    return normalized


def build_bar_chart_html(
    rows: list[dict[str, Any]],
    x_key: str,
    y_key: str,
    title: str,
    color: str,
) -> str:
    if not rows:
        rows = [{x_key: "No data", y_key: 0}]
    figure = px.bar(
        rows,
        x=x_key,
        y=y_key,
        text=y_key,
    )
    figure.update_traces(
        marker_color=color,
        textposition="outside",
        hovertemplate=f"%{{x}}<br>%{{y}}<extra>{title}</extra>",
    )
    figure.update_layout(
        title=title,
        margin={"l": 24, "r": 16, "t": 56, "b": 24},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f7fbff",
        font={"family": "IBM Plex Sans, Segoe UI, sans-serif", "color": "#102542"},
        xaxis_title="",
        yaxis_title="",
        yaxis=dict(gridcolor="rgba(15, 35, 66, 0.08)"),
    )
    return figure.to_html(full_html=False, include_plotlyjs="cdn", config={"displayModeBar": False})

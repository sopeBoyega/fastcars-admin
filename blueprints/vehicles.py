# File: fastcars-admin/blueprints/vehicles.py
from __future__ import annotations

from typing import Any

import requests
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from utils.decorators import login_required
from utils.helpers import (
    AuthSessionExpired,
    api_request,
    auth_headers,
    ensure_response,
    item_identifier,
    normalize_car_rows,
)

vehicles_bp = Blueprint("vehicles", __name__)


def _redirect_vehicle_index(form_data: dict[str, Any], fallback_car_id: str = ""):
    params: dict[str, str] = {}
    brand = str(form_data.get("return_brand", "All"))
    status = str(form_data.get("return_status", "All"))
    if brand and brand != "All":
        params["brand"] = brand
    if status and status != "All":
        params["status"] = status
    if str(form_data.get("return_featured", "")) == "1":
        params["featured"] = "1"
    selected_id = str(form_data.get("return_car_id") or fallback_car_id or "")
    if selected_id:
        params["car_id"] = selected_id
    return redirect(url_for("vehicles.index", **params))


def _load_brands() -> tuple[list[dict[str, Any]], str]:
    response = api_request("GET", "/api/admin/cars/brands", headers=auth_headers())
    ensure_response(response)
    payload = response.json()
    if isinstance(payload, list):
        brands = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            normalized = dict(item)
            normalized["id"] = item_identifier(item)
            normalized["_id"] = normalized["id"]
            normalized["name"] = str(item.get("name", "Unnamed brand")).strip() or "Unnamed brand"
            normalized["logo_url"] = item.get("logo_url") or ""
            brands.append(normalized)
        return brands, "Backend API"
    return [], "Backend API"


def _load_cars(brands: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    response = api_request("GET", "/api/admin/cars/", headers=auth_headers())
    ensure_response(response)
    payload = response.json()
    if isinstance(payload, list):
        return normalize_car_rows(payload, brands), "Backend API"
    return [], "Backend API"


def _upload_image_files(files: list[Any]) -> list[str]:
    valid_files = [file for file in files if getattr(file, "filename", "")]
    if not valid_files:
        return []

    uploaded_urls: list[str] = []
    for upload in valid_files:
        content_type = upload.mimetype or "application/octet-stream"
        file_payload = {"file": (upload.filename, upload.read(), content_type)}
        response = api_request(
            "POST",
            "/api/admin/cars/upload",
            headers=auth_headers(),
            files=file_payload,
        )
        ensure_response(response)
        payload = response.json()
        image_url = payload.get("url")
        if not image_url:
            raise RuntimeError("Image upload succeeded but no URL was returned by the backend.")
        uploaded_urls.append(str(image_url))
    return uploaded_urls


def _build_car_payload(form_data, uploaded_files) -> dict[str, Any]:
    description = form_data.get("description", "").strip()
    if len(description) < 10:
        raise ValueError("Description must be at least 10 characters long.")

    brand_id = form_data.get("brand_id", "").strip()
    if not brand_id:
        raise ValueError("A brand must be selected.")

    name = form_data.get("name", "").strip()
    if not name:
        raise ValueError("Car name is required.")

    image_urls = [
        line.strip()
        for line in form_data.get("image_urls", "").splitlines()
        if line.strip()
    ]
    image_urls.extend(_upload_image_files(uploaded_files))

    return {
        "brand_id": brand_id,
        "name": name,
        "category": form_data.get("category", "Economy"),
        "description": description,
        "images": image_urls,
        "daily_rate": float(form_data.get("daily_rate", 0) or 0),
        "seats": int(form_data.get("seats", 0) or 0),
        "transmission": form_data.get("transmission", "Automatic"),
        "fuel_type": form_data.get("fuel_type", "Petrol"),
        "status": form_data.get("status", "active"),
    }


@vehicles_bp.route("/brands", methods=["GET", "POST"])
@login_required
def brands():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        logo_url = request.form.get("logo_url", "").strip()
        if not name:
            flash("Brand name is required.", "error")
            return redirect(url_for("vehicles.brands"))

        try:
            response = api_request(
                "POST",
                "/api/admin/cars/brands",
                headers=auth_headers(),
                json={"name": name, "logo_url": logo_url or None},
            )
            ensure_response(response)
            flash(f"{name} added to the brand library.", "success")
            return redirect(url_for("vehicles.brands"))
        except AuthSessionExpired:
            session.clear()
            flash("Your admin session expired. Sign in again to continue.", "warning")
            return redirect(url_for("auth.login"))
        except requests.RequestException as exc:
            flash(f"Unable to reach the backend API: {exc}", "error")
            return redirect(url_for("vehicles.brands"))
        except Exception as exc:
            flash(f"Unable to create brand: {exc}", "error")
            return redirect(url_for("vehicles.brands"))

    try:
        brands_rows, source = _load_brands()
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except Exception as exc:
        flash(f"Unable to load brands: {exc}", "error")
        brands_rows, source = [], "Backend API"

    return render_template(
        "vehicles/brands.html",
        page_title="Brand Management",
        page_kicker="Fleet taxonomy",
        brands=sorted(brands_rows, key=lambda item: str(item.get("created_at", "")), reverse=True),
        featured_brands=brands_rows[:3],
        source=source,
    )


@vehicles_bp.route("/brands/<brand_id>/update", methods=["POST"])
@login_required
def update_brand(brand_id: str):
    name = request.form.get("name", "").strip()
    logo_url = request.form.get("logo_url", "").strip()
    if not name:
        flash("Brand name is required.", "error")
        return redirect(url_for("vehicles.brands"))

    try:
        response = api_request(
            "PATCH",
            f"/api/admin/cars/brands/{brand_id}",
            headers=auth_headers(),
            json={"name": name, "logo_url": logo_url or None},
        )
        ensure_response(response)
        flash(f"{name} updated successfully.", "success")
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except requests.RequestException as exc:
        flash(f"Unable to reach the backend API: {exc}", "error")
    except Exception as exc:
        flash(f"Unable to update brand: {exc}", "error")
    return redirect(url_for("vehicles.brands"))


@vehicles_bp.route("/brands/<brand_id>/delete", methods=["POST"])
@login_required
def delete_brand(brand_id: str):
    brand_name = request.form.get("brand_name", "Brand")
    try:
        response = api_request(
            "DELETE",
            f"/api/admin/cars/brands/{brand_id}",
            headers=auth_headers(),
        )
        ensure_response(response)
        flash(f"{brand_name} deleted from the brand library.", "success")
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except requests.RequestException as exc:
        flash(f"Unable to reach the backend API: {exc}", "error")
    except Exception as exc:
        flash(f"Unable to delete brand: {exc}", "error")
    return redirect(url_for("vehicles.brands"))


@vehicles_bp.route("/vehicles", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        try:
            payload = _build_car_payload(request.form, request.files.getlist("image_files"))
            response = api_request(
                "POST",
                "/api/admin/cars/",
                headers=auth_headers(),
                json=payload,
            )
            ensure_response(response)
            flash(f"{payload['name']} has been added to the fleet list.", "success")
        except AuthSessionExpired:
            session.clear()
            flash("Your admin session expired. Sign in again to continue.", "warning")
            return redirect(url_for("auth.login"))
        except requests.RequestException as exc:
            flash(f"Unable to reach the backend API: {exc}", "error")
        except Exception as exc:
            flash(f"Unable to create car: {exc}", "error")
        return redirect(url_for("vehicles.index"))

    try:
        brands, _ = _load_brands()
        all_cars, source = _load_cars(brands)
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except Exception as exc:
        flash(f"Unable to load vehicles: {exc}", "error")
        brands = []
        all_cars = []
        source = "Backend API"

    brand_filter = request.args.get("brand", "All")
    status_filter = request.args.get("status", "All")
    featured_only = request.args.get("featured") == "1"

    filtered_cars = list(all_cars)
    if brand_filter != "All":
        filtered_cars = [car for car in filtered_cars if car.get("brand_name") == brand_filter]
    if status_filter != "All":
        filtered_cars = [car for car in filtered_cars if car.get("status") == status_filter]
    if featured_only:
        filtered_cars = [car for car in filtered_cars if car.get("featured")]

    selected_car_id = request.args.get("car_id") or (filtered_cars[0]["id"] if filtered_cars else "")
    selected_car = next((car for car in filtered_cars if car.get("id") == selected_car_id), None)

    brand_options = ["All"] + sorted({car.get("brand_name", "Unknown") for car in all_cars})
    brand_map = {brand["name"]: brand.get("id") for brand in brands if brand.get("name")}

    return render_template(
        "vehicles/index.html",
        page_title="Fleet Inventory",
        page_kicker="Vehicles",
        source=source,
        brands=brands,
        brand_map=brand_map,
        all_cars=all_cars,
        filtered_cars=filtered_cars,
        selected_car=selected_car,
        brand_options=brand_options,
        brand_filter=brand_filter,
        status_filter=status_filter,
        featured_only=featured_only,
    )


@vehicles_bp.route("/vehicles/<car_id>/update", methods=["POST"])
@login_required
def update_vehicle(car_id: str):
    try:
        payload = _build_car_payload(request.form, request.files.getlist("image_files"))
        response = api_request(
            "PUT",
            f"/api/admin/cars/{car_id}",
            headers=auth_headers(),
            json=payload,
        )
        ensure_response(response)
        flash(f"{payload['name']} updated successfully.", "success")
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except requests.RequestException as exc:
        flash(f"Unable to reach the backend API: {exc}", "error")
    except Exception as exc:
        flash(f"Unable to update car: {exc}", "error")
    return _redirect_vehicle_index(request.form, fallback_car_id=car_id)


@vehicles_bp.route("/vehicles/<car_id>/delete", methods=["POST"])
@login_required
def delete_vehicle(car_id: str):
    try:
        car_name = request.form.get("car_name", "Car")
        response = api_request(
            "DELETE",
            f"/api/admin/cars/{car_id}",
            headers=auth_headers(),
        )
        ensure_response(response)
        flash(f"{car_name} deleted.", "success")
    except AuthSessionExpired:
        session.clear()
        flash("Your admin session expired. Sign in again to continue.", "warning")
        return redirect(url_for("auth.login"))
    except requests.RequestException as exc:
        flash(f"Unable to reach the backend API: {exc}", "error")
    except Exception as exc:
        flash(f"Unable to delete car: {exc}", "error")
    return _redirect_vehicle_index(request.form)

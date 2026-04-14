from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
import streamlit as st

DEMO_ADMIN_EMAIL = "admin@fastcars.com"
DEMO_ADMIN_PASSWORD = "admin123"


def _seed_store() -> dict[str, Any]:
    today = date.today()
    now = datetime.now()
    return {
        "brands": [
            {"id": "brand-1", "name": "Mercedes-Benz", "country": "Germany", "vehicle_count": 12, "featured": True, "logo_url": "", "created_at": now - timedelta(days=42)},
            {"id": "brand-2", "name": "BMW", "country": "Germany", "vehicle_count": 9, "featured": True, "logo_url": "", "created_at": now - timedelta(days=35)},
            {"id": "brand-3", "name": "Lexus", "country": "Japan", "vehicle_count": 7, "featured": False, "logo_url": "", "created_at": now - timedelta(days=27)},
            {"id": "brand-4", "name": "Range Rover", "country": "United Kingdom", "vehicle_count": 6, "featured": True, "logo_url": "", "created_at": now - timedelta(days=20)},
        ],
        "cars": [
            {"id": "car-101", "brand": "Mercedes-Benz", "name": "G-Wagon AMG", "category": "Luxury SUV", "daily_rate": 285000, "seats": 5, "transmission": "Automatic", "fuel_type": "Petrol", "status": "active", "featured": True, "image_url": "", "created_at": now - timedelta(days=15)},
            {"id": "car-102", "brand": "BMW", "name": "X7 M Sport", "category": "Premium SUV", "daily_rate": 215000, "seats": 7, "transmission": "Automatic", "fuel_type": "Petrol", "status": "active", "featured": True, "image_url": "", "created_at": now - timedelta(days=12)},
            {"id": "car-103", "brand": "Lexus", "name": "RX 350 Executive", "category": "Luxury", "daily_rate": 165000, "seats": 5, "transmission": "Automatic", "fuel_type": "Petrol", "status": "inactive", "featured": False, "image_url": "", "created_at": now - timedelta(days=9)},
            {"id": "car-104", "brand": "Range Rover", "name": "Velar Dynamic", "category": "Luxury SUV", "daily_rate": 245000, "seats": 5, "transmission": "Automatic", "fuel_type": "Diesel", "status": "active", "featured": True, "image_url": "", "created_at": now - timedelta(days=6)},
            {"id": "car-105", "brand": "Mercedes-Benz", "name": "C300 Cabriolet", "category": "Premium", "daily_rate": 145000, "seats": 4, "transmission": "Automatic", "fuel_type": "Petrol", "status": "active", "featured": False, "image_url": "", "created_at": now - timedelta(days=4)},
        ],
        "users": [
            {"id": "user-1", "name": "Amina Yusuf", "email": "amina@fastcars.ng", "phone": "+234 801 111 2222", "role": "user", "status": "active", "bookings": 4, "last_seen": now - timedelta(hours=2), "created_at": now - timedelta(days=90)},
            {"id": "user-2", "name": "David Cole", "email": "david@example.com", "phone": "+234 809 876 5544", "role": "user", "status": "active", "bookings": 2, "last_seen": now - timedelta(days=1), "created_at": now - timedelta(days=61)},
            {"id": "user-3", "name": "Ifeoma Obi", "email": "ifeoma@example.com", "phone": "+234 802 902 5500", "role": "user", "status": "inactive", "bookings": 0, "last_seen": now - timedelta(days=10), "created_at": now - timedelta(days=45)},
            {"id": "user-4", "name": "Admin Operator", "email": DEMO_ADMIN_EMAIL, "phone": "+234 800 000 0000", "role": "admin", "status": "active", "bookings": 0, "last_seen": now - timedelta(minutes=20), "created_at": now - timedelta(days=180)},
        ],
        "bookings": [
            {"id": "booking-1", "booking_ref": "FC-10021", "customer": "Amina Yusuf", "car_name": "G-Wagon AMG", "start_date": today + timedelta(days=1), "end_date": today + timedelta(days=4), "status": "pending", "total_cost": 855000, "created_at": now - timedelta(hours=6)},
            {"id": "booking-2", "booking_ref": "FC-10020", "customer": "David Cole", "car_name": "X7 M Sport", "start_date": today - timedelta(days=5), "end_date": today - timedelta(days=2), "status": "confirmed", "total_cost": 645000, "created_at": now - timedelta(days=3)},
            {"id": "booking-3", "booking_ref": "FC-10019", "customer": "Amina Yusuf", "car_name": "Velar Dynamic", "start_date": today + timedelta(days=8), "end_date": today + timedelta(days=12), "status": "pending", "total_cost": 980000, "created_at": now - timedelta(days=1, hours=4)},
            {"id": "booking-4", "booking_ref": "FC-10018", "customer": "Ifeoma Obi", "car_name": "RX 350 Executive", "start_date": today - timedelta(days=10), "end_date": today - timedelta(days=8), "status": "cancelled", "total_cost": 330000, "created_at": now - timedelta(days=8)},
        ],
        "testimonials": [
            {"id": "testimonial-1", "user_name": "Amina Yusuf", "message": "Fast pickup, spotless interior, and the support team stayed responsive all through the trip.", "rating": 5, "status": "active", "created_at": now - timedelta(days=7)},
            {"id": "testimonial-2", "user_name": "David Cole", "message": "Booking was smooth but I would love even more self-service options for delivery timing.", "rating": 4, "status": "inactive", "created_at": now - timedelta(days=2)},
            {"id": "testimonial-3", "user_name": "Mariam Hassan", "message": "The BMW arrived exactly as shown online. This is the level of polish the brand should keep.", "rating": 5, "status": "inactive", "created_at": now - timedelta(hours=18)},
        ],
        "site_content": {
            "hero_headline": "Rent premium cars in minutes, not days.",
            "hero_subtext": "Fast Cars connects business travellers, wedding clients, and premium mobility customers with a polished self-service booking flow.",
            "contact_phone": "+234 700 FASTCARS",
            "contact_email": "hello@fastcars.ng",
            "about_summary": "Fast Cars is building a premium-first vehicle booking experience for Nigeria with elegant fleet presentation, reliable operations, and admin-grade control.",
        },
        "enquiries": [
            {"id": "enquiry-1", "name": "Chinedu Okafor", "email": "chinedu@example.com", "phone": "+234 813 111 9900", "message": "Can I book the G-Wagon for airport pickup plus out-of-state travel?", "status": "unread", "created_at": now - timedelta(hours=5)},
            {"id": "enquiry-2", "name": "Susan Hart", "email": "susan@example.com", "phone": "+234 805 555 1099", "message": "Do you provide weekly corporate rates for executive assistants booking for teams?", "status": "read", "created_at": now - timedelta(days=2)},
            {"id": "enquiry-3", "name": "Adeola B.", "email": "adeola@example.com", "phone": "+234 815 221 4466", "message": "I need a luxury SUV for a wedding convoy in May. Please share options.", "status": "unread", "created_at": now - timedelta(hours=11)},
        ],
        "subscribers": [
            {"id": "subscriber-1", "email": "vip@company.com", "segment": "Corporate", "created_at": now - timedelta(days=16)},
            {"id": "subscriber-2", "email": "luxurydriver@gmail.com", "segment": "Luxury", "created_at": now - timedelta(days=9)},
            {"id": "subscriber-3", "email": "weddings@events.co", "segment": "Events", "created_at": now - timedelta(days=3)},
        ],
    }


def init_demo_state() -> None:
    if "fastcars_store" not in st.session_state:
        st.session_state.fastcars_store = deepcopy(_seed_store())
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    if "admin_token" not in st.session_state:
        st.session_state.admin_token = None
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "demo"
    if "admin_identity" not in st.session_state:
        st.session_state.admin_identity = {"name": "Admin Operator", "email": DEMO_ADMIN_EMAIL, "role": "Super Admin"}


def store() -> dict[str, Any]:
    init_demo_state()
    return st.session_state.fastcars_store


def to_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    for column in ("created_at", "last_seen", "start_date", "end_date"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column])
    return frame


def dashboard_metrics() -> dict[str, Any]:
    data = store()
    confirmed_revenue = sum(item["total_cost"] for item in data["bookings"] if item["status"] == "confirmed")
    return {
        "users": sum(1 for user in data["users"] if user["role"] == "user"),
        "active_cars": sum(1 for car in data["cars"] if car["status"] == "active"),
        "pending_bookings": sum(1 for item in data["bookings"] if item["status"] == "pending"),
        "confirmed_revenue": confirmed_revenue,
        "subscribers": len(data["subscribers"]),
        "unread_enquiries": sum(1 for item in data["enquiries"] if item["status"] == "unread"),
    }


def booking_status_frame() -> pd.DataFrame:
    counts: dict[str, int] = {}
    for item in store()["bookings"]:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return pd.DataFrame([{"status": key.title(), "count": value} for key, value in counts.items()])


def fleet_mix_frame() -> pd.DataFrame:
    counts: dict[str, int] = {}
    for item in store()["cars"]:
        counts[item["brand"]] = counts.get(item["brand"], 0) + 1
    return pd.DataFrame([{"brand": key, "vehicles": value} for key, value in counts.items()])


def recent_bookings(limit: int = 5) -> pd.DataFrame:
    items = sorted(store()["bookings"], key=lambda item: item["created_at"], reverse=True)[:limit]
    return to_frame(items)


def add_brand(name: str, country: str, featured: bool) -> None:
    data = store()
    data["brands"].append({"id": f"brand-{len(data['brands']) + 1}", "name": name, "country": country, "vehicle_count": 0, "featured": featured, "logo_url": "", "created_at": datetime.now()})


def add_car(payload: dict[str, Any]) -> None:
    data = store()
    payload["id"] = f"car-{100 + len(data['cars']) + 1}"
    payload["created_at"] = datetime.now()
    data["cars"].append(payload)
    for brand in data["brands"]:
        if brand["name"] == payload["brand"]:
            brand["vehicle_count"] += 1
            break


def update_booking_status(booking_id: str, status: str) -> None:
    for booking in store()["bookings"]:
        if booking["id"] == booking_id:
            booking["status"] = status
            return


def toggle_testimonial(testimonial_id: str, status: str) -> None:
    for testimonial in store()["testimonials"]:
        if testimonial["id"] == testimonial_id:
            testimonial["status"] = status
            return


def save_site_content(key: str, value: str) -> None:
    store()["site_content"][key] = value


def mark_enquiry_status(enquiry_id: str, status: str) -> None:
    for enquiry in store()["enquiries"]:
        if enquiry["id"] == enquiry_id:
            enquiry["status"] = status
            return


def delete_subscriber(subscriber_id: str) -> None:
    data = store()
    data["subscribers"] = [item for item in data["subscribers"] if item["id"] != subscriber_id]

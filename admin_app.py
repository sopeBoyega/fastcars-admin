# Entry point for the FastCars admin app
# Add Streamlit app logic here.

import streamlit as st

from shared.admin_data import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD
from shared.api import get_dashboard_summary, has_api, login_admin
from shared.admin_ui import boot, page_header, render_sidebar


boot("Admin Home")
render_sidebar()

page_header(
    "Admin control room for fleet, bookings, and content",
    "FastCars Admin UI",
    "This first build follows the implementation plan by establishing the admin shell, a demo login gate, and interactive management pages backed by session-based mock data until the FastAPI endpoints are ready.",
    ["Streamlit multipage", "API-ready structure", "Session-backed demo data"],
)

left, right = st.columns([1.1, 1], gap="large")

with left:
    st.markdown("#### Sign in")
    st.caption("Use API credentials if `API_URL` is configured. Otherwise the demo credentials still work for the local prototype.")
    with st.form("admin-login"):
        email = st.text_input("Email", value=DEMO_ADMIN_EMAIL)
        password = st.text_input("Password", value=DEMO_ADMIN_PASSWORD, type="password")
        submitted = st.form_submit_button("Enter admin workspace", use_container_width=True)
    if submitted:
        ok, message = login_admin(email, password)
        if ok:
            st.success(message)
        else:
            st.error(message)

    st.markdown("#### Integration notes")
    st.markdown(
        "- Admin auth now follows the backend note: `POST /api/auth/login` then `GET /api/admin/dashboard` to validate admin access.\n"
        "- Pages use live endpoints where they already exist and fall back only for current API gaps.\n"
        "- Current missing admin routes from backend note: subscribers, site content, and full inactive-inclusive car list."
    )
    if not has_api():
        st.warning("Set `API_URL` in `.streamlit/secrets.toml` or the environment to switch from demo mode to live API mode.")

with right:
    metrics, source = get_dashboard_summary()
    metric_cols = st.columns(2)
    metric_cols[0].metric("Registered users", metrics["users"])
    metric_cols[1].metric("Cars", metrics.get("cars", metrics.get("active_cars", 0)))
    metric_cols[0].metric("Pending bookings", metrics["pending_bookings"])
    metric_cols[1].metric("Enquiries", metrics.get("enquiries", metrics.get("unread_enquiries", 0)))
    st.info(
        f"Dashboard source: `{source}`. Live mode uses the established backend route `GET /api/admin/dashboard`."
    )

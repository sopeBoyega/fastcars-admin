import streamlit as st

from shared.api import (
    dashboard_booking_status,
    dashboard_fleet_mix,
    dashboard_recent_bookings,
    get_dashboard_summary,
)
from shared.admin_ui import boot, page_header, require_admin_access, section_heading, stat_grid


boot("Dashboard")
require_admin_access("dashboard")

page_header(
    "Operations dashboard",
    "Overview",
    "A concise operating view for the team: key business signals, booking health, fleet mix, and the latest customer activity in one place.",
    ["Business health", "Booking flow", "Recent activity"],
)

metrics, source = get_dashboard_summary()
stat_grid(
    [
        ("Users", str(metrics["users"]), "Registered accounts"),
        ("Cars", str(metrics.get("cars", metrics.get("active_cars", 0))), "Available inventory"),
        ("Pending bookings", str(metrics["pending_bookings"]), "Needs review"),
        ("Subscribers", str(metrics.get("subscribers", 0)), source),
    ]
)

section_heading("Operational signals", "Quick visual reads on bookings and brand distribution.")
chart_left, chart_right = st.columns(2, gap="large")
with chart_left:
    st.markdown("#### Booking status")
    st.bar_chart(dashboard_booking_status().set_index("status"))
with chart_right:
    st.markdown("#### Fleet by brand")
    st.bar_chart(dashboard_fleet_mix().set_index("brand"))

section_heading("Recent bookings", "A readable queue of the latest activity coming into the business.")
st.dataframe(
    dashboard_recent_bookings().loc[:, ["booking_ref", "customer", "car_name", "status", "total_cost", "created_at"]],
    width="stretch",
    hide_index=True,
)

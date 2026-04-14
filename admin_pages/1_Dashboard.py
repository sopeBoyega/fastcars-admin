import streamlit as st

from shared.api import (
    dashboard_booking_status,
    dashboard_fleet_mix,
    dashboard_recent_bookings,
    get_dashboard_summary,
)
from shared.admin_ui import boot, page_header, require_admin_access


boot("Dashboard")
require_admin_access()

page_header(
    "Operations dashboard",
    "Module G",
    "This dashboard matches the implementation plan's first admin module: headline metrics, booking status distribution, fleet composition, and a recent bookings pulse for the team lead.",
    ["Counts", "Charts", "Recent activity"],
)

metrics, source = get_dashboard_summary()
cards = st.columns(4)
cards[0].metric("Users", metrics["users"], "+3 this week")
cards[1].metric("Cars", metrics.get("cars", metrics.get("active_cars", 0)))
cards[2].metric("Pending Bookings", metrics["pending_bookings"], "Needs review")
cards[3].metric("Subscribers", metrics.get("subscribers", 0), source)

chart_left, chart_right = st.columns(2, gap="large")
with chart_left:
    st.markdown("#### Booking status")
    st.bar_chart(dashboard_booking_status().set_index("status"))
with chart_right:
    st.markdown("#### Fleet by brand")
    st.bar_chart(dashboard_fleet_mix().set_index("brand"))

st.markdown("#### Recent bookings")
st.dataframe(
    dashboard_recent_bookings().loc[:, ["booking_ref", "customer", "car_name", "status", "total_cost", "created_at"]],
    use_container_width=True,
    hide_index=True,
)

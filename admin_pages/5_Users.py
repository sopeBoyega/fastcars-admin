import streamlit as st

from shared.api import get_bookings, get_users
from shared.admin_data import to_frame
from shared.admin_ui import boot, page_header, require_admin_access


boot("Users")
require_admin_access()

page_header(
    "User management",
    "Module J",
    "This page is shaped around the planned admin user listing endpoints, giving the team a place to inspect account health, contact details, and booking activity before real pagination is wired in.",
    ["Directory", "Profile drill-down", "Booking context"],
)

users, source = get_users()
users = [user for user in users if user.get("role") == "user"]
user_df = to_frame(users)

top = st.columns(3)
top[0].metric("Registered users", len(users))
top[1].metric("Active accounts", sum(1 for user in users if user.get("status", "active") == "active"))
top[2].metric("Dormant accounts", sum(1 for user in users if user.get("status", "active") != "active"))

selected_email = st.selectbox("Inspect user", user_df["email"].tolist())
selected_user = next(user for user in users if user["email"] == selected_email)

info, history = st.columns([0.95, 1.4], gap="large")
with info:
    st.markdown("#### Profile")
    st.write(f"**Name:** {selected_user['name']}")
    st.write(f"**Phone:** {selected_user['phone']}")
    st.write(f"**Role:** {selected_user['role']}")
    if "status" in selected_user:
        st.write(f"**Status:** {selected_user['status'].title()}")
    if "created_at" in selected_user:
        st.write(f"**Joined:** {str(selected_user['created_at'])[:10]}")

with history:
    bookings, _ = get_bookings()
    user_bookings = [booking for booking in bookings if booking.get("user_id") == selected_user.get("_id") or booking.get("customer") == selected_user["name"]]
    st.markdown("#### Booking history")
    history_df = to_frame(
        [
            {
                "booking_ref": item.get("booking_ref", item.get("_id")),
                "car_name": item.get("car_name", item.get("car_id")),
                "status": item.get("status"),
                "start_date": item.get("start_date"),
                "end_date": item.get("end_date"),
                "total_cost": item.get("total_cost", item.get("total_price", 0)),
            }
            for item in user_bookings
        ]
    )
    if history_df.empty:
        st.caption("No bookings recorded for this user yet.")
    else:
        st.dataframe(
            history_df.loc[:, ["booking_ref", "car_name", "status", "start_date", "end_date", "total_cost"]],
            use_container_width=True,
            hide_index=True,
        )

st.markdown("#### All users")
st.caption(f"Source: {source}. Live route: `GET /api/admin/users/`.")
st.dataframe(
    user_df.loc[:, [column for column in ["name", "email", "phone", "role", "status", "last_seen"] if column in user_df.columns]],
    use_container_width=True,
    hide_index=True,
)

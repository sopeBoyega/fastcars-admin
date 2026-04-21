import streamlit as st

from shared.api import cancel_booking, confirm_booking, get_booking_detail, get_bookings
from shared.admin_data import to_frame
from shared.admin_ui import boot, page_header, require_admin_access


boot("Bookings")
require_admin_access("bookings")

page_header(
    "Booking operations",
    "Module I",
    "The bookings workspace follows the implementation plan for admin confirmations and cancellations, with filtering, a review queue, and quick actions mapped to the future `PATCH /api/admin/bookings/{id}` endpoint.",
    ["Filter", "Confirm", "Cancel"],
)

all_bookings, source = get_bookings()
status_filter = st.selectbox("Filter by status", ["All", "pending", "confirmed", "cancelled"])
filtered = all_bookings if status_filter == "All" else [item for item in all_bookings if item["status"] == status_filter]

selector_labels = [f"{item['booking_ref']} • {item['customer']} • {item['status']}" for item in filtered]
selected_label = st.selectbox("Review booking", selector_labels) if selector_labels else None
selected = next((item for item in filtered if f"{item['booking_ref']} • {item['customer']} • {item['status']}" == selected_label), None)

if selected:
    detail, detail_source = get_booking_detail(selected["id"])
    detail = detail or selected
    a, b, c = st.columns(3)
    amount = detail.get("total_cost", 0)
    a.metric("Trip value", f"{amount:,}")
    b.metric("Travel window", f"{detail['start_date']} to {detail['end_date']}")
    c.metric("Current status", detail["status"].title())
    st.caption(f"Review source: {detail_source}. Detail route: `GET /api/admin/bookings/{{booking_id}}`.")
    info_left, info_right = st.columns(2)
    info_left.write(f"**Customer:** {detail.get('customer', 'Unknown')}")
    info_left.write(f"**Customer Email:** {detail.get('user_email', 'Not provided')}")
    info_right.write(f"**Car:** {detail.get('car_name', 'Unknown')}")
    info_right.write(f"**Total Days:** {detail.get('total_days', 'N/A')}")
    actions = st.columns(2)
    if actions[0].button("Confirm booking", width="stretch"):
        try:
            confirm_booking(selected["id"])
            st.success(f"{selected['booking_ref']} marked as confirmed.")
            st.rerun()
        except Exception as exc:
            st.error(f"Unable to confirm booking: {exc}")
    if actions[1].button("Cancel booking", width="stretch"):
        try:
            cancel_booking(selected["id"])
            st.success(f"{selected['booking_ref']} marked as cancelled.")
            st.rerun()
        except Exception as exc:
            st.error(f"Unable to cancel booking: {exc}")

queue = []
for item in filtered:
    queue.append(
        {
            "booking_ref": item.get("booking_ref"),
            "customer": item.get("customer"),
            "car_name": item.get("car_name"),
            "start_date": item.get("start_date"),
            "end_date": item.get("end_date"),
            "status": item.get("status"),
            "total_cost": item.get("total_cost", 0),
        }
    )
st.markdown("#### Booking queue")
st.caption(f"Source: {source}. Live routes: `GET /api/admin/bookings/`, `GET /api/admin/bookings/{{booking_id}}`, `PATCH /confirm`, `PATCH /cancel`.")
st.dataframe(
    to_frame(queue).loc[:, ["booking_ref", "customer", "car_name", "start_date", "end_date", "status", "total_cost"]],
    width="stretch",
    hide_index=True,
)

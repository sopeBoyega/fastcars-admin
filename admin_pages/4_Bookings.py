import streamlit as st

from shared.api import cancel_booking, confirm_booking, get_bookings
from shared.admin_data import to_frame
from shared.admin_ui import boot, page_header, require_admin_access


boot("Bookings")
require_admin_access()

page_header(
    "Booking operations",
    "Module I",
    "The bookings workspace follows the implementation plan for admin confirmations and cancellations, with filtering, a review queue, and quick actions mapped to the future `PATCH /api/admin/bookings/{id}` endpoint.",
    ["Filter", "Confirm", "Cancel"],
)

all_bookings, source = get_bookings()
status_filter = st.selectbox("Filter by status", ["All", "pending", "confirmed", "cancelled"])
filtered = all_bookings if status_filter == "All" else [item for item in all_bookings if item["status"] == status_filter]

selector_labels = [f"{item.get('booking_ref', item.get('_id', 'booking'))} • {item.get('customer', item.get('user_id', 'user'))} • {item['status']}" for item in filtered]
selected_label = st.selectbox("Review booking", selector_labels) if selector_labels else None
selected = next((item for item in filtered if f"{item.get('booking_ref', item.get('_id', 'booking'))} • {item.get('customer', item.get('user_id', 'user'))} • {item['status']}" == selected_label), None)

if selected:
    a, b, c = st.columns(3)
    amount = selected.get("total_cost", selected.get("total_price", 0))
    a.metric("Trip value", f"{amount:,}")
    b.metric("Travel window", f"{selected['start_date']} to {selected['end_date']}")
    c.metric("Current status", selected["status"].title())
    actions = st.columns(2)
    if actions[0].button("Confirm booking", use_container_width=True):
        try:
            confirm_booking(selected.get("id", selected.get("_id")))
            st.success(f"{selected.get('booking_ref', selected.get('_id'))} marked as confirmed.")
            st.rerun()
        except Exception as exc:
            st.error(f"Unable to confirm booking: {exc}")
    if actions[1].button("Cancel booking", use_container_width=True):
        try:
            cancel_booking(selected.get("id", selected.get("_id")))
            st.success(f"{selected.get('booking_ref', selected.get('_id'))} marked as cancelled.")
            st.rerun()
        except Exception as exc:
            st.error(f"Unable to cancel booking: {exc}")

queue = []
for item in filtered:
    queue.append(
        {
            "booking_ref": item.get("booking_ref", item.get("_id")),
            "customer": item.get("customer", item.get("user_id")),
            "car_name": item.get("car_name", item.get("car_id")),
            "start_date": item.get("start_date"),
            "end_date": item.get("end_date"),
            "status": item.get("status"),
            "total_cost": item.get("total_cost", item.get("total_price", 0)),
        }
    )
st.markdown("#### Booking queue")
st.caption(f"Source: {source}. Live routes: `GET /api/admin/bookings/`, `PATCH /confirm`, `PATCH /cancel`.")
st.dataframe(
    to_frame(queue).loc[:, ["booking_ref", "customer", "car_name", "start_date", "end_date", "status", "total_cost"]],
    use_container_width=True,
    hide_index=True,
)

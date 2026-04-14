import streamlit as st

from shared.api import get_testimonials, set_testimonial_active
from shared.admin_data import to_frame
from shared.admin_ui import boot, page_header, require_admin_access


boot("Testimonials")
require_admin_access()

page_header(
    "Testimonial moderation",
    "Module J",
    "The testimonial page lets the admin team approve or hide submissions, matching the document's moderation flow where new customer reviews stay inactive until reviewed.",
    ["Moderate", "Approve", "Hide"],
)

testimonials, source = get_testimonials()
labels = [
    f"{item['user_name']} • {'active' if item.get('is_active') or item.get('status') == 'active' else 'inactive'}"
    for item in testimonials
]
selected_label = st.selectbox("Select testimonial", labels)
selected = next(
    item
    for item in testimonials
    if f"{item['user_name']} • {'active' if item.get('is_active') or item.get('status') == 'active' else 'inactive'}" == selected_label
)

st.markdown("#### Review message")
st.info(selected["message"])

actions = st.columns(2)
if actions[0].button("Approve for public display", use_container_width=True):
    try:
        set_testimonial_active(selected.get("id", selected.get("_id")), True)
        st.success("Testimonial is now active.")
        st.rerun()
    except Exception as exc:
        st.error(f"Unable to update testimonial: {exc}")
if actions[1].button("Keep hidden", use_container_width=True):
    try:
        set_testimonial_active(selected.get("id", selected.get("_id")), False)
        st.success("Testimonial kept inactive.")
        st.rerun()
    except Exception as exc:
        st.error(f"Unable to update testimonial: {exc}")

queue = [
    {
        "user_name": item.get("user_name"),
        "status": "active" if item.get("is_active") or item.get("status") == "active" else "inactive",
        "created_at": item.get("created_at"),
    }
    for item in testimonials
]
st.markdown("#### Moderation queue")
st.caption(f"Source: {source}. Live routes: `GET /api/admin/testimonials/`, `PATCH /api/admin/testimonials/{{id}}`.")
st.dataframe(
    to_frame(queue).loc[:, ["user_name", "status", "created_at"]],
    use_container_width=True,
    hide_index=True,
)

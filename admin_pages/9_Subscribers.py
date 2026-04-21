import streamlit as st

from shared.api import get_subscribers, remove_subscriber
from shared.admin_data import to_frame
from shared.admin_ui import boot, page_header, require_admin_access


boot("Subscribers")
require_admin_access("enquiries")

page_header(
    "Subscriber management",
    "Module J",
    "This page turns newsletter contacts into a manageable audience list with segmentation and cleanup actions, matching the implementation plan's subscriber admin workflow.",
    ["Audience", "Segments", "Cleanup"],
)

subscribers, source = get_subscribers()
segments = ["All"] + sorted({subscriber.get("segment", "General") for subscriber in subscribers})
segment_filter = st.selectbox("Segment", segments)
filtered = subscribers if segment_filter == "All" else [item for item in subscribers if item.get("segment", "General") == segment_filter]

top = st.columns(3)
top[0].metric("Subscribers", len(subscribers))
top[1].metric("Filtered audience", len(filtered))
top[2].metric("Segments", len(set(subscriber.get("segment", "General") for subscriber in subscribers)))

labels = [f"{item['email']} • {item.get('segment', 'General')}" for item in filtered]
selected_label = st.selectbox("Select subscriber", labels) if labels else None
selected = next((item for item in filtered if f"{item['email']} • {item.get('segment', 'General')}" == selected_label), None)

if selected and st.button("Remove subscriber", width="stretch"):
    try:
        remove_subscriber(selected.get("id", selected.get("_id")))
        st.success(f"{selected['email']} removed from the audience.")
        st.rerun()
    except Exception as exc:
        st.error(f"Unable to remove subscriber: {exc}")

frame = to_frame(filtered)
st.markdown("#### Audience table")
st.caption(f"Source: {source}. Live routes: `GET /api/admin/subscribers`, `DELETE /api/admin/subscribers/{{id}}`.")
if frame.empty:
    st.caption("No subscribers match this segment yet.")
else:
    st.dataframe(
        frame.loc[:, [column for column in ["email", "segment", "created_at"] if column in frame.columns]],
        width="stretch",
        hide_index=True,
    )

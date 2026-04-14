import streamlit as st

from shared.admin_data import delete_subscriber, store, to_frame
from shared.admin_ui import boot, page_header, require_admin_access


boot("Subscribers")
require_admin_access()

page_header(
    "Subscriber management",
    "Module J",
    "This page turns newsletter contacts into a manageable audience list with segmentation and cleanup actions, matching the implementation plan's subscriber admin workflow.",
    ["Audience", "Segments", "Cleanup"],
)

st.info("The backend note says there is no admin subscriber list endpoint yet, so this page still uses local demo data until that route is delivered.")

subscribers = store()["subscribers"]
segments = ["All"] + sorted({subscriber["segment"] for subscriber in subscribers})
segment_filter = st.selectbox("Segment", segments)
filtered = subscribers if segment_filter == "All" else [item for item in subscribers if item["segment"] == segment_filter]

top = st.columns(3)
top[0].metric("Subscribers", len(subscribers))
top[1].metric("Filtered audience", len(filtered))
top[2].metric("Segments", len(set(subscriber["segment"] for subscriber in subscribers)))

labels = [f"{item['email']} • {item['segment']}" for item in filtered]
selected_label = st.selectbox("Select subscriber", labels) if labels else None
selected = next((item for item in filtered if f"{item['email']} • {item['segment']}" == selected_label), None)

if selected and st.button("Remove subscriber", use_container_width=True):
    delete_subscriber(selected["id"])
    st.success(f"{selected['email']} removed from the audience.")
    st.rerun()

frame = to_frame(filtered)
st.markdown("#### Audience table")
if frame.empty:
    st.caption("No subscribers match this segment yet.")
else:
    st.dataframe(
        frame.loc[:, ["email", "segment", "created_at"]],
        use_container_width=True,
        hide_index=True,
    )

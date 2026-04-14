import streamlit as st

from shared.api import delete_enquiry, get_enquiries
from shared.admin_data import to_frame
from shared.admin_ui import boot, page_header, require_admin_access


boot("Enquiries")
require_admin_access()

page_header(
    "Customer enquiries inbox",
    "Module J",
    "The enquiries page is organized like a lightweight support queue, ready to connect to `GET /api/admin/enquiries` and `PATCH /api/admin/enquiries/{id}` once the backend is available.",
    ["Inbox", "Unread filter", "Mark as read"],
)

enquiries, source = get_enquiries()
status_filter = st.radio("View", ["all", "recent"], horizontal=True)
if status_filter == "recent":
    enquiries = enquiries[:5]

labels = [f"{item['name']} • {str(item['created_at'])[:16]}" for item in enquiries]
selected_label = st.selectbox("Open enquiry", labels) if labels else None
selected = next((item for item in enquiries if f"{item['name']} • {str(item['created_at'])[:16]}" == selected_label), None)

if selected:
    st.markdown("#### Message")
    phone = selected.get("phone", "Not provided")
    st.write(f"**From:** {selected['name']}  \n**Email:** {selected['email']}  \n**Phone:** {phone}")
    st.info(selected["message"])
    if st.button("Delete after review", use_container_width=True):
        try:
            delete_enquiry(selected.get("id", selected.get("_id")))
            st.success("Enquiry deleted.")
            st.rerun()
        except Exception as exc:
            st.error(f"Unable to delete enquiry: {exc}")

frame = to_frame(enquiries)
st.markdown("#### Enquiry log")
st.caption(f"Source: {source}. Live routes: `GET /api/admin/enquiries`, `DELETE /api/admin/enquiries/{{id}}`.")
if frame.empty:
    st.caption("No enquiries in this view.")
else:
    st.dataframe(
        frame.loc[:, [column for column in ["name", "email", "phone", "created_at"] if column in frame.columns]],
        use_container_width=True,
        hide_index=True,
    )

import streamlit as st

from shared.api import delete_enquiry, get_enquiries, mark_enquiry_read
from shared.admin_data import to_frame
from shared.admin_ui import boot, page_header, require_admin_access


boot("Enquiries")
require_admin_access("enquiries")

page_header(
    "Customer enquiries inbox",
    "Module J",
    "The enquiries page is organized like a lightweight support queue, ready to connect to `GET /api/admin/enquiries` and `PATCH /api/admin/enquiries/{id}` once the backend is available.",
    ["Inbox", "Unread filter", "Mark as read"],
)

enquiries, source = get_enquiries()
status_filter = st.radio("View", ["all", "unread", "read"], horizontal=True)
if status_filter != "all":
    enquiries = [item for item in enquiries if item.get("status", "unread") == status_filter]

labels = [f"{item['name']} • {item.get('status', 'unread')} • {str(item['created_at'])[:16]}" for item in enquiries]
selected_label = st.selectbox("Open enquiry", labels) if labels else None
selected = next((item for item in enquiries if f"{item['name']} • {item.get('status', 'unread')} • {str(item['created_at'])[:16]}" == selected_label), None)

if selected:
    st.markdown("#### Message")
    phone = selected.get("phone", "Not provided")
    st.write(f"**From:** {selected['name']}  \n**Email:** {selected['email']}  \n**Phone:** {phone}")
    st.info(selected["message"])
    actions = st.columns(2)
    if selected.get("status", "unread") == "unread" and actions[0].button("Mark as read", width="stretch"):
        try:
            mark_enquiry_read(selected.get("id", selected.get("_id")))
            st.success("Enquiry marked as read.")
            st.rerun()
        except Exception as exc:
            st.error(f"Unable to update enquiry: {exc}")
    if actions[1].button("Delete after review", width="stretch"):
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
        frame.loc[:, [column for column in ["name", "email", "phone", "status", "created_at"] if column in frame.columns]],
        width="stretch",
        hide_index=True,
    )

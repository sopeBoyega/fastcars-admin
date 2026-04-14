import streamlit as st

from shared.admin_data import save_site_content, store
from shared.admin_ui import boot, page_header, require_admin_access


boot("Content")
require_admin_access()

page_header(
    "Editable site content",
    "Module J",
    "This content surface mirrors the `site_content` collection from the implementation plan, so the admin team can start shaping copy before the backend persistence layer lands.",
    ["CMS-lite", "Editable copy", "Site content keys"],
)

st.info("The backend note says site content admin endpoints are not available yet, so this page remains on local session-backed demo data for now.")

content = store()["site_content"]
selected_key = st.selectbox("Content key", list(content.keys()))

with st.form("content-update"):
    new_value = st.text_area("Value", value=content[selected_key], height=180)
    submitted = st.form_submit_button("Save content", use_container_width=True)
if submitted:
    save_site_content(selected_key, new_value)
    st.success(f"{selected_key} updated in the demo store.")

st.markdown("#### Current content map")
items = list(store()["site_content"].items())
for start in range(0, len(items), 2):
    row = st.columns(2)
    for column, (key, value) in zip(row, items[start : start + 2]):
        column.markdown(
            f"""
            <div class="fc-card">
                <div class="fc-eyebrow">{key}</div>
                <div class="fc-copy" style="margin-top:.45rem;">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

import streamlit as st

from shared.api import get_site_content, upsert_site_content
from shared.admin_ui import boot, page_header, require_admin_access


boot("Content")
require_admin_access("content")

page_header(
    "Editable site content",
    "Module J",
    "This content surface mirrors the `site_content` collection from the implementation plan, so the admin team can start shaping copy before the backend persistence layer lands.",
    ["CMS-lite", "Editable copy", "Site content keys"],
)

items, source = get_site_content()
content = {item.get("key"): item.get("value", "") for item in items if item.get("key")}
mode = st.radio("Key mode", ["Existing key", "Custom key"], horizontal=True)
selected_key = st.selectbox("Content key", list(content.keys())) if mode == "Existing key" else st.text_input("Custom content key", placeholder="homepage_hero")
current_value = content.get(selected_key, "")

with st.form("content-update"):
    new_value = st.text_area("Value", value=current_value, height=180)
    submitted = st.form_submit_button("Save content", width="stretch")
if submitted and selected_key.strip():
    try:
        payload, source = upsert_site_content(selected_key.strip(), new_value)
        st.success(f"{payload['key']} updated via {source} mode.")
        st.rerun()
    except Exception as exc:
        st.error(f"Unable to save content: {exc}")

st.markdown("#### Current content map")
content_items = list(content.items())
st.caption(f"Source: {source}. Live routes: `GET /api/admin/site-content`, `PATCH /api/admin/site-content/{{key}}`.")
for start in range(0, len(content_items), 2):
    row = st.columns(2)
    for column, (key, value) in zip(row, content_items[start : start + 2]):
        column.markdown(
            f"""
            <div class="fc-card">
                <div class="fc-eyebrow">{key}</div>
                <div class="fc-copy" style="margin-top:.45rem;">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

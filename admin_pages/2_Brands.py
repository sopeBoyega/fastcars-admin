import streamlit as st

from shared.api import create_brand, get_brands
from shared.admin_data import to_frame
from shared.admin_ui import boot, page_header, require_admin_access


boot("Brands")
require_admin_access("cars")

page_header(
    "Brand management",
    "Module H",
    "The brand page is set up for the `/api/admin/brands` resource: create brands, review positioning, and keep the fleet taxonomy clean before cars are added.",
    ["Create", "Review", "Feature flags"],
)

left, right = st.columns([0.95, 1.4], gap="large")
with left:
    st.markdown("#### Add a new brand")
    with st.form("brand-create", clear_on_submit=True):
        name = st.text_input("Brand name")
        logo_url = st.text_input("Logo URL", placeholder="https://...")
        save = st.form_submit_button("Save brand", width="stretch")
    if save and name:
        try:
            create_brand(name=name, logo_url=logo_url or None)
            st.success(f"{name} added to the brand library.")
            st.rerun()
        except Exception as exc:
            st.error(f"Unable to create brand: {exc}")

with right:
    brands, source = get_brands()
    brands_df = to_frame(brands).sort_values("created_at", ascending=False)
    st.markdown("#### Brand library")
    st.caption(f"Source: {source}. Live route: `GET /api/admin/cars/brands`.")
    st.data_editor(
        brands_df.loc[:, [column for column in ["name", "logo_url", "created_at"] if column in brands_df.columns]],
        width="stretch",
        hide_index=True,
        disabled=True,
    )

st.markdown("#### Featured brands")
featured_cols = st.columns(3)
featured = brands[:3]
for column, brand in zip(featured_cols, featured):
    column.markdown(
        f"""
        <div class="fc-card">
            <div class="fc-eyebrow">Brand</div>
            <div style="font-size:1.2rem;font-weight:700;margin:.35rem 0;">{brand['name']}</div>
            <div class="fc-copy">{brand.get('logo_url') or 'Logo pending or not provided.'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

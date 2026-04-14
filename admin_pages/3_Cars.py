import streamlit as st

from shared.api import create_car, get_brands, get_reference_cars
from shared.admin_data import to_frame
from shared.admin_ui import boot, page_header, require_admin_access


boot("Cars")
require_admin_access()

page_header(
    "Fleet inventory",
    "Module H",
    "This page gives the admin team a clean inventory cockpit for vehicle creation and review, mirroring the planned `/api/admin/cars` workflow with status, pricing, and merchandising signals.",
    ["Inventory", "Pricing", "Status control"],
)

filters = st.columns(3)
cars, car_source = get_reference_cars()
brands, _ = get_brands()
brand_options = ["All"] + sorted(
    {
        car.get("brand_name") or car.get("brand") or next(
            (brand["name"] for brand in brands if brand.get("id") == car.get("brand_id")),
            car.get("brand_id", "Unknown"),
        )
        for car in cars
    }
)
selected_brand = filters[0].selectbox("Brand", brand_options)
selected_status = filters[1].selectbox("Status", ["All", "active", "inactive"])
featured_only = filters[2].toggle("Featured only", value=False)

left, right = st.columns([1, 1.4], gap="large")
with left:
    st.markdown("#### Add car")
    with st.form("car-create", clear_on_submit=True):
        brand_map = {brand["name"]: brand.get("id") for brand in brands}
        brand = st.selectbox("Brand", list(brand_map.keys()) if brand_map else [""])
        name = st.text_input("Car name")
        category = st.selectbox("Category", ["Economy", "Premium", "SUV", "Luxury"])
        description = st.text_area("Description")
        daily_rate = st.number_input("Daily rate", min_value=50.0, step=5.0, value=150.0)
        seats = st.number_input("Seats", min_value=2, max_value=9, value=5)
        transmission = st.selectbox("Transmission", ["Automatic", "Manual"])
        fuel_type = st.selectbox("Fuel type", ["Petrol", "Diesel", "Electric", "Hybrid"])
        status = st.selectbox("Listing status", ["active", "inactive"])
        submitted = st.form_submit_button("Create car", use_container_width=True)
    if submitted and name and brand_map.get(brand):
        try:
            create_car(
                {
                    "brand_id": brand_map[brand],
                    "name": name,
                    "category": category,
                    "description": description,
                    "images": [],
                    "daily_rate": daily_rate,
                    "seats": int(seats),
                    "transmission": transmission,
                    "fuel_type": fuel_type,
                    "status": status,
                }
            )
            st.success(f"{name} has been added to the fleet list.")
            st.rerun()
        except Exception as exc:
            st.error(f"Unable to create car: {exc}")

normalized = []
for car in cars:
    brand_name = car.get("brand_name") or car.get("brand") or next(
        (brand["name"] for brand in brands if brand.get("id") == car.get("brand_id")),
        car.get("brand_id", "Unknown"),
    )
    normalized.append(
        {
            "brand": brand_name,
            "name": car.get("name"),
            "category": car.get("category"),
            "daily_rate": car.get("daily_rate"),
            "status": car.get("status", "active"),
            "featured": car.get("featured", False),
            "transmission": car.get("transmission"),
            "fuel_type": car.get("fuel_type"),
            "created_at": car.get("created_at"),
        }
    )
cars = normalized
if selected_brand != "All":
    cars = [car for car in cars if car["brand"] == selected_brand]
if selected_status != "All":
    cars = [car for car in cars if car["status"] == selected_status]
if featured_only:
    cars = [car for car in cars if car["featured"]]

with right:
    st.markdown("#### Fleet table")
    st.caption(f"Source: {car_source}. Live mode uses public `GET /api/cars/` because the backend note says the admin car list endpoint is still missing.")
    cars_df = to_frame(cars)
    st.dataframe(
        cars_df.loc[:, ["brand", "name", "category", "daily_rate", "status", "featured", "created_at"]],
        use_container_width=True,
        hide_index=True,
    )

st.markdown("#### Fleet spotlight")
spotlight_cols = st.columns(min(3, max(len(cars), 1)))
for column, car in zip(spotlight_cols, cars[:3]):
    column.markdown(
        f"""
        <div class="fc-card">
            <div class="fc-eyebrow">{car['brand']}</div>
            <div style="font-size:1.15rem;font-weight:700;margin:.35rem 0;">{car['name']}</div>
            <div class="fc-copy">{car['category']} • {car['transmission']} • {car['fuel_type']}</div>
            <div style="margin-top:.6rem;font-weight:700;">NGN {car['daily_rate']:,}/day</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

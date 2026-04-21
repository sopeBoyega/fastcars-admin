import streamlit as st

from shared.api import create_car, delete_car, get_admin_cars, get_brands, has_api, update_car, upload_car_images
from shared.admin_data import to_frame
from shared.admin_ui import boot, page_header, require_admin_access


def upload_selected_images(image_files: list[object]) -> list[str]:
    if not image_files:
        return []
    if has_api() and st.session_state.get("auth_mode") == "live":
        progress = st.progress(0, text="Uploading selected images...")
        uploaded_urls: list[str] = []
        files_to_upload = list(image_files)
        for index, file in enumerate(files_to_upload, start=1):
            uploaded_urls.extend(upload_car_images([file]))
            progress.progress(
                int(index / len(files_to_upload) * 100),
                text=f"Uploaded {index} of {len(files_to_upload)} image(s)",
            )
        progress.empty()
        return uploaded_urls
    return upload_car_images(list(image_files))


boot("Cars")
require_admin_access("cars")

page_header(
    "Fleet inventory",
    "Module H",
    "This page gives the admin team a clean inventory cockpit for vehicle creation and review, mirroring the planned `/api/admin/cars` workflow with status, pricing, and merchandising signals.",
    ["Inventory", "Pricing", "Status control"],
)

filters = st.columns(3)
all_cars, car_source = get_admin_cars()
brands, _ = get_brands()
brand_options = ["All"] + sorted(
    {
        car.get("brand_name") or car.get("brand") or next(
            (brand["name"] for brand in brands if brand.get("id") == car.get("brand_id")),
            car.get("brand_id", "Unknown"),
        )
        for car in all_cars
    }
)
selected_brand = filters[0].selectbox("Brand", brand_options)
selected_status = filters[1].selectbox("Status", ["All", "active", "inactive"])
featured_only = filters[2].toggle("Featured only", value=False)

left, middle, right = st.columns([1, 1, 1.2], gap="large")
brand_map = {brand["name"]: brand.get("id") for brand in brands}

with left:
    st.markdown("#### Add car")
    with st.form("car-create", clear_on_submit=True):
        brand = st.selectbox("Brand", list(brand_map.keys()) if brand_map else [""])
        name = st.text_input("Car name")
        category = st.selectbox("Category", ["Economy", "Premium", "SUV", "Luxury"])
        description = st.text_area("Description")
        daily_rate = st.number_input("Daily rate", min_value=50.0, step=5.0, value=150.0)
        seats = st.number_input("Seats", min_value=2, max_value=9, value=5)
        transmission = st.selectbox("Transmission", ["Automatic", "Manual"])
        fuel_type = st.selectbox("Fuel type", ["Petrol", "Diesel", "Electric", "Hybrid"])
        status = st.selectbox("Listing status", ["active", "inactive"])
        image_files = st.file_uploader(
            "Upload car images",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            help="Selected files are uploaded to the admin image endpoint before the car is saved.",
        )
        image_urls_text = st.text_area(
            "Or paste image URLs",
            placeholder="https://...\nhttps://...",
            help="Optional fallback if you already have hosted image URLs.",
        )
        submitted = st.form_submit_button("Create car", width="stretch")
    if submitted and name and brand_map.get(brand):
        try:
            trimmed_description = description.strip()
            if len(trimmed_description) < 10:
                raise ValueError("Description must be at least 10 characters long.")

            image_urls = [line.strip() for line in image_urls_text.splitlines() if line.strip()]
            if image_files:
                image_urls.extend(upload_selected_images(list(image_files)))

            create_car(
                {
                    "brand_id": brand_map[brand],
                    "name": name,
                    "category": category,
                    "description": trimmed_description,
                    "images": image_urls,
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

car_labels = [
    f"{car.get('name', 'Car')} • {car.get('status', 'unknown')} • {car.get('brand_name') or car.get('brand', 'Unknown')}"
    for car in all_cars
]
selected_car_label = None
selected_car = None
if car_labels:
    selected_car_label = middle.selectbox("Manage existing car", car_labels)
    selected_car = next(
        (
            car for car in all_cars
            if f"{car.get('name', 'Car')} • {car.get('status', 'unknown')} • {car.get('brand_name') or car.get('brand', 'Unknown')}" == selected_car_label
        ),
        None,
    )

with middle:
    st.markdown("#### Update or delete")
    if selected_car:
        current_brand = selected_car.get("brand_name") or selected_car.get("brand")
        current_brand_index = (
            list(brand_map.keys()).index(current_brand)
            if current_brand in brand_map
            else 0
        )
        current_category = selected_car.get("category", "Economy")
        current_transmission = selected_car.get("transmission", "Automatic")
        current_fuel_type = selected_car.get("fuel_type", "Petrol")
        current_status = selected_car.get("status", "active")
        existing_images = selected_car.get("images") or ([selected_car.get("image_url")] if selected_car.get("image_url") else [])

        with st.form("car-update"):
            edit_brand = st.selectbox("Brand", list(brand_map.keys()) if brand_map else [""], index=current_brand_index, key="edit_brand")
            edit_name = st.text_input("Car name", value=selected_car.get("name", ""), key="edit_name")
            edit_category = st.selectbox("Category", ["Economy", "Premium", "SUV", "Luxury"], index=["Economy", "Premium", "SUV", "Luxury"].index(current_category) if current_category in ["Economy", "Premium", "SUV", "Luxury"] else 0, key="edit_category")
            edit_description = st.text_area("Description", value=selected_car.get("description", ""), key="edit_description")
            edit_daily_rate = st.number_input("Daily rate", min_value=50.0, step=5.0, value=float(selected_car.get("daily_rate", 150.0)), key="edit_daily_rate")
            edit_seats = st.number_input("Seats", min_value=2, max_value=9, value=int(selected_car.get("seats", 5)), key="edit_seats")
            edit_transmission = st.selectbox("Transmission", ["Automatic", "Manual"], index=["Automatic", "Manual"].index(current_transmission) if current_transmission in ["Automatic", "Manual"] else 0, key="edit_transmission")
            edit_fuel_type = st.selectbox("Fuel type", ["Petrol", "Diesel", "Electric", "Hybrid"], index=["Petrol", "Diesel", "Electric", "Hybrid"].index(current_fuel_type) if current_fuel_type in ["Petrol", "Diesel", "Electric", "Hybrid"] else 0, key="edit_fuel_type")
            edit_status = st.selectbox("Listing status", ["active", "inactive"], index=["active", "inactive"].index(current_status) if current_status in ["active", "inactive"] else 0, key="edit_status")
            edit_image_files = st.file_uploader(
                "Upload additional car images",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                help="Selected files are uploaded first, then included in the car update payload.",
                key="edit_image_files",
            )
            edit_image_urls_text = st.text_area(
                "Image URLs",
                value="\n".join(existing_images),
                help="Edit the current image URL list or append more hosted image URLs.",
                key="edit_image_urls_text",
            )
            save_changes = st.form_submit_button("Save changes", width="stretch")
        if save_changes:
            try:
                trimmed_description = edit_description.strip()
                if len(trimmed_description) < 10:
                    raise ValueError("Description must be at least 10 characters long.")
                updated_image_urls = [line.strip() for line in edit_image_urls_text.splitlines() if line.strip()]
                if edit_image_files:
                    updated_image_urls.extend(upload_selected_images(list(edit_image_files)))
                update_car(
                    selected_car["id"],
                    {
                        "brand_id": brand_map[edit_brand],
                        "name": edit_name,
                        "category": edit_category,
                        "description": trimmed_description,
                        "images": updated_image_urls,
                        "daily_rate": edit_daily_rate,
                        "seats": int(edit_seats),
                        "transmission": edit_transmission,
                        "fuel_type": edit_fuel_type,
                        "status": edit_status,
                    },
                )
                st.success(f"{edit_name} updated successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Unable to update car: {exc}")

        if middle.button("Delete selected car", width="stretch", type="secondary"):
            try:
                delete_car(selected_car["id"])
                st.success(f"{selected_car.get('name', 'Car')} deleted.")
                st.rerun()
            except Exception as exc:
                st.error(f"Unable to delete car: {exc}")
    else:
        st.caption("No car selected yet.")

normalized = []
for car in all_cars:
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
            "id": car.get("id"),
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
    st.caption(f"Source: {car_source}. Live route: `GET /api/admin/cars/` now returns active and inactive cars with `brand_name`.")
    cars_df = to_frame(cars)
    st.dataframe(
        cars_df.loc[:, ["brand", "name", "category", "daily_rate", "status", "featured", "created_at"]],
        width="stretch",
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

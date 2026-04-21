import streamlit as st

from shared.admin_data import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD
from shared.api import get_dashboard_summary, has_api, login_admin
from shared.admin_ui import boot, page_header, render_sidebar, section_heading


def render_metric_cards(items: list[tuple[str, str, str]]) -> None:
    columns = st.columns(len(items))
    for column, (label, value, footnote) in zip(columns, items):
        with column:
            with st.container(border=True):
                st.caption(label)
                st.markdown(f"## {value}")
                st.write(footnote)


def render_feature_cards(items: list[tuple[str, str]], columns_per_row: int = 2) -> None:
    for start in range(0, len(items), columns_per_row):
        row = st.columns(columns_per_row)
        for column, (title, description) in zip(row, items[start : start + columns_per_row]):
            with column:
                with st.container(border=True):
                    st.markdown(f"#### {title}")
                    st.write(description)


def home_page() -> None:
    boot("Admin Home")
    render_sidebar("home")

    page_header(
        "Run daily operations with clarity",
        "FastCars Admin",
        "A calmer, more focused workspace for fleet updates, booking review, customer follow-up, and content changes without exposing technical complexity.",
        ["Focused workflow", "Clear actions", "Modern admin"],
    )

    metrics, source = get_dashboard_summary()
    render_metric_cards(
        [
            ("Registered users", str(metrics["users"]), "Customer accounts"),
            ("Cars", str(metrics.get("cars", metrics.get("active_cars", 0))), "Live inventory"),
            ("Pending bookings", str(metrics["pending_bookings"]), "Needs attention"),
            ("Enquiries", str(metrics.get("enquiries", metrics.get("unread_enquiries", 0))), source),
        ]
    )

    left, right = st.columns([1.1, 1], gap="large")

    with left:
        section_heading("Sign in", "Use your admin credentials to open the workspace.")
        st.caption("When `API_URL` is configured, sign in with backend admin credentials. Without it, the demo credentials below will work locally.")
        st.code(f"{DEMO_ADMIN_EMAIL}\n{DEMO_ADMIN_PASSWORD}", language=None)
        with st.form("admin-login"):
            email = st.text_input("Email", value=DEMO_ADMIN_EMAIL)
            password = st.text_input("Password", value=DEMO_ADMIN_PASSWORD, type="password")
            submitted = st.form_submit_button("Enter admin workspace", width="stretch")
        if submitted:
            ok, message = login_admin(email, password)
            if ok:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

        section_heading("How the workspace is organized", "The UI keeps the most common actions front and center.")
        render_feature_cards(
            [
                ("Overview first", "Start with a concise snapshot of bookings, inventory, and customer activity."),
                ("Task-based navigation", "Move through cars, bookings, messages, content, and reviews from one consistent sidebar."),
                ("Safer for non-technical staff", "The interface avoids route-heavy navigation and presents only meaningful admin tasks."),
            ],
        )
        if not has_api():
            st.warning("`API_URL` is not configured, so the app is running in demo mode.")

    with right:
        section_heading("What you can do here", "A streamlined admin surface for the work that happens every day.")
        render_feature_cards(
            [
                ("Update fleet availability", "Keep car details, pricing, and status aligned with the live business."),
                ("Review booking demand", "Catch pending requests quickly and move customers through the approval flow."),
                ("Respond to customers", "Stay on top of enquiries and testimonials without digging through internal pages."),
                ("Maintain the website", "Refresh marketing content from the same workspace used for operations."),
            ],
        )
        st.info(
            f"Dashboard source: `{source}`. Once signed in, the sidebar opens the main admin tasks."
        )


navigation = st.navigation(
    {
        "Workspace": [
            st.Page(home_page, title="Home", icon=":material/home:"),
            st.Page("admin_pages/1_Dashboard.py", title="Dashboard", icon=":material/dashboard:"),
            st.Page("admin_pages/2_Brands.py", title="Brands", icon=":material/branding_watermark:"),
            st.Page("admin_pages/3_Cars.py", title="Cars", icon=":material/directions_car:"),
            st.Page("admin_pages/4_Bookings.py", title="Bookings", icon=":material/event_note:"),
            st.Page("admin_pages/5_Users.py", title="Users", icon=":material/group:"),
            st.Page("admin_pages/6_Testimonials.py", title="Testimonials", icon=":material/star:"),
            st.Page("admin_pages/7_Content.py", title="Content", icon=":material/edit_note:"),
            st.Page("admin_pages/8_Enquiries.py", title="Enquiries", icon=":material/mail:"),
            st.Page("admin_pages/9_Subscribers.py", title="Subscribers", icon=":material/notifications_active:"),
        ]
    },
    position="sidebar",
)

navigation.run()

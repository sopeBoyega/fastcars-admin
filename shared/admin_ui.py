from __future__ import annotations

from typing import Iterable

import streamlit as st

from shared.admin_data import init_demo_state
from shared.api import has_api, logout_admin


def boot(page_title: str, icon: str = "🚘") -> None:
    st.set_page_config(
        page_title=f"{page_title} | FastCars Admin",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_demo_state()
    inject_theme()


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --fc-bg: #f6f3ed;
            --fc-panel: rgba(255, 255, 255, 0.8);
            --fc-ink: #1c1917;
            --fc-muted: #6b6259;
            --fc-accent: #b45309;
            --fc-accent-dark: #7c2d12;
            --fc-line: rgba(28, 25, 23, 0.10);
        }
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(180, 83, 9, 0.18), transparent 30%),
                radial-gradient(circle at left center, rgba(120, 53, 15, 0.12), transparent 25%),
                linear-gradient(180deg, #fcfbf8 0%, var(--fc-bg) 100%);
            color: var(--fc-ink);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #231815 0%, #3b2419 100%);
        }
        [data-testid="stSidebar"] * {
            color: #f8f4ef;
        }
        .fc-shell {
            padding: 1.1rem 1.3rem;
            border: 1px solid var(--fc-line);
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(255,255,255,0.88), rgba(255,255,255,0.74));
            box-shadow: 0 24px 60px rgba(28, 25, 23, 0.07);
            margin-bottom: 1rem;
        }
        .fc-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.72rem;
            color: var(--fc-accent-dark);
            font-weight: 700;
        }
        .fc-title {
            font-size: 2.2rem;
            line-height: 1.05;
            margin: 0.35rem 0 0.45rem;
            color: var(--fc-ink);
        }
        .fc-copy {
            font-size: 1rem;
            line-height: 1.7;
            color: var(--fc-muted);
            max-width: 64rem;
        }
        .fc-card {
            border: 1px solid var(--fc-line);
            border-radius: 22px;
            padding: 1rem 1.1rem;
            background: var(--fc-panel);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.45);
            margin-bottom: 1rem;
        }
        .fc-chip {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            margin-right: 0.45rem;
            margin-bottom: 0.4rem;
            background: rgba(180, 83, 9, 0.10);
            color: var(--fc-accent-dark);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        identity = st.session_state.admin_identity
        st.markdown("### FastCars Admin")
        st.caption("Premium fleet operations cockpit")
        mode = "Live API" if st.session_state.get("auth_mode") == "live" else "Demo data"
        api_state = get_api_caption()
        st.markdown(
            f"""
            <div class="fc-card">
                <div class="fc-eyebrow">Session</div>
                <div style="font-size:1.1rem;font-weight:700;margin:.35rem 0 .2rem;">{identity['name']}</div>
                <div style="color:#e7ddd4;font-size:.92rem;">{identity['role']} • {identity['email']}</div>
                <div style="color:#f6d7b0;font-size:.85rem;margin-top:.45rem;">{mode}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(api_state)
        st.caption("Planned API integrations")
        for label in (
            "GET /api/admin/dashboard",
            "GET /api/admin/brands",
            "GET /api/admin/cars",
            "PATCH /api/admin/bookings/{id}",
        ):
            st.markdown(f"- `{label}`")
        if st.session_state.admin_authenticated and st.button("Log out", use_container_width=True):
            logout_admin()
            st.rerun()


def page_header(title: str, eyebrow: str, description: str, chips: Iterable[str] | None = None) -> None:
    chip_markup = ""
    if chips:
        chip_markup = "".join([f'<span class="fc-chip">{chip}</span>' for chip in chips])
    st.markdown(
        f"""
        <div class="fc-shell">
            <div class="fc-eyebrow">{eyebrow}</div>
            <h1 class="fc-title">{title}</h1>
            <p class="fc-copy">{description}</p>
            <div>{chip_markup}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def require_admin_access() -> None:
    render_sidebar()
    if not st.session_state.admin_authenticated:
        st.warning("Sign in from the home page with the demo admin account to preview the admin interface.")
        st.stop()


def get_api_caption() -> str:
    if has_api():
        return f"API_URL configured: {st.secrets['API_URL'] if 'API_URL' in st.secrets else 'environment variable'}"
    return "No API_URL configured. Using local session data."

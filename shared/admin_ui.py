from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st

from shared.admin_data import init_demo_state
from shared.api import has_api, logout_admin


WORKSPACE_NAV = (
    ("dashboard", "Overview", "admin_pages/1_Dashboard.py"),
    ("cars", "Manage cars", "admin_pages/3_Cars.py"),
    ("bookings", "Bookings", "admin_pages/4_Bookings.py"),
    ("enquiries", "Customer messages", "admin_pages/8_Enquiries.py"),
    ("content", "Website content", "admin_pages/7_Content.py"),
    ("testimonials", "Reviews", "admin_pages/6_Testimonials.py"),
)


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
            --fc-bg: #f5f7fb;
            --fc-bg-accent: #eef3ff;
            --fc-surface: rgba(255, 255, 255, 0.88);
            --fc-surface-strong: #ffffff;
            --fc-sidebar: #0f172a;
            --fc-sidebar-muted: #94a3b8;
            --fc-ink: #0f172a;
            --fc-muted: #475569;
            --fc-subtle: #64748b;
            --fc-accent: #2563eb;
            --fc-accent-strong: #1d4ed8;
            --fc-accent-soft: rgba(37, 99, 235, 0.10);
            --fc-line: rgba(15, 23, 42, 0.08);
            --fc-line-strong: rgba(15, 23, 42, 0.14);
            --fc-shadow: 0 20px 48px rgba(15, 23, 42, 0.08);
            --fc-radius-lg: 24px;
            --fc-radius-md: 18px;
            --fc-radius-sm: 14px;
            --fc-info-bg: #eff6ff;
            --fc-info-text: #1d4ed8;
            --fc-success-bg: #ecfdf3;
            --fc-success-text: #047857;
            --fc-warn-bg: #fff7ed;
            --fc-warn-text: #c2410c;
            --fc-error-bg: #fef2f2;
            --fc-error-text: #b91c1c;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.10), transparent 28%),
                radial-gradient(circle at top right, rgba(15, 23, 42, 0.05), transparent 22%),
                linear-gradient(180deg, var(--fc-bg-accent) 0%, var(--fc-bg) 32%, #f8fafc 100%);
            color: var(--fc-ink);
        }
        .stApp, .stApp p, .stApp span, .stApp label, .stApp div, .stApp li {
            color: var(--fc-ink);
        }
        .block-container {
            max-width: 1240px;
            padding-top: 1.4rem;
            padding-bottom: 2.75rem;
        }
        [data-testid="stSidebar"] {
            background:
                radial-gradient(circle at top, rgba(37, 99, 235, 0.18), transparent 26%),
                linear-gradient(180deg, #0f172a 0%, #111827 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.12);
            min-width: 290px;
        }
        [data-testid="stSidebar"] * {
            color: #e2e8f0;
        }
        [data-testid="stSidebarNav"] {
            display: none;
        }
        [data-testid="collapsedControl"] {
            color: #cbd5e1;
        }
        [data-testid="stSidebarUserContent"] {
            padding-top: 0.8rem;
        }
        [data-testid="stSidebar"] .stButton > button {
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.14);
            min-height: 2.9rem;
            background: rgba(255, 255, 255, 0.04);
            color: #f8fafc;
            font-weight: 600;
            letter-spacing: -0.01em;
            transition: all 120ms ease;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            border-color: rgba(148, 163, 184, 0.26);
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-1px);
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: linear-gradient(180deg, #ffffff 0%, #dbeafe 100%);
            border-color: rgba(191, 219, 254, 0.6);
            color: #0f172a;
        }
        .fc-shell {
            padding: 1.6rem 1.7rem;
            border: 1px solid rgba(255, 255, 255, 0.66);
            border-radius: var(--fc-radius-lg);
            background:
                linear-gradient(180deg, rgba(255,255,255,0.94), rgba(255,255,255,0.86)),
                linear-gradient(135deg, rgba(37,99,235,0.08), transparent 45%);
            box-shadow: var(--fc-shadow);
            margin-bottom: 1.25rem;
            backdrop-filter: blur(16px);
        }
        .fc-shell-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.9fr);
            gap: 1.25rem;
            align-items: start;
        }
        .fc-shell-aside {
            padding: 1rem 1.05rem;
            border-radius: var(--fc-radius-md);
            border: 1px solid rgba(37, 99, 235, 0.10);
            background: linear-gradient(180deg, rgba(241, 245, 249, 0.72), rgba(255, 255, 255, 0.82));
        }
        .fc-shell-aside-label {
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: var(--fc-accent-strong);
            margin-bottom: 0.45rem;
        }
        .fc-shell-aside p {
            margin: 0;
            font-size: 0.94rem;
            line-height: 1.65;
            color: var(--fc-muted);
        }
        .fc-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.72rem;
            color: var(--fc-accent);
            font-weight: 700;
        }
        .fc-title {
            font-size: clamp(2rem, 2.7vw, 3rem);
            line-height: 1.02;
            letter-spacing: -0.04em;
            margin: 0.45rem 0 0.65rem;
            color: var(--fc-ink);
        }
        .fc-copy {
            font-size: 1rem;
            line-height: 1.75;
            color: var(--fc-muted);
            max-width: 56rem;
        }
        .fc-card {
            border: 1px solid var(--fc-line);
            border-radius: var(--fc-radius-md);
            padding: 1.1rem 1.15rem;
            background: var(--fc-surface);
            box-shadow: 0 10px 32px rgba(15, 23, 42, 0.05);
            margin-bottom: 1rem;
            backdrop-filter: blur(12px);
        }
        .fc-chip {
            display: inline-block;
            padding: 0.32rem 0.7rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            margin-right: 0.45rem;
            margin-bottom: 0.4rem;
            background: var(--fc-accent-soft);
            color: var(--fc-accent-strong);
        }
        .fc-brand {
            padding: 0.2rem 0 1rem;
            margin-bottom: 1.15rem;
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
        }
        .fc-brand-mark {
            width: 2.35rem;
            height: 2.35rem;
            border-radius: 0.9rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%);
            color: white;
            font-weight: 800;
            box-shadow: 0 14px 30px rgba(37, 99, 235, 0.35);
            margin-bottom: 0.85rem;
        }
        .fc-sidebar-card {
            border: 1px solid rgba(148, 163, 184, 0.12);
            background: rgba(255,255,255,0.04);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        }
        .fc-stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 0.9rem;
            margin: 1rem 0 1.2rem;
        }
        .fc-stat {
            border: 1px solid var(--fc-line);
            border-radius: var(--fc-radius-md);
            background:
                linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,255,255,0.88)),
                linear-gradient(135deg, rgba(37,99,235,0.05), transparent 55%);
            padding: 1rem 1.05rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        }
        .fc-stat-label {
            font-size: 0.82rem;
            font-weight: 600;
            letter-spacing: -0.01em;
            color: var(--fc-subtle);
            margin-bottom: 0.45rem;
        }
        .fc-stat-value {
            font-size: 1.7rem;
            line-height: 1;
            letter-spacing: -0.04em;
            font-weight: 700;
            color: var(--fc-ink);
        }
        .fc-stat-footnote {
            font-size: 0.82rem;
            color: var(--fc-muted);
            margin-top: 0.45rem;
        }
        .fc-feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.95rem;
            margin-top: 1rem;
        }
        .fc-feature {
            border: 1px solid var(--fc-line);
            border-radius: var(--fc-radius-md);
            background: rgba(255,255,255,0.74);
            padding: 1rem 1.05rem;
        }
        .fc-feature h4 {
            margin: 0 0 0.35rem 0;
            font-size: 1rem;
            letter-spacing: -0.02em;
        }
        .fc-feature p {
            margin: 0;
            font-size: 0.93rem;
            line-height: 1.65;
            color: var(--fc-muted);
        }
        .fc-section-heading {
            margin: 1.3rem 0 0.7rem;
        }
        .fc-section-heading h2 {
            font-size: 1.1rem;
            letter-spacing: -0.02em;
            margin: 0;
        }
        .fc-section-heading p {
            margin: 0.22rem 0 0;
            color: var(--fc-muted);
            font-size: 0.94rem;
        }
        .fc-panel {
            border: 1px solid var(--fc-line);
            border-radius: var(--fc-radius-md);
            background:
                linear-gradient(180deg, rgba(255,255,255,0.94), rgba(255,255,255,0.82)),
                linear-gradient(135deg, rgba(37,99,235,0.04), transparent 55%);
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
            padding: 1rem 1.05rem 1.1rem;
            margin-bottom: 1rem;
        }
        .fc-panel-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.85rem;
        }
        .fc-panel-header h3 {
            margin: 0;
            font-size: 1.02rem;
            letter-spacing: -0.02em;
        }
        .fc-panel-header p {
            margin: 0.22rem 0 0;
            color: var(--fc-muted);
            font-size: 0.92rem;
            line-height: 1.6;
        }
        .fc-panel-badge {
            padding: 0.28rem 0.58rem;
            border-radius: 999px;
            background: var(--fc-accent-soft);
            color: var(--fc-accent-strong);
            font-size: 0.76rem;
            font-weight: 700;
            white-space: nowrap;
        }
        .fc-stack {
            display: grid;
            gap: 1rem;
        }
        .fc-list {
            display: grid;
            gap: 0.8rem;
            margin-top: 0.6rem;
        }
        .fc-list-item {
            display: grid;
            grid-template-columns: 1.7rem minmax(0, 1fr);
            gap: 0.75rem;
            align-items: start;
        }
        .fc-list-dot {
            width: 1.7rem;
            height: 1.7rem;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: var(--fc-accent-soft);
            color: var(--fc-accent-strong);
            font-size: 0.82rem;
            font-weight: 700;
        }
        .fc-list-item h4 {
            margin: 0 0 0.12rem;
            font-size: 0.95rem;
            letter-spacing: -0.02em;
        }
        .fc-list-item p {
            margin: 0;
            color: var(--fc-muted);
            font-size: 0.9rem;
            line-height: 1.6;
        }
        h1, h2, h3, h4, h5, h6 {
            color: var(--fc-ink) !important;
            letter-spacing: -0.03em;
        }
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid var(--fc-line);
            border-radius: var(--fc-radius-md);
            padding: 1rem 1.05rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        }
        [data-testid="stMetricLabel"] p {
            color: var(--fc-muted) !important;
            font-weight: 600;
            letter-spacing: -0.01em;
        }
        [data-testid="stMetricValue"] {
            color: var(--fc-ink) !important;
        }
        [data-testid="stMetricDelta"] {
            color: var(--fc-accent-strong) !important;
        }
        [data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid var(--fc-line);
            border-radius: var(--fc-radius-md);
            padding: 1rem;
        }
        .stTextInput label,
        .stTextArea label,
        .stSelectbox label,
        .stNumberInput label,
        .stDateInput label,
        .stMultiSelect label,
        .stRadio label,
        .stToggle label {
            color: var(--fc-ink) !important;
            font-weight: 600;
        }
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        .stDateInput input {
            background: rgba(255, 255, 255, 0.96) !important;
            color: var(--fc-ink) !important;
            border: 1px solid var(--fc-line-strong) !important;
            border-radius: 12px !important;
        }
        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus,
        .stDateInput input:focus {
            border-color: rgba(37, 99, 235, 0.45) !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
        }
        .stSelectbox [data-baseweb="select"] > div,
        .stMultiSelect [data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.96) !important;
            color: var(--fc-ink) !important;
            border-color: var(--fc-line) !important;
            border-radius: 12px !important;
        }
        .stSelectbox [data-baseweb="select"] > div:focus-within,
        .stMultiSelect [data-baseweb="select"] > div:focus-within {
            border-color: rgba(37, 99, 235, 0.45) !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
        }
        .stButton > button,
        .stForm button[kind="primary"] {
            background: linear-gradient(180deg, var(--fc-accent) 0%, var(--fc-accent-strong) 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(37, 99, 235, 0.35) !important;
            border-radius: 12px !important;
            min-height: 2.8rem;
            font-weight: 600 !important;
            letter-spacing: -0.01em;
            box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
        }
        .stButton > button:hover,
        .stForm button[kind="primary"]:hover {
            background: linear-gradient(180deg, #3b82f6 0%, var(--fc-accent) 100%) !important;
            border-color: rgba(59, 130, 246, 0.45) !important;
            color: #ffffff !important;
            transform: translateY(-1px);
        }
        .stCode, code {
            color: var(--fc-ink) !important;
        }
        pre, .stCodeBlock, [data-testid="stCodeBlock"] {
            background: #f8fafc !important;
            color: var(--fc-ink) !important;
            border-radius: 16px !important;
            border: 1px solid var(--fc-line) !important;
        }
        [data-testid="stAlertContainer"] [data-testid="stMarkdownContainer"] p {
            font-weight: 600;
        }
        [data-testid="stAlert"][kind="info"] {
            background: var(--fc-info-bg);
            color: var(--fc-info-text);
        }
        [data-testid="stAlert"][kind="success"] {
            background: var(--fc-success-bg);
            color: var(--fc-success-text);
        }
        [data-testid="stAlert"][kind="warning"] {
            background: var(--fc-warn-bg);
            color: var(--fc-warn-text);
        }
        [data-testid="stAlert"][kind="error"] {
            background: var(--fc-error-bg);
            color: var(--fc-error-text);
        }
        [data-testid="stDataFrame"] {
            background: rgba(255, 255, 255, 0.82);
            border-radius: var(--fc-radius-md);
            border: 1px solid var(--fc-line);
            padding: 0.25rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        }
        [data-testid="stMarkdownContainer"] code {
            background: rgba(15, 23, 42, 0.06);
            color: var(--fc-accent-strong) !important;
            padding: 0.12rem 0.35rem;
            border-radius: 8px;
        }
        .stCaption {
            color: var(--fc-subtle) !important;
        }
        hr {
            border-color: var(--fc-line);
            margin: 1.25rem 0;
        }
        @media (max-width: 900px) {
            .fc-shell-grid {
                grid-template-columns: 1fr;
            }
            .block-container {
                padding-top: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(current_page: str = "home") -> None:
    with st.sidebar:
        identity = st.session_state.admin_identity
        st.markdown(
            """
            <div class="fc-brand">
                <div class="fc-brand-mark">F</div>
                <div style="font-size:1.05rem;font-weight:700;letter-spacing:-0.03em;">FastCars Admin</div>
                <div style="margin-top:.25rem;color:var(--fc-sidebar-muted);font-size:.92rem;line-height:1.55;">
                    Premium operations workspace for a small team that needs clarity, not complexity.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        mode = "Live API" if st.session_state.get("auth_mode") == "live" else "Demo data"
        api_state = get_api_caption()
        st.markdown(
            f"""
            <div class="fc-card fc-sidebar-card">
                <div class="fc-eyebrow" style="color:#93c5fd;">Account</div>
                <div style="font-size:1.08rem;font-weight:700;margin:.4rem 0 .16rem;letter-spacing:-0.02em;">{escape(identity['name'])}</div>
                <div style="color:#cbd5e1;font-size:.92rem;line-height:1.55;">{escape(identity['role'])} • {escape(identity['email'])}</div>
                <div style="color:#93c5fd;font-size:.85rem;margin-top:.55rem;">{mode}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(api_state)
        if st.session_state.admin_authenticated:
            st.markdown("#### Workspace")
            st.caption("Choose a task")
            for key, label, path in WORKSPACE_NAV:
                is_current = current_page == key
                if st.button(
                    label,
                    key=f"nav-{key}",
                    width="stretch",
                    type="primary" if is_current else "secondary",
                    disabled=is_current,
                ):
                    st.switch_page(path)
        else:
            st.info("Sign in from the home screen to open the admin workspace.")
        if st.session_state.admin_authenticated and st.button("Log out", width="stretch"):
            logout_admin()
            st.rerun()


def page_header(title: str, eyebrow: str, description: str, chips: Iterable[str] | None = None) -> None:
    chip_markup = ""
    if chips:
        chip_markup = "".join([f'<span class="fc-chip">{escape(chip)}</span>' for chip in chips])
    st.markdown(
        f"""
        <div class="fc-shell">
            <div class="fc-eyebrow">{escape(eyebrow)}</div>
            <h1 class="fc-title">{escape(title)}</h1>
            <p class="fc-copy">{escape(description)}</p>
            <div>{chip_markup}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero_header(
    title: str,
    eyebrow: str,
    description: str,
    chips: Iterable[str] | None = None,
    aside_title: str | None = None,
    aside_body: str | None = None,
) -> None:
    chip_markup = ""
    if chips:
        chip_markup = "".join([f'<span class="fc-chip">{escape(chip)}</span>' for chip in chips])
    aside_markup = ""
    if aside_title and aside_body:
        aside_markup = f"""
        <div class="fc-shell-aside">
            <div class="fc-shell-aside-label">{escape(aside_title)}</div>
            <p>{escape(aside_body)}</p>
        </div>
        """
    st.markdown(
        f"""
        <div class="fc-shell">
            <div class="fc-shell-grid">
                <div>
                    <div class="fc-eyebrow">{escape(eyebrow)}</div>
                    <h1 class="fc-title">{escape(title)}</h1>
                    <p class="fc-copy">{escape(description)}</p>
                    <div>{chip_markup}</div>
                </div>
                {aside_markup}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_heading(title: str, description: str | None = None) -> None:
    description_markup = f"<p>{escape(description)}</p>" if description else ""
    st.markdown(
        f"""
        <div class="fc-section-heading">
            <h2>{escape(title)}</h2>
            {description_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_grid(items: Iterable[tuple[str, str, str | None]]) -> None:
    cards = []
    for label, value, footnote in items:
        footnote_markup = f'<div class="fc-stat-footnote">{escape(footnote)}</div>' if footnote else ""
        cards.append(
            (
                f'<div class="fc-stat">'
                f'<div class="fc-stat-label">{escape(label)}</div>'
                f'<div class="fc-stat-value">{escape(value)}</div>'
                f"{footnote_markup}"
                f"</div>"
            )
        )
    st.markdown(f'<div class="fc-stat-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def feature_grid(items: Iterable[tuple[str, str]]) -> None:
    cards = [
        (
            f'<div class="fc-feature">'
            f"<h4>{escape(title)}</h4>"
            f"<p>{escape(description)}</p>"
            f"</div>"
        )
        for title, description in items
    ]
    st.markdown(f'<div class="fc-feature-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def panel_header(title: str, description: str | None = None, badge: str | None = None) -> None:
    badge_markup = f'<div class="fc-panel-badge">{escape(badge)}</div>' if badge else ""
    description_markup = f"<p>{escape(description)}</p>" if description else ""
    st.markdown(
        (
            f'<div class="fc-panel">'
            f'<div class="fc-panel-header">'
            f"<div>"
            f"<h3>{escape(title)}</h3>"
            f"{description_markup}"
            f"</div>"
            f"{badge_markup}"
            f"</div>"
            f"</div>"
        ),
        unsafe_allow_html=True,
    )


def checklist(items: Iterable[tuple[str, str]]) -> None:
    rows = []
    for index, (title, description) in enumerate(items, start=1):
        rows.append(
            (
                f'<div class="fc-list-item">'
                f'<div class="fc-list-dot">{index}</div>'
                f"<div>"
                f"<h4>{escape(title)}</h4>"
                f"<p>{escape(description)}</p>"
                f"</div>"
                f"</div>"
            )
        )
    st.markdown(f'<div class="fc-list">{"".join(rows)}</div>', unsafe_allow_html=True)


def require_admin_access(current_page: str) -> None:
    render_sidebar(current_page=current_page)
    if not st.session_state.admin_authenticated:
        st.warning("Sign in from the home page with the demo admin account to preview the admin interface.")
        st.stop()


def get_api_caption() -> str:
    if has_api():
        return f"API_URL configured: {st.secrets['API_URL'] if 'API_URL' in st.secrets else 'environment variable'}"
    return "No API_URL configured. Using local session data."

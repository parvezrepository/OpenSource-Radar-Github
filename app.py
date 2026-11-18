"""OpenSource Radar — AI-Powered Tech Intelligence & Content Discovery Platform.
Main Streamlit application entry point.
"""

import streamlit as st

from config import get_settings
from database.migrations import run_migrations
from database.repository_store import RepositoryStore
from utils.helpers import (
    inject_custom_css,
    render_editorial_hero,
    render_magnification_dock,
    render_repository_card,
    render_sidebar_status,
)

# Configure page layout
st.set_page_config(
    page_title="OpenSource Radar",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Global Editorial Design System
inject_custom_css()

# Run database migrations on startup (cached once per server lifetime)
@st.cache_resource
def _run_startup_migrations():
    try:
        run_migrations()
        return True
    except Exception as exc:
        return False

_run_startup_migrations()

# Sidebar Telemetry
render_sidebar_status()

# 1. Editorial Hero & Minimal Navigation (per design spec)
render_editorial_hero()

# 2. Bottom Content Grid (12-column layout per design spec)
col_left, col_mid, col_right = st.columns([5.5, 0.5, 6.0])

with col_left:
    st.markdown(
        """
        <div class="editorial-hero-sub">
            Autonomous technical intelligence engineered for builders, quants, and researchers.
            Continuous deep surveillance of emerging GitHub repositories before developer consensus.
        </div>
        <div class="editorial-lead-stat">
            <span class="status-dot"></span> BATCH 003 FILLING &bull; REAL-TIME SURVEILLANCE
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_right:
    with st.container(border=True):
        st.markdown(
            '<div style="font-size: 11px; font-weight: 700; color: #DC9F85; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px;">INTELLIGENCE PROTOCOL / DIRECT REPOSITORY SCAN</div>',
            unsafe_allow_html=True,
        )
        scan_input = st.text_input(
            "Repository or Access Token",
            placeholder="Search 500k+ repos (e.g. owner/repo) or enter email for invite...",
            label_visibility="collapsed",
            key="home_scan_input",
        )
        btn_col1, btn_col2 = st.columns([1.2, 1])
        with btn_col1:
            if st.button("🚀 SCAN & ANALYZE  →", type="primary", use_container_width=True, key="home_scan_btn"):
                if scan_input.strip():
                    st.session_state["selected_repo"] = scan_input.strip()
                    st.switch_page("pages/07_Repository_Analyzer.py")
                else:
                    st.warning("Enter a repository name (e.g. 'browser-use/browser-use') or topic to scan.")
        with btn_col2:
            if st.button("REQUEST INVITE  →", use_container_width=True, key="home_invite_btn"):
                if "@" in scan_input:
                    st.success(f"Access granted for {scan_input.strip()} (Batch 003 verified).")
                else:
                    st.info("Enter your email address in the field above to join Batch 003.")
        st.markdown(
            '<div style="color: #66473B; font-size: 11px; margin-top: 8px; letter-spacing: 0.5px;">Zero spam. Pure utility. Direct GitHub GraphQL telemetry.</div>',
            unsafe_allow_html=True,
        )

st.markdown('<hr style="border-color: #35211A; margin: 32px 0 24px 0;">', unsafe_allow_html=True)

# 3. Live Telemetry Metrics
st.markdown(
    '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">'
    '<div style="width: 14px; height: 2px; background-color: #DC9F85;"></div>'
    '<span style="font-size: 11px; font-weight: 700; color: #B6A596; letter-spacing: 1.2px; text-transform: uppercase;">PLATFORM TELEMETRY</span>'
    '</div>',
    unsafe_allow_html=True,
)

stats = RepositoryStore.get_overview_stats()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Discovered Repos", f"{stats['total_discovered']:,}")
with col2:
    st.metric("Bookmarked Projects", f"{stats['total_saved']:,}")
with col3:
    st.metric("Analyzed Projects", f"{stats['total_analyzed']:,}")
with col4:
    st.metric("Content Drafts", f"{stats['total_drafts']:,}")

st.markdown('<hr style="border-color: #35211A; margin: 28px 0 24px 0;">', unsafe_allow_html=True)

# 4. Structured Navigation Grid
st.markdown(
    '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">'
    '<div style="width: 14px; height: 2px; background-color: #DC9F85;"></div>'
    '<span style="font-size: 11px; font-weight: 700; color: #B6A596; letter-spacing: 1.2px; text-transform: uppercase;">MODULE DIRECTORY</span>'
    '</div>',
    unsafe_allow_html=True,
)

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    with st.container(border=True):
        st.markdown("#### 01 / DISCOVERY & RADARS")
        st.page_link("pages/01_Overview.py", label="01 Overview — Platform Health", icon="📊")
        st.page_link("pages/02_Discover.py", label="02 Discover — Deep Search Engine", icon="🔍")
        st.page_link("pages/03_Trending.py", label="03 Trending — Fast-Moving Tech", icon="📈")
        st.page_link("pages/04_Hidden_Gems.py", label="04 Hidden Gems — High-Ratio Repos", icon="✨")

with nav_col2:
    with st.container(border=True):
        st.markdown("#### 02 / CURATED INTELLIGENCE")
        st.page_link("pages/05_AI_Agents.py", label="05 AI & Agents — MCP & Autonomy", icon="🤖")
        st.page_link("pages/06_Trading_FinTech.py", label="06 Trading & FinTech — Quants", icon="💰")
        st.page_link("pages/07_Repository_Analyzer.py", label="07 Repo Analyzer — AI Dossier", icon="🔬")
        st.page_link("pages/08_Compare.py", label="08 Compare — Side-by-Side Matrix", icon="⚖️")

with nav_col3:
    with st.container(border=True):
        st.markdown("#### 03 / STUDIO & ANALYTICS")
        st.page_link("pages/09_Content_Studio.py", label="09 Content Studio — Draft Scripts", icon="✍️")
        st.page_link("pages/10_Saved_Projects.py", label="10 Saved Projects — Bookmarks", icon="🔖")
        st.page_link("pages/11_Analytics.py", label="11 Analytics — Historical Growth", icon="📉")
        st.page_link("pages/12_Settings.py", label="12 Settings — Telemetry Diagnostics", icon="⚙️")

# 5. Live Feed Preview
recent_repos = RepositoryStore.list_repositories(limit=3)
if recent_repos:
    st.markdown('<hr style="border-color: #35211A; margin: 28px 0 20px 0;">', unsafe_allow_html=True)
    st.markdown(
        '<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">'
        '<div style="display: flex; align-items: center; gap: 8px;">'
        '<div style="width: 14px; height: 2px; background-color: #DC9F85;"></div>'
        '<span style="font-size: 11px; font-weight: 700; color: #B6A596; letter-spacing: 1.2px; text-transform: uppercase;">LIVE TELEMETRY STREAM &bull; FEATURED CODEBASES</span>'
        '</div>'
        '<span style="font-size: 11px; color: #DC9F85; font-weight: 600;">STREAM ACTIVE</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    for repo in recent_repos:
        render_repository_card(repo, key_prefix="home")

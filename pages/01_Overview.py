"""Overview Dashboard — High-level platform metrics and operational status."""

import streamlit as st

from config import get_settings
from database.connection import check_db_health
from database.repository_store import RepositoryStore
from utils.helpers import render_page_header, render_sidebar_status

st.set_page_config(page_title="Overview — OpenSource Radar", page_icon="📊", layout="wide")
render_sidebar_status()

render_page_header(
    title="Executive Overview",
    subtitle="Platform telemetry, discovery statistics, and operational health.",
    icon="📊",
)

# Database-backed metrics
stats = RepositoryStore.get_overview_stats()
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="Discovered Repositories", value=f"{stats['total_discovered']:,}", help="Total repositories indexed in SQLite")
with col2:
    st.metric(label="Saved Projects", value=f"{stats['total_saved']:,}", help="Repositories bookmarked for research")
with col3:
    st.metric(label="Analyzed Projects", value=f"{stats['total_analyzed']:,}", help="Repositories with static or AI dossiers")
with col4:
    st.metric(label="Generated Drafts", value=f"{stats['total_drafts']:,}", help="Multi-platform content drafts created")
with col5:
    st.metric(label="Historical Snapshots", value=f"{stats.get('total_snapshots', 0):,}", help="Point-in-time observations for growth tracking")

st.markdown("### 🔌 System Infrastructure Status")
s1, s2, s3 = st.columns(3)

settings = get_settings()

with s1:
    with st.container(border=True):
        st.markdown("#### 🐙 GitHub Connection")
        if settings.has_github_token:
            st.success("Authenticated PAT Active")
            st.caption(f"Token: `{settings.masked_github_token}`")
            st.caption("Rate Limit Quota: 5,000 req/hr")
        else:
            st.warning("Public Mode (Unauthenticated)")
            st.caption("Rate Limit Quota: 60 req/hr")
            st.caption("Configure `GITHUB_TOKEN` in `.env` for production usage.")

with s2:
    with st.container(border=True):
        st.markdown("#### 🤖 AI Engine Status")
        if settings.AI_PROVIDER == "openai":
            if settings.has_openai_credentials:
                st.success(f"OpenAI Active ({settings.OPENAI_MODEL})")
                st.caption(f"Key: `{settings.masked_openai_key}`")
            else:
                st.info("OpenAI Configured (No Key)")
                st.caption("Static deterministic fallback enabled.")
        elif settings.AI_PROVIDER == "gemini":
            if settings.has_gemini_credentials:
                st.success(f"Google Gemini Active ({settings.GEMINI_MODEL})")
                st.caption(f"Key: `{settings.masked_gemini_key}`")
            else:
                st.info("Gemini Configured (No Key)")
                st.caption("Static deterministic fallback enabled.")
        else:
            st.info("AI Provider: Offline / None")
            st.caption("Operating in deterministic static analysis mode.")

with s3:
    with st.container(border=True):
        st.markdown("#### 🗄️ Database Status")
        db_health = check_db_health()
        if db_health.get("connected"):
            st.success("SQLite Connected")
            st.caption("WAL Mode: Enabled")
            st.caption(f"Storage: `{settings.DATABASE_URL}`")
        else:
            st.error("Database Connection Failed")
            st.caption(db_health.get("error", "Unknown error"))

st.markdown("### 🕒 Recent Discovery Activity")
recent_repos = stats["recent_repositories"]

if not recent_repos:
    st.info("No repositories have been discovered yet. Use **02 Discover** to run your first GitHub search.")
else:
    for repo in recent_repos:
        with st.container(border=True):
            r_col1, r_col2, r_col3 = st.columns([3, 1, 1])
            with r_col1:
                st.markdown(f"**[{repo.full_name}]({repo.html_url})**")
                st.caption(repo.description or "No description provided.")
            with r_col2:
                st.write(f"⭐ **{repo.stars:,}** | 🍴 **{repo.forks:,}**")
                st.caption(f"Lang: {repo.primary_language or 'Unknown'}")
            with r_col3:
                scraped_str = repo.last_scraped_at.strftime("%Y-%m-%d %H:%M") if repo.last_scraped_at else "N/A"
                st.caption(f"Scraped: {scraped_str}")

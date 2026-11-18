"""Settings & Diagnostics — Application configuration, rate limits, and API testing."""

import streamlit as st

from config import get_settings
from core.cache import global_cache
from core.github_client import get_github_client
from database.connection import check_db_health
from utils.helpers import render_page_header, render_sidebar_status

st.set_page_config(page_title="Settings — OpenSource Radar", page_icon="⚙️", layout="wide")
render_sidebar_status()

render_page_header(
    title="Settings & System Diagnostics",
    subtitle="Inspect API connections, rate limits, persistence layers, and cache state.",
    icon="⚙️",
)

settings = get_settings()

from scheduler import PID_FILE, is_pid_running

tab_github, tab_ai, tab_db, tab_cache, tab_automation = st.tabs([
    "🐙 GitHub Integration",
    "🤖 AI Providers",
    "🗄️ Database & Storage",
    "⚡ Cache & Memory",
    "⏱️ Automation & Notifications",
])

# ----------------- Tab 1: GitHub Integration -----------------
with tab_github:
    st.markdown("### GitHub REST API Diagnostics")
    gh_col1, gh_col2 = st.columns(2)

    with gh_col1:
        st.write(f"**API Base URL**: `{settings.GITHUB_API_BASE}`")
        st.write(f"**Token Configured**: `{'Yes' if settings.has_github_token else 'No (Public Mode)'}`")
        st.write(f"**Masked Token**: `{settings.masked_github_token}`")
        st.write(f"**Timeout**: `{settings.GITHUB_REQUEST_TIMEOUT}s` | **Max Retries**: `{settings.GITHUB_MAX_RETRIES}`")

    with gh_col2:
        if st.button("🧪 Test GitHub Connection", type="primary"):
            client = get_github_client()
            with st.spinner("Connecting to GitHub REST API..."):
                test_res = client.test_connection()
            
            if test_res.get("status") in ["connected", "connected_unauthenticated"]:
                if test_res.get("authenticated"):
                    st.success(f"Connected as **{test_res.get('username')}** ({test_res.get('name')})")
                else:
                    st.warning(f"Connected in public mode. {test_res.get('warning', '')}")
                
                # Show rate limit stats
                rate_limit = test_res.get("rate_limit", {})
                rem = rate_limit.get("remaining", "N/A")
                limit = rate_limit.get("limit", "N/A")
                reset_sec = rate_limit.get("seconds_until_reset", "N/A")
                st.metric("Rate Limit Quota Remaining", f"{rem} / {limit}", delta=f"Resets in {reset_sec}s")
            else:
                st.error(f"Connection Failed: {test_res.get('error', 'Unknown error')}")

    st.markdown("---")
    st.markdown("#### Real-time Rate Limit Metrics")
    client = get_github_client()
    rate_info = client.rate_limiter.to_dict()
    rc1, rc2, rc3, rc4 = st.columns(4)
    with rc1:
        st.metric("Quota Limit", rate_info["limit"])
    with rc2:
        st.metric("Calls Remaining", rate_info["remaining"])
    with rc3:
        st.metric("Seconds Until Reset", f"{rate_info['seconds_until_reset']}s")
    with rc4:
        st.metric("Capacity", f"{rate_info['percent_remaining']}%")

# ----------------- Tab 2: AI Providers -----------------
with tab_ai:
    st.markdown("### AI Provider Configuration")
    ai_col1, ai_col2 = st.columns(2)

    with ai_col1:
        st.markdown("#### Primary AI Engine")
        st.write(f"**Configured Provider**: `{settings.AI_PROVIDER}`")
        if settings.AI_PROVIDER == "openai":
            st.write(f"**OpenAI Model**: `{settings.OPENAI_MODEL}`")
            st.write(f"**API Key**: `{settings.masked_openai_key}`")
            if settings.has_openai_credentials:
                st.success("OpenAI credentials configured.")
            else:
                st.info("No OpenAI API key provided. Falling back to deterministic static analysis.")
        elif settings.AI_PROVIDER == "gemini":
            st.write(f"**Gemini Model**: `{settings.GEMINI_MODEL}`")
            st.write(f"**API Key**: `{settings.masked_gemini_key}`")
            if settings.has_gemini_credentials:
                st.success("Google Gemini credentials configured.")
            else:
                st.info("No Gemini API key provided. Falling back to deterministic static analysis.")
        else:
            st.info("AI Provider disabled. Static analysis active.")

    with ai_col2:
        st.info("""
        **Security & Credential Policy**:
        - Raw API keys are never stored in database records or logged.
        - The platform functions completely without AI credentials by providing static rule-based analysis.
        - When active, all repository inputs are strictly isolated to defend against prompt injection.
        """)

# ----------------- Tab 3: Database & Storage -----------------
with tab_db:
    st.markdown("### Database Health & Configuration")
    health = check_db_health()

    if health.get("connected"):
        st.success("✅ Database is reachable and healthy.")
    else:
        st.error(f"❌ Database error: {health.get('error')}")

    st.write(f"**Database URL**: `{health.get('url')}`")
    st.write("**Engine**: SQLite with Write-Ahead Logging (WAL) and foreign key constraints enabled.")

# ----------------- Tab 4: Cache & Memory -----------------
with tab_cache:
    st.markdown("### Cache Management")
    c_size = global_cache.size()
    st.metric("Cached API Queries", c_size)

    if st.button("🗑️ Clear Cache", type="secondary"):
        global_cache.clear()
        st.success("In-memory cache cleared successfully.")
        st.rerun()

# ----------------- Tab 5: Automation & Notifications -----------------
with tab_automation:
    st.markdown("### Background Scheduler & Notification Diagnostics")
    
    # Scheduler PID Check
    sched_running = False
    sched_pid = None
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            if is_pid_running(pid):
                sched_running = True
                sched_pid = pid
        except Exception:
            pass

    auto_col1, auto_col2 = st.columns(2)
    with auto_col1:
        st.markdown("#### Background Daemon Status")
        if sched_running:
            st.success(f"🟢 **Scheduler Running** (PID: `{sched_pid}`)")
        else:
            st.warning("⚪ **Scheduler Stopped**")
        st.code("python scheduler.py", language="bash")
        st.caption("Launch in an isolated terminal or background process to run automated discovery jobs.")

    with auto_col2:
        st.markdown("#### Notification Channel Settings")
        st.write("- **Application Log**: `ACTIVE` (`logs/monitoring.log`)")
        st.write(f"- **Telegram Bot**: `{'CONFIGURED' if settings.has_telegram_credentials else 'NOT CONFIGURED'}`")
        if settings.has_telegram_credentials:
            st.write(f"  - Bot Token: `{settings.masked_telegram_token}`")
            st.write(f"  - Chat ID: `{settings.TELEGRAM_CHAT_ID}`")
            st.write(f"  - Alert Threshold: `Score >= {settings.TELEGRAM_ALERT_SCORE_THRESHOLD}`")

            from services.telegram_service import telegram_service
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                if st.button("🧪 Test Telegram Bot", key="test_telegram_btn"):
                    with st.spinner("Connecting to Telegram Bot API..."):
                        t_res = telegram_service.test_connection()
                    if t_res.get("status") == "connected":
                        st.success(f"Connected! Bot: **@{t_res.get('bot_username')}** (Ping sent)")
                    else:
                        st.error(f"Telegram Error: {t_res.get('error')}")
            with t_col2:
                if st.button("📢 Send Sample Alert", key="sample_telegram_alert_btn"):
                    with st.spinner("Dispatching sample alert..."):
                        sample_repo = {
                            "full_name": "Significant-Gravitas/AutoGPT",
                            "html_url": "https://github.com/Significant-Gravitas/AutoGPT",
                            "stars": 169000,
                            "forks": 42000,
                            "primary_language": "Python",
                            "description": "AutoGPT is the vision of accessible AI for everyone, to use and to build upon.",
                            "topics": ["ai-agents", "autonomous", "llm"],
                        }
                        sample_score = {"total_score": 88}
                        sent = telegram_service.send_repository_alert(sample_repo, sample_score, reason="Trending High Velocity")
                    if sent:
                        st.success("Sample alert delivered to Telegram!")
                    else:
                        st.error("Failed to send sample alert. Check logs.")
        else:
            st.info("💡 **Setup Telegram Mobile Alerts**:\n1. In Telegram, message `@BotFather` to create a bot & copy the **HTTP API Token**.\n2. Message `@userinfobot` to get your personal **Chat ID**.\n3. Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` to `.env`.")

"""Trend Analytics — Historical star tracking, trajectory analysis, and scheduler management."""

from datetime import datetime, timezone
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import desc, func, select

from config import BASE_DIR, get_settings
from core.trend_tracker import trend_tracker
from database.connection import get_db
from database.models import Category, DiscoveryJob, DiscoveryLog, Repository, RepositoryAnalysis, RepositorySnapshot
from database.repository_store import RepositoryStore
from scheduler import PID_FILE, is_pid_running
from services.monitoring_service import NotificationEvent, monitoring_service
from services.scheduler_service import scheduler_service
from utils.helpers import render_page_header, render_sidebar_status

st.set_page_config(page_title="Analytics — OpenSource Radar", page_icon="📈", layout="wide")
render_sidebar_status()

render_page_header(
    title="Historical Growth & Trend Analytics",
    subtitle="Measured velocity, star growth rates, historical trajectory comparisons, and scheduled jobs.",
    icon="📈",
)

st.markdown("""
> [!NOTE]
> **Data Integrity Non-Negotiable**: Historical growth is computed strictly from verified, timestamped snapshot observations.
> Growth metrics and trajectories are never fabricated from single point-in-time totals.
""")

# Top Overview Telemetry
overview_stats = RepositoryStore.get_overview_stats()
total_snapshots = RepositoryStore.get_snapshots_count()
jobs_list = scheduler_service.list_jobs()
active_jobs_count = sum(1 for j in jobs_list if j["is_enabled"])

# Determine background scheduler process status
scheduler_is_running = False
scheduler_pid = None
if PID_FILE.exists():
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        if is_pid_running(pid):
            scheduler_is_running = True
            scheduler_pid = pid
    except Exception:
        pass

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Tracked Repositories", f"{overview_stats['total_discovered']:,}")
with m2:
    st.metric("Historical Snapshots", f"{total_snapshots:,}")
with m3:
    st.metric("Configured Discovery Jobs", f"{len(jobs_list)} ({active_jobs_count} active)")
with m4:
    if scheduler_is_running:
        st.metric("Background Scheduler", "🟢 RUNNING", help=f"Process PID: {scheduler_pid}")
    else:
        st.metric("Background Scheduler", "⚪ STOPPED", help="Run 'python scheduler.py' in a separate terminal.")

tab_trajectory, tab_ecosystem, tab_jobs, tab_alerts = st.tabs([
    "📈 Historical Trajectory & Star Growth",
    "🌐 Discovery Ecosystem Analytics",
    "⏱️ Scheduled Discovery Jobs & Logs",
    "📢 Monitoring Alerts",
])

# ----------------- Tab 1: Historical Trajectory & Star Growth -----------------
with tab_trajectory:
    st.markdown("### 📊 Repository Point-in-Time Growth Trajectory")

    # Fetch repositories for dropdown
    repos_with_snapshots = RepositoryStore.get_repositories_with_snapshots()

    if not repos_with_snapshots:
        with get_db() as s:
            all_repos = list(s.execute(select(Repository).order_by(desc(Repository.stars)).limit(50)).scalars().all())
    else:
        all_repos = repos_with_snapshots

    if not all_repos:
        st.info("No repositories currently found in database. Run discovery in Discover or Trending pages first.")
    else:
        col_sel, col_action = st.columns([3, 1])
        with col_sel:
            repo_options = {f"{r.full_name} ({r.stars:,} ⭐)": r.id for r in all_repos}
            selected_label = st.selectbox("Select Repository to Inspect Growth", options=list(repo_options.keys()))
            selected_repo_id = repo_options[selected_label]
            selected_repo = next((r for r in all_repos if r.id == selected_repo_id), None)

        with col_action:
            st.write("")
            st.write("")
            if st.button("📸 Capture Snapshot Now", use_container_width=True, help="Force-record a new observation right now"):
                if selected_repo:
                    snap = trend_tracker.record_snapshot(
                        repository_id=selected_repo.id,
                        stars=selected_repo.stars,
                        forks=selected_repo.forks,
                        open_issues=selected_repo.open_issues,
                        force=True,
                    )
                    st.success(f"Snapshot recorded at {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}.")
                    st.rerun()

        if selected_repo:
            growth = trend_tracker.calculate_growth(selected_repo.id)

            if not growth.get("has_sufficient_data"):
                st.warning(
                    f"⚠️ **Insufficient Historical Data**: Only **{growth.get('total_snapshots', 0)}** snapshot observation(s) "
                    f"recorded for `{selected_repo.full_name}`.\n\n"
                    f"Calculating verified 24-hour, 7-day, or 30-day velocity requires at least **2 distinct snapshot observations** "
                    f"taken over time. Click **'Capture Snapshot Now'** above to record additional points or keep the background scheduler running."
                )
            else:
                st.success(f"✅ Verified growth computed across **{growth['total_snapshots']}** observations.")
                
                # Growth Metrics Row
                g1, g2, g3, g4 = st.columns(4)
                
                with g1:
                    g24 = growth.get("growth_24h")
                    if g24 and g24.get("available"):
                        st.metric(
                            "Observed 24h Growth",
                            f"{g24['delta_stars']:+d} ⭐",
                            f"{g24['growth_percent']:+.2f}%",
                            help=f"Over {g24['hours_elapsed']} observed hours",
                        )
                    else:
                        st.metric("Observed 24h Growth", "Insufficient Data", help="No baseline snapshot within 18h-36h window")

                with g2:
                    g7 = growth.get("growth_7d")
                    if g7 and g7.get("available"):
                        st.metric(
                            "Observed 7d Growth",
                            f"{g7['delta_stars']:+d} ⭐",
                            f"{g7['growth_percent']:+.2f}%",
                            help=f"Over {g7['hours_elapsed']} observed hours",
                        )
                    else:
                        st.metric("Observed 7d Growth", "Insufficient Data", help="No baseline snapshot within 5d-9d window")

                with g3:
                    g30 = growth.get("growth_30d")
                    if g30 and g30.get("available"):
                        st.metric(
                            "Observed 30d Growth",
                            f"{g30['delta_stars']:+d} ⭐",
                            f"{g30['growth_percent']:+.2f}%",
                            help=f"Over {g30['hours_elapsed']} observed hours",
                        )
                    else:
                        st.metric("Observed 30d Growth", "Insufficient Data", help="No baseline snapshot within 25d-35d window")

                with g4:
                    tot = growth.get("total_observed_growth")
                    if tot:
                        st.metric(
                            "Total Observed Delta",
                            f"{tot['delta_stars']:+d} ⭐",
                            f"{tot['growth_percent']:+.2f}%",
                            help=f"Over {tot['hours_elapsed']} total hours",
                        )

                # Plotly Time-Series Chart
                series_data = trend_tracker.get_time_series(selected_repo.id)
                if series_data:
                    df_series = pd.DataFrame(series_data)
                    df_series["recorded_at"] = pd.to_datetime(df_series["recorded_at"])

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_series["recorded_at"],
                        y=df_series["stars"],
                        mode="lines+markers",
                        name="Stars ⭐",
                        line=dict(color="#FF4B4B", width=3),
                        marker=dict(size=7),
                    ))
                    fig.add_trace(go.Scatter(
                        x=df_series["recorded_at"],
                        y=df_series["forks"],
                        mode="lines+markers",
                        name="Forks 🍴",
                        line=dict(color="#00D26A", width=2, dash="dot"),
                        marker=dict(size=5),
                    ))
                    fig.update_layout(
                        title=f"Star & Fork Growth History: {selected_repo.full_name}",
                        xaxis_title="Recorded Timestamp (UTC)",
                        yaxis_title="Count",
                        template="plotly_dark",
                        hovermode="x unified",
                        height=420,
                        margin=dict(l=20, r=20, t=50, b=20),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    with st.expander("🔍 View Raw Observation Snapshots"):
                        st.dataframe(df_series, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🚀 Measured High-Velocity Repositories")
    high_velocity = trend_tracker.get_high_velocity_repositories(limit=10)
    if not high_velocity:
        st.info("No high-velocity leaderboards available yet. Requires multiple snapshot observations across repositories.")
    else:
        df_hv = pd.DataFrame(high_velocity)
        st.dataframe(
            df_hv.rename(columns={
                "full_name": "Repository",
                "current_stars": "Current Stars",
                "delta_stars": "Observed Star Delta",
                "growth_percent": "Growth %",
                "hours_elapsed": "Time Elapsed (Hours)",
                "snapshots_count": "Snapshots Count",
            }),
            use_container_width=True,
        )

# ----------------- Tab 2: Discovery Ecosystem Analytics -----------------
with tab_ecosystem:
    st.markdown("### 🌐 Global OpenSource Radar Ecosystem")
    c_cat, c_lang = st.columns(2)

    with c_cat:
        cat_dist = RepositoryStore.get_category_distribution()
        if cat_dist:
            df_cat = pd.DataFrame(list(cat_dist.items()), columns=["Category", "Count"])
            fig_cat = px.pie(
                df_cat,
                names="Category",
                values="Count",
                title="Repository Distribution by Category",
                hole=0.4,
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
            fig_cat.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("No categorized repositories yet.")

    with c_lang:
        lang_dist = RepositoryStore.get_language_distribution(limit=8)
        if lang_dist:
            df_lang = pd.DataFrame(list(lang_dist.items()), columns=["Language", "Count"])
            fig_lang = px.bar(
                df_lang,
                x="Language",
                y="Count",
                title="Top Programming Languages in Radar",
                template="plotly_dark",
                color="Count",
                color_continuous_scale="Viridis",
            )
            fig_lang.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_lang, use_container_width=True)
        else:
            st.info("No language statistics yet.")

    st.markdown("---")
    st.markdown("### 💡 Content Opportunity Scores Distribution")
    with get_db() as s:
        scored_analyses = list(s.execute(
            select(RepositoryAnalysis.content_opportunity_score)
        ).scalars().all())

    if scored_analyses:
        df_scores = pd.DataFrame({"Score": scored_analyses})
        fig_score = px.histogram(
            df_scores,
            x="Score",
            nbins=10,
            title="Content Opportunity Score Histogram (0–100)",
            template="plotly_dark",
            color_discrete_sequence=["#00B4D8"],
        )
        fig_score.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_score, use_container_width=True)
    else:
        st.info("No analyzed repositories with Content Opportunity Scores yet. Run static or AI analysis in Repository Analyzer.")

# ----------------- Tab 3: Scheduled Discovery Jobs & Logs -----------------
with tab_jobs:
    st.markdown("### ⏱️ Scheduled Autonomous Discovery Jobs")
    st.caption("Configured jobs run periodically when the standalone background scheduler process (`python scheduler.py`) is running.")

    if not scheduler_is_running:
        st.warning(
            "⚠️ **Background Scheduler Daemon is STOPPED**.\n\n"
            "To activate automated background execution, launch the scheduler in a dedicated terminal window:\n\n"
            "```bash\npython scheduler.py\n```"
        )
    else:
        st.success(f"🟢 **Scheduler Daemon Active** (PID: `{scheduler_pid}`). Jobs will execute at their configured cron triggers.")

    # List of jobs
    jobs = scheduler_service.list_jobs()
    for j in jobs:
        with st.container(border=True):
            r1, r2, r3, r4 = st.columns([3, 1.5, 1.5, 1.2])
            with r1:
                status_badge = "🟢 ENABLED" if j["is_enabled"] else "⚪ DISABLED"
                st.markdown(f"#### {j['job_name']} `{status_badge}`")
                st.caption(f"Category: **{j['category'].upper()}** | Cron: `{j['cron_expression']}`")
            with r2:
                st.write(f"Latest Run: **{j['latest_status']}**")
                if j["last_run_at"]:
                    st.caption(f"Last executed: {j['last_run_at'].strftime('%Y-%m-%d %H:%M UTC')}")
                else:
                    st.caption("Never executed yet")
            with r3:
                new_state = st.toggle("Active", value=j["is_enabled"], key=f"toggle_{j['id']}")
                if new_state != j["is_enabled"]:
                    scheduler_service.toggle_job(j["id"], new_state)
                    st.rerun()
            with r4:
                if st.button("▶️ Run Now", key=f"run_now_{j['id']}", use_container_width=True):
                    with st.spinner(f"Executing '{j['job_name']}'..."):
                        res = scheduler_service.execute_job(j["id"])
                        if res["status"] == "SUCCESS":
                            st.success(f"Discovered: {res['discovered_count']} | Updated: {res['updated_count']}")
                        else:
                            st.error(f"Status: {res['status']} — {res.get('error_message')}")
                        st.rerun()

    # Form to add a new job
    with st.expander("➕ Configure New Scheduled Discovery Job"):
        with st.form("new_job_form"):
            nj_name = st.text_input("Job Name", placeholder="e.g. Daily Cybersecurity Radar")
            nj_cat = st.selectbox("Category", ["ai", "agents", "software", "security", "fintech", "devtools", "cloud", "all"])
            nj_keywords = st.text_input("Keywords (comma separated)", placeholder="e.g. pentest, vulnerability, osint")
            nj_cron = st.selectbox(
                "Frequency",
                [
                    "0 */6 * * * (Every 6 Hours)",
                    "0 0 * * * (Daily at Midnight)",
                    "0 12 * * * (Daily at Noon)",
                    "0 */12 * * * (Every 12 Hours)",
                ],
            )
            nj_cron_clean = nj_cron.split(" ")[0] + " " + nj_cron.split(" ")[1] + " * * *"
            nj_per_page = st.number_input("Maximum Results Per Run", min_value=5, max_value=50, value=20)
            submit_job = st.form_submit_button("Save & Register Job", type="primary")

            if submit_job:
                if not nj_name.strip():
                    st.error("Job name is required.")
                else:
                    scheduler_service.create_or_update_job(
                        job_name=nj_name.strip(),
                        category=nj_cat,
                        query_params={
                            "mode": "trending" if nj_cat != "agents" else "ai_agents",
                            "category": nj_cat if nj_cat != "all" else None,
                            "keywords": nj_keywords.strip(),
                            "per_page": nj_per_page,
                        },
                        cron_expression=nj_cron_clean,
                        is_enabled=True,
                    )
                    st.success(f"Job '{nj_name}' created successfully.")
                    st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Recent Job Execution Logs")
    logs = scheduler_service.list_recent_logs(limit=30)
    if not logs:
        st.info("No execution logs recorded yet. Trigger a job above or let the scheduler run.")
    else:
        df_logs = pd.DataFrame(logs)
        st.dataframe(
            df_logs.rename(columns={
                "job_name": "Job Name",
                "started_at": "Started (UTC)",
                "finished_at": "Finished (UTC)",
                "discovered_count": "Discovered",
                "updated_count": "Updated",
                "status": "Status",
                "error_message": "Error Details",
            }),
            use_container_width=True,
        )

# ----------------- Tab 4: Monitoring Alerts -----------------
with tab_alerts:
    st.markdown("### 📢 Monitoring & Notification Alerts")
    
    s = get_settings()
    ac1, ac2 = st.columns(2)
    with ac1:
        st.markdown("**Notification Providers Status**:")
        st.write("- 📝 **Application Log Provider**: `ACTIVE` (`logs/monitoring.log`)")
        if s.has_telegram_credentials:
            st.write(f"- 📱 **Telegram Bot Provider**: `CONFIGURED` (Chat ID: `{s.TELEGRAM_CHAT_ID}`)")
        else:
            st.write("- 📱 **Telegram Bot Provider**: `NOT CONFIGURED` (Optional via `.env`)")

    with ac2:
        st.markdown("**Dispatch Test Alert**:")
        if st.button("🔔 Send Test Notification"):
            res = monitoring_service.notify(
                event_type=NotificationEvent.NEW_DISCOVERY,
                title="Manual Notification Test",
                message="This is a test alert dispatched from OpenSource Radar Dashboard.",
                metadata={"url": "https://github.com/trending"},
            )
            st.success(f"Alert broadcasted: {res['dispatched']}")
            st.rerun()

    st.markdown("---")
    st.markdown("### 📜 Recent Alerts Stream")
    alerts = monitoring_service.get_recent_alerts(limit=25)
    if not alerts:
        st.info("No alerts dispatched in current application session.")
    else:
        for a in alerts:
            with st.container(border=True):
                st.markdown(f"**[{a['event_type'].upper()}]** {a['title']}")
                st.caption(f"Timestamp: {a['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
                st.write(a['message'])
                if a.get("metadata") and "url" in a["metadata"]:
                    st.markdown(f"🔗 [Repository Link]({a['metadata']['url']})")

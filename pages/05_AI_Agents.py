"""AI & Autonomous Agents — Curated agentic frameworks and MCP servers."""

import streamlit as st

from services.discovery_service import discovery_service
from utils.helpers import render_page_header, render_repository_card, render_sidebar_status

st.set_page_config(page_title="AI Agents — OpenSource Radar", page_icon="🤖", layout="wide")
render_sidebar_status()

render_page_header(
    title="AI Agents & Automation Radar",
    subtitle="Tracking autonomous agents, multi-agent frameworks, MCP servers, and agent memory.",
    icon="🤖",
)

st.markdown("""
> [!NOTE]
> Curated intelligence covering autonomous frameworks, coding assistants, browser agents, and Model Context Protocol (MCP) ecosystems.
""")

with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        specialization = st.selectbox(
            "Agent Domain",
            [
                "All Agent Frameworks",
                "Model Context Protocol (MCP)",
                "Autonomous Agents",
                "Multi-Agent Swarms",
                "AI Coding Agents",
                "Browser & Web Agents",
                "Agent Memory & Vector Stores",
            ],
        )
        spec_map = {
            "All Agent Frameworks": "agent",
            "Model Context Protocol (MCP)": "mcp",
            "Autonomous Agents": "autonomous-agents",
            "Multi-Agent Swarms": "multi-agent",
            "AI Coding Agents": "coding-agent",
            "Browser & Web Agents": "browser-agent",
            "Agent Memory & Vector Stores": "agent-memory",
        }
    with col2:
        language = st.selectbox("Language", ["Any", "Python", "TypeScript", "Rust", "Go"])
    with col3:
        st.write("")
        st.write("")
        scan_agents_btn = st.button("🤖 Scan Agent Ecosystem", type="primary", use_container_width=True)

if scan_agents_btn or st.session_state.get("last_agents_results"):
    if scan_agents_btn:
        with st.spinner("Scanning GitHub for AI Agent repositories..."):
            try:
                res = discovery_service.run_discovery(
                    mode="ai_agents",
                    keywords=spec_map[specialization],
                    language=None if language == "Any" else language,
                    per_page=15,
                )
                st.session_state["last_agents_results"] = res
            except Exception as exc:
                st.error(f"Failed to scan agent ecosystem: {exc}")
                st.session_state["last_agents_results"] = None

    results = st.session_state.get("last_agents_results")
    if results:
        items = results.get("items", [])
        st.success(f"Discovered {results.get('total_count', 0):,} repositories in the {specialization} space. Showing top {len(items)}.")

        if not items:
            st.info("No repositories found.")
        else:
            for idx, repo in enumerate(items):
                render_repository_card(repo, key_prefix=f"agent_{idx}")
else:
    st.info("Click **Scan Agent Ecosystem** to scout the latest autonomous agents and MCP tooling.")

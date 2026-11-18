"""Discover Repositories — Multi-filter GitHub search engine."""

import streamlit as st

from core.categorizer import categorizer
from database.repository_store import RepositoryStore
from services.discovery_service import discovery_service
from utils.helpers import render_page_header, render_repository_card, render_sidebar_status

st.set_page_config(page_title="Discover — OpenSource Radar", page_icon="🔍", layout="wide")
render_sidebar_status()

render_page_header(
    title="Global Technology Discovery",
    subtitle="Search and filter public GitHub repositories across curated domains with custom criteria.",
    icon="🔍",
)

tab_search, tab_history = st.tabs(["🔎 Deep Search", "📜 Search History"])

with tab_search:
    # Build category list
    all_cats = categorizer.list_categories()
    cat_options = {"All Categories": None} | {c.display_name: c.key for c in all_cats}

    with st.expander("🛠️ Advanced Search Filters", expanded=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            keywords = st.text_input("Keywords", placeholder="e.g. autonomous agent, backtesting, rag")
            selected_cat_name = st.selectbox("Technology Category", options=list(cat_options.keys()))
            selected_cat_key = cat_options[selected_cat_name]
        with f_col2:
            topic = st.text_input("Specific Topic Tag", placeholder="e.g. mcp, llm, osint")
            language = st.selectbox("Programming Language", ["Any", "Python", "Rust", "Go", "TypeScript", "C++", "Java", "Solidity"])
        with f_col3:
            min_stars = st.number_input("Minimum Stars", min_value=0, max_value=500000, value=25, step=25)
            max_stars = st.number_input("Maximum Stars (Optional)", min_value=0, max_value=500000, value=0, step=100)
            sort_by = st.selectbox("Sort Order", ["stars", "forks", "updated"])
            order_dir = st.selectbox("Direction", ["desc", "asc"])

    p_col1, p_col2 = st.columns([1, 4])
    with p_col1:
        page_num = st.number_input("Page", min_value=1, max_value=50, value=1, step=1)
    with p_col2:
        search_btn = st.button("🚀 Search GitHub", type="primary", use_container_width=True)

    if search_btn or st.session_state.get("last_discover_results"):
        if search_btn:
            with st.spinner("Searching GitHub public repositories..."):
                try:
                    res = discovery_service.run_custom_search(
                        keywords=keywords if keywords.strip() else None,
                        category=selected_cat_key,
                        topic=topic if topic.strip() else None,
                        language=None if language == "Any" else language,
                        min_stars=min_stars if min_stars > 0 else None,
                        max_stars=max_stars if max_stars > 0 else None,
                        sort=sort_by,
                        order=order_dir,
                        page=page_num,
                        per_page=20,
                    )
                    st.session_state["last_discover_results"] = res
                except Exception as exc:
                    st.error(f"Search failed: {str(exc)}")
                    st.session_state["last_discover_results"] = None

        results = st.session_state.get("last_discover_results")
        if results:
            items = results.get("items", [])
            total_count = results.get("total_count", 0)
            st.success(f"Discovered {total_count:,} repositories on GitHub (Showing page {results.get('page')} — {len(items)} items)")

            if not items:
                st.info("No repositories matched your search query.")
            else:
                for idx, repo in enumerate(items):
                    render_repository_card(repo, key_prefix=f"disc_{idx}")

with tab_history:
    st.markdown("### Recent Search Logs")
    history = RepositoryStore.get_recent_searches(limit=15)
    if not history:
        st.info("No search queries recorded yet.")
    else:
        for entry in history:
            with st.container(border=True):
                st.markdown(f"**Query**: `{entry.query_string}`")
                st.caption(
                    f"Results Found: **{entry.result_count:,}** | "
                    f"Executed: **{entry.executed_at.strftime('%Y-%m-%d %H:%M:%S')}**"
                )
                if entry.filters_applied:
                    st.json(entry.filters_applied, expanded=False)

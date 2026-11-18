"""Trending Repositories — Fast-moving tech projects radar."""

import streamlit as st

from core.categorizer import categorizer
from services.discovery_service import discovery_service
from utils.helpers import render_page_header, render_repository_card, render_sidebar_status

st.set_page_config(page_title="Trending — OpenSource Radar", page_icon="🔥", layout="wide")
render_sidebar_status()

render_page_header(
    title="Trending Radar",
    subtitle="Fast-moving repositories with significant recent push activity and star momentum.",
    icon="🔥",
)

st.markdown("""
> [!NOTE]
> **Accuracy Notice**: GitHub does not provide an official universal trending API feed.
> OpenSource Radar tracks trending velocity by filtering repositories with active push events within the selected window and high star traction.
""")

all_cats = categorizer.list_categories()
cat_options = {"All Domains": None} | {c.display_name: c.key for c in all_cats}

with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        timeframe = st.selectbox("Activity Window", ["Past 7 Days", "Past 14 Days", "Past 30 Days"])
        days_map = {"Past 7 Days": 7, "Past 14 Days": 14, "Past 30 Days": 30}
        days_window = days_map[timeframe]
    with col2:
        selected_cat_name = st.selectbox("Domain Filter", list(cat_options.keys()))
        selected_cat_key = cat_options[selected_cat_name]
    with col3:
        language = st.selectbox("Language", ["Any", "Python", "Rust", "Go", "TypeScript", "C++"])
    with col4:
        st.write("")
        st.write("")
        fetch_btn = st.button("🔥 Scan Trending", type="primary", use_container_width=True)

if fetch_btn or st.session_state.get("last_trending_results"):
    if fetch_btn:
        with st.spinner("Analyzing trending momentum on GitHub..."):
            try:
                res = discovery_service.run_discovery(
                    mode="trending",
                    category=selected_cat_key,
                    language=None if language == "Any" else language,
                    days_window=days_window,
                    per_page=15,
                )
                st.session_state["last_trending_results"] = res
            except Exception as exc:
                st.error(f"Failed to fetch trending repositories: {exc}")
                st.session_state["last_trending_results"] = None

    results = st.session_state.get("last_trending_results")
    if results:
        items = results.get("items", [])
        st.success(f"Discovered {results.get('total_count', 0):,} trending repositories. Displaying top {len(items)}.")

        if not items:
            st.info("No repositories matched the trending parameters.")
        else:
            for idx, repo in enumerate(items):
                render_repository_card(repo, key_prefix=f"trend_{idx}")
else:
    st.info("Select your timeframe and domain above, then click **Scan Trending** to discover repositories.")

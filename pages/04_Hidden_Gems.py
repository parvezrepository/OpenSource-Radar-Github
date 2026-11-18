"""Hidden Gems — High-potential under-the-radar repositories."""

import streamlit as st

from core.categorizer import categorizer
from services.discovery_service import discovery_service
from utils.helpers import render_page_header, render_repository_card, render_sidebar_status

st.set_page_config(page_title="Hidden Gems — OpenSource Radar", page_icon="💎", layout="wide")
render_sidebar_status()

render_page_header(
    title="Hidden Gems Discovery Radar",
    subtitle="Emerging projects with strong initial traction, active commits, and low mainstream visibility.",
    icon="💎",
)

st.markdown("""
> [!NOTE]
> **Editorial Notice**: Hidden Gems are surfaced as *potential discoveries* based on star-to-fork ratios and active commits.
> They are candidates for early review and content creation, not verified production-grade tools.
""")

all_cats = categorizer.list_categories()
cat_options = {"All Domains": None} | {c.display_name: c.key for c in all_cats}

with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        domain_name = st.selectbox("Domain", list(cat_options.keys()))
        domain_key = cat_options[domain_name]
    with col2:
        custom_kw = st.text_input("Niche Topic (Optional)", placeholder="e.g. compiler, quant, parser")
    with col3:
        language = st.selectbox("Language", ["Any", "Python", "Rust", "Go", "TypeScript", "C++"])
    with col4:
        st.write("")
        st.write("")
        scan_btn = st.button("💎 Scout Hidden Gems", type="primary", use_container_width=True)

if scan_btn or st.session_state.get("last_gems_results"):
    if scan_btn:
        with st.spinner("Scouting high-potential hidden gems on GitHub..."):
            try:
                res = discovery_service.run_discovery(
                    mode="hidden_gems",
                    category=domain_key,
                    keywords=custom_kw if custom_kw.strip() else None,
                    language=None if language == "Any" else language,
                    per_page=15,
                )
                st.session_state["last_gems_results"] = res
            except Exception as exc:
                st.error(f"Discovery error: {exc}")
                st.session_state["last_gems_results"] = None

    results = st.session_state.get("last_gems_results")
    if results:
        items = results.get("items", [])
        st.success(f"Discovered {results.get('total_count', 0):,} candidates on GitHub. Showing top {len(items)}.")

        if not items:
            st.info("No hidden gems found matching these criteria.")
        else:
            for idx, repo in enumerate(items):
                render_repository_card(repo, key_prefix=f"gem_{idx}")
else:
    st.info("Click **Scout Hidden Gems** to identify emerging repositories with under 1,200 stars.")

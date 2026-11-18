"""Trading & FinTech — Algorithmic trading, bots, and quantitative finance."""

import streamlit as st

from services.discovery_service import discovery_service
from utils.helpers import render_page_header, render_repository_card, render_sidebar_status

st.set_page_config(page_title="Trading & FinTech — OpenSource Radar", page_icon="📈", layout="wide")
render_sidebar_status()

render_page_header(
    title="Trading & FinTech Radar",
    subtitle="Algorithmic trading systems, crypto bots, MT4/MT5 expert advisors, and quantitative finance tools.",
    icon="📈",
)

st.markdown("""
> [!NOTE]
> Curated intelligence covering quantitative finance, automated trading strategies, backtesting engines, and risk analysis packages.
""")

with st.container(border=True):
    t1, t2, t3 = st.columns(3)
    with t1:
        fintech_type = st.selectbox(
            "Financial Domain",
            [
                "All FinTech & Trading",
                "Algorithmic Trading & Execution",
                "Crypto Trading & Arbitrage",
                "Backtesting Engines",
                "Forex & MT4 / MT5",
                "Technical Indicators & TA-Lib",
                "Portfolio & Risk Management",
            ],
        )
        fintech_map = {
            "All FinTech & Trading": "trading",
            "Algorithmic Trading & Execution": "algorithmic-trading",
            "Crypto Trading & Arbitrage": "crypto bot",
            "Backtesting Engines": "backtesting",
            "Forex & MT4 / MT5": "metatrader",
            "Technical Indicators & TA-Lib": "technical analysis",
            "Portfolio & Risk Management": "risk management",
        }
    with t2:
        language = st.selectbox("Language", ["Any", "Python", "Rust", "C++", "Go", "MQL5"])
    with t3:
        st.write("")
        st.write("")
        scan_fintech_btn = st.button("📈 Scan FinTech Repos", type="primary", use_container_width=True)

if scan_fintech_btn or st.session_state.get("last_fintech_results"):
    if scan_fintech_btn:
        with st.spinner("Scanning GitHub for Trading & FinTech repositories..."):
            try:
                res = discovery_service.run_discovery(
                    mode="trading_fintech",
                    keywords=fintech_map[fintech_type],
                    language=None if language == "Any" else language,
                    per_page=15,
                )
                st.session_state["last_fintech_results"] = res
            except Exception as exc:
                st.error(f"Failed to scan FinTech ecosystem: {exc}")
                st.session_state["last_fintech_results"] = None

    results = st.session_state.get("last_fintech_results")
    if results:
        items = results.get("items", [])
        st.success(f"Discovered {results.get('total_count', 0):,} repositories in {fintech_type}. Showing top {len(items)}.")

        if not items:
            st.info("No repositories found.")
        else:
            for idx, repo in enumerate(items):
                render_repository_card(repo, key_prefix=f"fin_{idx}")
else:
    st.info("Click **Scan FinTech Repos** to explore open-source trading bots and quant frameworks.")

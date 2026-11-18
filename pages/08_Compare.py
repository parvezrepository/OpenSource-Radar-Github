"""Compare Repositories — Side-by-side comparative analysis matrix."""

import pandas as pd
import streamlit as st

from core.comparison_engine import comparison_engine
from database.repository_store import RepositoryStore
from utils.helpers import render_page_header, render_sidebar_status

st.set_page_config(page_title="Compare — OpenSource Radar", page_icon="⚖️", layout="wide")
render_sidebar_status()

render_page_header(
    title="Repository Comparison Matrix",
    subtitle="Evaluate 2 to 5 repositories side-by-side on architecture, metrics, maintenance, and editorial appeal.",
    icon="⚖️",
)

st.markdown("""
> [!NOTE]
> Select 2 to 5 repositories to evaluate their metrics, dependency overlap, and technical trade-offs.
""")

# Load saved repositories as suggestions
saved_list = RepositoryStore.list_saved_repositories()
saved_names = [item["repository"].full_name for item in saved_list if item.get("repository")]

col_input, col_action = st.columns([4, 1])

with col_input:
    selected_repos = st.multiselect(
        "Select Repositories from Bookmarks or Type Names (2–5)",
        options=saved_names,
        default=saved_names[:2] if len(saved_names) >= 2 else [],
        placeholder="Select saved repositories...",
    )
    custom_inputs = st.text_input(
        "Or add custom repository names (comma-separated, e.g. 'tiangolo/fastapi, pallets/flask')",
        placeholder="owner/repo, owner/repo",
    )

with col_action:
    st.write("")
    st.write("")
    compare_btn = st.button("⚖️ Compare Repositories", type="primary", use_container_width=True)

# Parse targets
targets = list(selected_repos)
if custom_inputs.strip():
    for piece in custom_inputs.split(","):
        cleaned = piece.strip().replace("https://github.com/", "")
        if cleaned and cleaned not in targets:
            targets.append(cleaned)

if compare_btn:
    if len(targets) < 2:
        st.warning("Please provide at least 2 repositories to compare.")
    elif len(targets) > 5:
        st.warning("You can compare at most 5 repositories at once.")
    else:
        with st.spinner(f"Comparing {len(targets)} repositories side-by-side..."):
            try:
                matrix = comparison_engine.compare_repositories(targets)
                st.session_state["compare_matrix"] = matrix
                st.success("Comparison generated successfully.")
            except Exception as exc:
                st.error(f"Comparison failed: {str(exc)}")
                st.session_state["compare_matrix"] = None

matrix = st.session_state.get("compare_matrix")

if matrix:
    repos = matrix["repositories"]
    st.markdown(f"### Comparing: {', '.join([f'`{r}`' for r in repos])}")

    # Metrics Table
    st.markdown("#### 📊 Core Metric Matrix")
    metrics_data = {
        "Metric": [
            "Stars",
            "Forks",
            "Open Issues",
            "Content Opportunity Score",
            "Primary Language",
            "License",
            "Has Test Suite",
            "Has Dockerfile",
            "Last Commit Date",
        ]
    }
    for r in repos:
        m = matrix["metrics"]
        metrics_data[r] = [
            f"{m['stars'].get(r, 0):,}",
            f"{m['forks'].get(r, 0):,}",
            f"{m['open_issues'].get(r, 0):,}",
            f"{m['content_opportunity_score'].get(r, 0)} / 100",
            m["primary_language"].get(r, "N/A"),
            m["license"].get(r, "None"),
            m["has_tests"].get(r, "No"),
            m["has_docker"].get(r, "No"),
            m["last_commit"].get(r, "N/A"),
        ]

    df_metrics = pd.DataFrame(metrics_data)
    st.dataframe(df_metrics, use_container_width=True, hide_index=True)

    # Dependency Overlap
    st.markdown("#### 🔗 Dependency Overlap")
    common_deps = matrix.get("common_dependencies", [])
    if common_deps:
        st.success(f"Common dependencies across all compared repositories: {', '.join([f'`{d}`' for d in common_deps])}")
    else:
        st.info("No shared dependencies identified across the compared repositories.")

    # Strengths and Trade-offs
    st.markdown("#### ⚖️ Strengths & Limitations Side-by-Side")
    cols = st.columns(len(repos))
    for idx, r in enumerate(repos):
        with cols[idx]:
            with st.container(border=True):
                st.markdown(f"**{r}**")
                st.markdown("##### Strengths")
                for s in matrix["strengths"].get(r, []):
                    st.write(f"- ✅ {s}")

                st.markdown("##### Limitations / Gaps")
                for l in matrix["limitations"].get(r, []):
                    st.caption(f"- ⚠️ {l}")
else:
    st.info("Select or enter at least 2 repositories above and click **Compare Repositories**.")

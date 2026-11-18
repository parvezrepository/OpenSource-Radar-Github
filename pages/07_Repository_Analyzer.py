"""Repository Analyzer — Deep technical research dossier and AI intelligence engine."""

import streamlit as st

from config import get_settings
from core.github_client import get_github_client
from core.repository_analyzer import repository_analyzer
from core.scoring_engine import scoring_engine
from database.repository_store import RepositoryStore
from utils.helpers import render_page_header, render_sidebar_status

st.set_page_config(page_title="Analyzer — OpenSource Radar", page_icon="🔬", layout="wide")
render_sidebar_status()

render_page_header(
    title="Repository Deep Analyzer & AI Assistant",
    subtitle="In-depth static intelligence: architecture, README inspection, dependency parsing, explainable scoring, and AI insights.",
    icon="🔬",
)

st.markdown("""
> [!IMPORTANT]
> **Strict Zero Code Execution**: Repository source code is never executed, installed, or imported dynamically.
> All analyses are conducted strictly via static parsing, verified GitHub REST API data, and hardened AI models.
""")

settings = get_settings()

# Check if selected from another page via session state
initial_repo = st.session_state.get("selected_repo", "")

# Search input row
a_col1, a_col2, a_col3 = st.columns([3, 1.2, 1.2])
with a_col1:
    repo_input = st.text_input(
        "GitHub Repository (owner/repo or URL)",
        value=initial_repo,
        placeholder="e.g. tiangolo/fastapi or https://github.com/microsoft/markitdown",
    )
with a_col2:
    st.write("")
    st.write("")
    static_btn = st.button("🔬 Static Analysis", type="secondary", use_container_width=True)
with a_col3:
    st.write("")
    st.write("")
    ai_btn = st.button("🤖 Analyze with AI", type="primary", use_container_width=True)

# Parse repo input
def clean_repo_input(raw: str) -> tuple[str, str]:
    cleaned = raw.strip().replace("https://github.com/", "").replace("http://github.com/", "").strip("/")
    if "/" in cleaned:
        parts = cleaned.split("/")
        return parts[0], parts[1]
    return "", ""

target_owner, target_name = clean_repo_input(repo_input)
target_full_name = f"{target_owner}/{target_name}".lower() if target_owner and target_name else ""
current_dossier = st.session_state.get("current_dossier")
current_dossier_repo = current_dossier.get("repository", {}).get("full_name", "").lower() if current_dossier else ""

# Auto-load existing analysis from database if switching to a new repository
if target_full_name and (current_dossier_repo != target_full_name) and not (static_btn or ai_btn):
    db_repo = RepositoryStore.get_by_full_name(f"{target_owner}/{target_name}")
    if db_repo and db_repo.analyses:
        latest = db_repo.analyses[-1]
        st.session_state["current_dossier"] = latest.dossier_data
        st.session_state["current_score"] = latest.score_breakdown or {"total_score": latest.opportunity_score}
        st.session_state["current_ai_analysis"] = latest.ai_analysis_data
    elif initial_repo and not current_dossier:
        with st.spinner(f"Loading telemetry for {target_owner}/{target_name}..."):
            try:
                dossier = repository_analyzer.analyze_repository(target_owner, target_name)
                score_report = scoring_engine.calculate_score(dossier)
                st.session_state["current_dossier"] = dossier
                st.session_state["current_score"] = score_report.to_dict()
                st.session_state["current_ai_analysis"] = None
                repo_record = RepositoryStore.upsert_repository(dossier["repository"])
                repository_analyzer.persist_analysis(
                    repository_id=repo_record.id,
                    dossier=dossier,
                    score=score_report.total_score,
                    score_breakdown=score_report.to_dict(),
                )
            except Exception:
                pass

# Handle Static Analysis
if static_btn and target_owner and target_name:
    with st.spinner(f"Analyzing {target_owner}/{target_name} statically..."):
        try:
            dossier = repository_analyzer.analyze_repository(target_owner, target_name)
            score_report = scoring_engine.calculate_score(dossier)
            st.session_state["current_dossier"] = dossier
            st.session_state["current_score"] = score_report.to_dict()
            st.session_state["current_ai_analysis"] = None

            # Ensure repository is in database
            repo_record = RepositoryStore.upsert_repository(dossier["repository"])
            repository_analyzer.persist_analysis(
                repository_id=repo_record.id,
                dossier=dossier,
                score=score_report.total_score,
                score_breakdown=score_report.to_dict(),
            )
            st.success(f"Static analysis completed and saved for **{target_owner}/{target_name}**.")
        except Exception as exc:
            st.error(f"Analysis failed: {str(exc)}")
            st.session_state["current_dossier"] = None

# Handle AI Analysis
if ai_btn and target_owner and target_name:
    if settings.AI_PROVIDER == "none" or (settings.AI_PROVIDER == "openai" and not settings.has_openai_credentials) or (settings.AI_PROVIDER == "gemini" and not settings.has_gemini_credentials):
        st.warning(
            f"AI provider '{settings.AI_PROVIDER}' requires active credentials. "
            "Please configure `OPENAI_API_KEY` or `GEMINI_API_KEY` in your `.env` file. "
            "Displaying static deterministic analysis below."
        )
        # Fallback to static
        with st.spinner(f"Running deterministic static analysis for {target_owner}/{target_name}..."):
            try:
                dossier = repository_analyzer.analyze_repository(target_owner, target_name)
                score_report = scoring_engine.calculate_score(dossier)
                st.session_state["current_dossier"] = dossier
                st.session_state["current_score"] = score_report.to_dict()
                st.session_state["current_ai_analysis"] = None
            except Exception as exc:
                st.error(f"Static analysis failed: {exc}")
    else:
        with st.spinner(f"Generating AI research intelligence for {target_owner}/{target_name} with {settings.AI_PROVIDER.upper()}..."):
            try:
                ai_res, saved_rec = repository_analyzer.analyze_with_ai(target_owner, target_name, force_refresh=True)
                dossier = repository_analyzer.analyze_repository(target_owner, target_name)
                score_report = scoring_engine.calculate_score(dossier)
                st.session_state["current_dossier"] = dossier
                st.session_state["current_score"] = score_report.to_dict()
                st.session_state["current_ai_analysis"] = ai_res.to_dict()
                st.success(f"AI intelligence generated and persisted with **{settings.AI_PROVIDER.upper()}**.")
            except Exception as exc:
                st.error(f"AI analysis failed: {str(exc)}")

dossier = st.session_state.get("current_dossier")
score_dict = st.session_state.get("current_score")
ai_analysis = st.session_state.get("current_ai_analysis")

if dossier and score_dict:
    repo_meta = dossier["repository"]
    facts = dossier["verified_facts"]
    claims = dossier["readme_claims"]
    obs = dossier["source_code_observations"]
    tech = obs.get("detected_technologies", {})

    st.markdown(f"## 📦 [{repo_meta['full_name']}]({repo_meta['html_url']})")
    st.caption(repo_meta["description"] or "No description provided.")

    # Top metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Stars", f"{repo_meta['stars']:,}")
    with m2:
        st.metric("Forks", f"{repo_meta['forks']:,}")
    with m3:
        st.metric("Open Issues", f"{repo_meta['open_issues']:,}")
    with m4:
        st.metric("Content Opportunity", f"{score_dict['total_score']} / 100")
    with m5:
        st.metric("Analysis Mode", "AI-Powered" if ai_analysis else "Static / Deterministic")

    st.markdown("---")

    # If AI analysis exists, show AI Intelligence Card upfront
    if ai_analysis:
        with st.container(border=True):
            st.markdown("### 🤖 AI Research Intelligence Dossier")
            st.caption(f"Synthesized by **{settings.AI_PROVIDER.upper()}** ({settings.OPENAI_MODEL if settings.AI_PROVIDER == 'openai' else settings.GEMINI_MODEL}) with strict prompt-injection guardrails.")
            
            st.markdown("#### 💡 Plain Language Explanation")
            st.info(ai_analysis.get("simple_explanation"))

            st.markdown("#### 🏗️ Technical Architecture Insights")
            st.write(ai_analysis.get("technical_architecture"))

            a1, a2 = st.columns(2)
            with a1:
                st.markdown("##### 🚀 Practical Applications & Use Cases")
                for app in ai_analysis.get("practical_applications", []):
                    st.write(f"- {app}")

                st.markdown("##### ⚙️ Key Functions & Modules")
                for fn in ai_analysis.get("key_functions", []):
                    st.write(f"- `{fn}`")

            with a2:
                st.markdown("##### 🎓 Key Learning Opportunities")
                for learn in ai_analysis.get("learning_opportunities", []):
                    st.write(f"- 📘 {learn}")

                st.markdown("##### 🔬 Potential Research & Content Topics")
                for topic in ai_analysis.get("potential_research_topics", []):
                    st.write(f"- 🎯 {topic}")

            if ai_analysis.get("important_files"):
                st.markdown("##### 📁 Key Source Files Identified")
                for f_info in ai_analysis["important_files"]:
                    st.write(f"- `{f_info.get('path')}`: {f_info.get('purpose')}")

            if ai_analysis.get("evidence_sources"):
                st.caption(f"📑 Evidence Sources: {', '.join(ai_analysis.get('evidence_sources', []))}")

    def render_dossier_tabs() -> None:
        tabs = st.tabs([
            "📋 Overview",
            "🛠️ Technologies & Stack",
            "✨ Features & Claims",
            "🏗️ Architecture",
            "📁 Source Files",
            "📖 Documentation",
            "🩺 Repository Health",
            "💡 Content Opportunities",
        ])

        # Tab 1: Overview
        with tabs[0]:
            st.markdown("### Verified Facts")
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                st.write(f"**License**: `{repo_meta['license']}`")
                st.write(f"**Default Branch**: `{repo_meta['default_branch']}`")
                st.write(f"**Archived Status**: `{'Yes (Read Only)' if repo_meta['is_archived'] else 'No (Active)'}`")
                st.write(f"**Latest Release**: `{facts['latest_release_tag']}` (Published: {facts['latest_release_date'][:10]})")
            with f_col2:
                st.write(f"**Last Commit**: `{str(facts['last_commit_date'])[:10]}`")
                st.write(f"**Test Suite Detected**: `{'✅ Yes' if facts['has_test_suite'] else '❌ No'}`")
                st.write(f"**CI Pipeline**: `{'✅ Yes' if facts['has_ci_pipeline'] else '❌ No'}`")
                st.write(f"**Dockerfile / Compose**: `{'✅ Yes' if facts['has_dockerfile'] else '❌ No'}`")

            st.markdown("#### High-Level Problem Statement (from README)")
            st.info(claims["problem_solved"])

        # Tab 2: Technologies & Stack
        with tabs[1]:
            st.markdown("### Detected Technical Stack")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown("#### Frameworks & Libraries")
                if tech.get("frameworks"):
                    for fw in tech["frameworks"]:
                        st.badge(fw)
                else:
                    st.write("No major frameworks detected in static manifests.")

                st.markdown("#### Databases & Stores")
                if tech.get("databases"):
                    for db in tech["databases"]:
                        st.badge(db)
                else:
                    st.write("No database drivers detected in manifest.")

            with t_col2:
                st.markdown("#### Language Byte Distribution")
                lang_dist = facts.get("languages_byte_distribution", {})
                if lang_dist:
                    total_bytes = sum(lang_dist.values()) or 1
                    for lang, b_count in lang_dist.items():
                        pct = (b_count / total_bytes) * 100
                        st.write(f"**{lang}**: {pct:.1f}% ({b_count:,} bytes)")
                else:
                    st.write("Language breakdown not available.")

            st.markdown("#### Parsed Dependencies")
            deps = obs.get("dependencies_parsed", [])
            if deps:
                st.write(", ".join([f"`{d}`" for d in deps]))
            else:
                st.info("No primary dependency manifest (`requirements.txt`, `pyproject.toml`, `package.json`) detected.")

        # Tab 3: Features & Claims
        with tabs[2]:
            st.markdown("### README Claims & Highlights")
            st.markdown("#### Claimed Features")
            st.write(claims["features_claimed"])

            st.markdown("#### Installation Process")
            st.code(claims["installation_process"], language="bash")

            st.markdown("#### Usage Instructions")
            st.write(claims["usage_instructions"])

        # Tab 4: Architecture
        with tabs[3]:
            st.markdown("### Static Architectural Signals")
            st.write(f"**Total Indexed Files**: {facts['total_indexed_files']}")
            st.write(f"**Detected Manifests**: `{', '.join(obs.get('manifest_detected', [])) or 'None'}`")
            st.write(f"**Containerization**: `{'Dockerfile present' if facts['has_dockerfile'] else 'None detected'}`")
            st.write(f"**Continuous Integration**: `{'GitHub Actions active' if facts['has_ci_pipeline'] else 'None detected'}`")

        # Tab 5: Source Files
        with tabs[4]:
            st.markdown("### Safe Static Source Browser")
            st.caption("Inspect text files safely (max 100KB per file). Binaries are automatically rejected.")
            
            file_tree = dossier.get("file_tree", [])
            if file_tree:
                selected_file = st.selectbox("Select file to view", options=file_tree)
                if selected_file and st.button(f"👁️ View {selected_file}", type="secondary"):
                    client = get_github_client()
                    content, err = client.get_file_content(target_owner, target_name, selected_file, max_size_kb=100)
                    if err:
                        st.error(err)
                    else:
                        st.code(content or "[Empty file]")
            else:
                st.info("No file tree available.")

        # Tab 6: Documentation
        with tabs[5]:
            st.markdown("### Raw README Content")
            if dossier.get("raw_readme"):
                with st.expander("Show Complete README Markdown", expanded=True):
                    st.markdown(dossier["raw_readme"])
            else:
                st.info("No README found for this repository.")

        # Tab 7: Repository Health
        with tabs[6]:
            st.markdown("### Repository Health & Maintenance Signals")
            h1, h2, h3 = st.columns(3)
            with h1:
                st.metric("Test Coverage Signal", "Present" if facts["has_test_suite"] else "Missing")
            with h2:
                st.metric("Archived", "Yes" if repo_meta["is_archived"] else "No")
            with h3:
                st.metric("Issue Ratio", f"{repo_meta['open_issues']} issues / {repo_meta['forks']} forks")

        # Tab 8: Content Opportunities
        with tabs[7]:
            st.markdown("### 💡 Explainable Content Opportunity Score")
            st.metric("Overall Editorial Score", f"{score_dict['total_score']} / 100")
            st.info(f"**Editorial Verdict**: {score_dict['editorial_verdict']}")

            if score_dict.get("is_preliminary"):
                st.warning("⚠️ **Preliminary Score**: Measured historical trajectory snapshots will be added in Phase 6.")

            st.markdown("#### Five Pillar Breakdown")
            pillars = score_dict["pillars"]
            for p_key, p_data in pillars.items():
                with st.container(border=True):
                    st.markdown(f"**{p_data['name']}**: `{p_data['score']} / {p_data['max_score']} pts`")
                    if p_data["reasons"]:
                        for r in p_data["reasons"]:
                            st.write(f"- ✅ {r}")
                    if p_data["missing"]:
                        for m in p_data["missing"]:
                            st.caption(f"- ⚠️ {m}")

    def render_chat_assistant() -> None:
        chat_history_key = f"chat_history_{repo_meta['full_name']}"
        if chat_history_key not in st.session_state:
            st.session_state[chat_history_key] = [
                {
                    "role": "assistant",
                    "content": f"Hello! I am your AI intelligence assistant for **{repo_meta['full_name']}**.\n\n"
                               f"I have direct access to verified facts, parsed dependencies, source files, and README claims. "
                               f"Ask me anything about this codebase!",
                }
            ]

        with st.container(border=True):
            ch_col1, ch_col2 = st.columns([3, 1])
            with ch_col1:
                st.markdown(
                    f'<div style="display: flex; align-items: center; gap: 8px;">'
                    f'<span class="status-dot"></span>'
                    f'<span style="font-size: 11px; font-weight: 700; color: #DC9F85; letter-spacing: 1px; text-transform: uppercase;">GROUNDED AI ASSISTANT</span>'
                    f'</div>'
                    f'<h4 style="margin: 2px 0 0 0; font-size: 15px; color: #EBDCC4;">Chat with {repo_meta["name"]}</h4>',
                    unsafe_allow_html=True,
                )
            with ch_col2:
                if st.button("🧹 Clear", key=f"clear_chat_{repo_meta['full_name']}", help="Reset conversation history", use_container_width=True):
                    st.session_state[chat_history_key] = [
                        {
                            "role": "assistant",
                            "content": f"Conversation reset. How can I assist you with **{repo_meta['full_name']}**?",
                        }
                    ]
                    st.rerun()

            st.caption("Grounded strictly in verified static dossier facts. Zero code execution.")

            # Quick Prompt Pills
            st.markdown('<div style="font-size: 11px; font-weight: 600; color: #B6A596; margin-top: 6px; margin-bottom: 4px;">SUGGESTED INQUIRIES:</div>', unsafe_allow_html=True)
            q1, q2, q3, q4 = st.columns(4)
            quick_query = None
            with q1:
                if st.button("🐳 Docker", key=f"btn_dock_{repo_meta['full_name']}", use_container_width=True):
                    quick_query = "How do I run and deploy this repository using Docker or Docker Compose?"
            with q2:
                if st.button("🎯 Use Cases", key=f"btn_uses_{repo_meta['full_name']}", use_container_width=True):
                    quick_query = "What real-world problem does this repository solve and what are its practical use cases?"
            with q3:
                if st.button("🏗️ Arch", key=f"btn_arch_{repo_meta['full_name']}", use_container_width=True):
                    quick_query = "Explain the high-level system architecture, entry points, and main pipelines of this codebase."
            with q4:
                if st.button("📦 Deps", key=f"btn_deps_{repo_meta['full_name']}", use_container_width=True):
                    quick_query = "What are the core external libraries and manifest dependencies required to run this?"

            # Scrollable Message Container (Locked Height 480px)
            with st.container(height=480, border=True):
                for msg in st.session_state[chat_history_key]:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            # Input field
            user_input = st.chat_input("Ask anything about this repository...", key=f"chat_in_{repo_meta['full_name']}")
            active_query = user_input or quick_query

            if active_query:
                st.session_state[chat_history_key].append({"role": "user", "content": active_query})
                with st.spinner("Analyzing codebase dossier..."):
                    try:
                        reply = repository_analyzer.chat(
                            dossier=dossier,
                            query=active_query,
                            chat_history=st.session_state[chat_history_key],
                        )
                        st.session_state[chat_history_key].append({"role": "assistant", "content": reply})
                    except Exception as err:
                        st.session_state[chat_history_key].append({"role": "assistant", "content": f"Sorry, could not answer: {err}"})
                st.rerun()

    # Persistent Layout Mode Controller
    st.markdown('<hr style="border-color: #35211A; margin: 18px 0 14px 0;">', unsafe_allow_html=True)
    st.markdown(
        '<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">'
        '<div style="display: flex; align-items: center; gap: 8px;">'
        '<div style="width: 14px; height: 2px; background-color: #DC9F85;"></div>'
        '<span style="font-size: 11px; font-weight: 700; color: #B6A596; letter-spacing: 1.2px; text-transform: uppercase;">INTELLIGENCE WORKSPACE ORIENTATION</span>'
        '</div>'
        '<span style="font-size: 11px; color: #DC9F85; font-weight: 600;">LOCKED IN PLACE</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode_options = [
        "⚡ Split View (Dossier + Chat)",
        "💬 Dedicated AI Chat Assistant",
        "📋 Full Technical Dossier",
    ]
    selected_mode = st.radio(
        "Workspace View",
        options=mode_options,
        index=0,
        horizontal=True,
        key="analyzer_workspace_mode",
        label_visibility="collapsed",
    )

    if selected_mode == "⚡ Split View (Dossier + Chat)":
        col_dossier, col_chat = st.columns([1.35, 1.15], gap="large")
        with col_dossier:
            render_dossier_tabs()
        with col_chat:
            render_chat_assistant()
    elif selected_mode == "💬 Dedicated AI Chat Assistant":
        render_chat_assistant()
    else:
        render_dossier_tabs()
else:
    st.info("Enter a repository handle above (e.g. `psf/requests` or `tiangolo/fastapi`) and click **Static Analysis** or **Analyze with AI**.")

"""Content Creation Studio — Educational scripts, articles, and social drafts."""

import streamlit as st

from ai.analysis import ContentDraftSchema
from database.connection import get_db
from database.models import Repository
from database.repository_store import RepositoryStore
from services.content_service import content_service
from utils.helpers import render_page_header, render_sidebar_status
from sqlalchemy import select

st.set_page_config(page_title="Content Studio — OpenSource Radar", page_icon="✍️", layout="wide")
render_sidebar_status()

render_page_header(
    title="Multi-Platform Content Studio",
    subtitle="Synthesize technical research dossiers into educational video scripts, articles, and social posts.",
    icon="✍️",
)

tab_create, tab_saved = st.tabs(["✨ Content Generator & Editor", "📂 Saved Drafts"])

# Retrieve available repositories for dropdown
with get_db() as session:
    repos_db = list(session.execute(select(Repository).order_by(Repository.full_name)).scalars().all())
    repo_choices = {r.full_name: (r.owner, r.name, r.id) for r in repos_db}

# ----------------- Tab 1: Content Generator & Editor -----------------
with tab_create:
    with st.container(border=True):
        st.markdown("### ⚙️ Content Configuration")
        c1, c2, c3 = st.columns(3)
        with c1:
            repo_selection_mode = st.radio("Repository Source", ["From Database / Saved", "Custom Handle"], horizontal=True)
            if repo_selection_mode == "From Database / Saved" and repo_choices:
                chosen_repo_name = st.selectbox("Select Repository", options=list(repo_choices.keys()))
                target_owner, target_name, target_db_id = repo_choices[chosen_repo_name]
            else:
                custom_handle = st.text_input("Enter Repository (owner/repo)", placeholder="tiangolo/fastapi")
                if "/" in custom_handle:
                    parts = custom_handle.strip().split("/", 1)
                    target_owner, target_name = parts[0], parts[1]
                else:
                    target_owner, target_name = "", ""
                target_db_id = None

            platform = st.selectbox(
                "Distribution Platform",
                [
                    "YouTube (Long-form)",
                    "YouTube Shorts (30-60s)",
                    "Facebook Post",
                    "Instagram Reel / Carousel",
                    "Telegram Tech Update",
                    "Technical Blog Article",
                    "Step-by-Step Tutorial",
                ],
            )

        with c2:
            content_type = st.selectbox(
                "Content Format",
                ["Full Script", "Educational Post", "Technical Review", "Tutorial Walkthrough", "Announcement"],
            )
            language_display = st.selectbox("Language", ["English (en)", "Bengali / বাংলা (bn)", "Banglish (banglish)"])
            lang_code = "en"
            if "bn" in language_display:
                lang_code = "bn"
            elif "banglish" in language_display:
                lang_code = "banglish"

            tone = st.selectbox(
                "Tone of Voice",
                ["Educational", "Professional", "Conversational", "Engaging", "Technical Deep Dive", "Beginner-Friendly"],
            )

        with c3:
            audience = st.selectbox("Audience Level", ["Beginner", "Intermediate", "Advanced"])
            extra_instructions = st.text_area(
                "Additional Guidance (Optional)",
                placeholder="e.g. Focus on deployment, highlight PyTorch integration, emphasize speed comparison",
                height=110,
            )

        gen_col1, gen_col2 = st.columns([3, 1])
        with gen_col1:
            st.caption("Grounded strictly in verified repository facts, README sections, and detected manifests.")
        with gen_col2:
            generate_btn = st.button("🚀 Generate Draft", type="primary", use_container_width=True)

    # State initialization for editor
    if "studio_draft" not in st.session_state:
        st.session_state["studio_draft"] = None
    if "current_draft_id" not in st.session_state:
        st.session_state["current_draft_id"] = None
    if "studio_repo_id" not in st.session_state:
        st.session_state["studio_repo_id"] = None

    if generate_btn:
        if not target_owner or not target_name:
            st.warning("Please select or enter a valid repository (owner/repo).")
        else:
            with st.spinner(f"Synthesizing {content_type} for {target_owner}/{target_name} in {language_display}..."):
                try:
                    schema, mode, repo_id = content_service.generate_draft(
                        owner=target_owner,
                        repo=target_name,
                        platform=platform,
                        content_type=content_type,
                        language=lang_code,
                        tone=tone,
                        audience_level=audience,
                        additional_instructions=extra_instructions,
                    )
                    st.session_state["studio_draft"] = schema.to_dict()
                    st.session_state["studio_mode"] = mode
                    st.session_state["studio_repo_id"] = repo_id
                    st.session_state["current_draft_id"] = None  # New unsaved draft
                    st.success(f"Draft generated successfully ({mode}).")
                except Exception as exc:
                    st.error(f"Generation failed: {str(exc)}")

    draft_dict = st.session_state.get("studio_draft")

    if draft_dict:
        st.markdown("---")
        st.markdown("### ✍️ Content Draft Studio Editor")
        st.caption(f"Mode: **{st.session_state.get('studio_mode', 'standard').upper()}** | Platform: **{draft_dict.get('platform')}** | Language: **{draft_dict.get('language')}**")

        # Editable fields
        edited_title = st.text_input("Title / Headline", value=draft_dict.get("title", ""))
        edited_hook = st.text_area("Opening Hook (Intro / First 5 seconds)", value=draft_dict.get("hook", ""), height=80)
        edited_body = st.text_area("Main Content Body", value=draft_dict.get("body", ""), height=350)
        edited_practical = st.text_area("Practical Explanation / Use Case", value=draft_dict.get("practical_explanation", ""), height=100)
        edited_cta = st.text_input("Call To Action (CTA)", value=draft_dict.get("cta", ""))
        
        tags_str = ", ".join(draft_dict.get("hashtags", []))
        edited_tags_input = st.text_input("Hashtags (comma separated)", value=tags_str)
        edited_tags = [t.strip() for t in edited_tags_input.split(",") if t.strip()]

        # Visual demo ideas
        demo_ideas = draft_dict.get("visual_demo_suggestions", [])
        if demo_ideas:
            with st.expander("🎬 Suggested Visuals & Demo Concepts", expanded=True):
                for idea in demo_ideas:
                    st.write(f"- {idea}")

        # Update draft in session state
        updated_schema = ContentDraftSchema(
            platform=draft_dict.get("platform", "YouTube"),
            content_type=draft_dict.get("content_type", "Script"),
            language=draft_dict.get("language", "en"),
            tone=draft_dict.get("tone", "Educational"),
            audience_level=draft_dict.get("audience_level", "Intermediate"),
            title=edited_title,
            hook=edited_hook,
            body=edited_body,
            practical_explanation=edited_practical,
            visual_demo_suggestions=demo_ideas,
            cta=edited_cta,
            hashtags=edited_tags,
            source_url=draft_dict.get("source_url", ""),
        )

        # Editor Action Buttons
        act_col1, act_col2, act_col3 = st.columns(3)

        with act_col1:
            if st.button("💾 Save Draft to Database", type="primary", use_container_width=True):
                saved_rec = content_service.save_draft(
                    repository_id=st.session_state.get("studio_repo_id", 1),
                    schema=updated_schema,
                    draft_id=st.session_state.get("current_draft_id"),
                    status="draft",
                )
                st.session_state["current_draft_id"] = saved_rec.id
                st.success(f"Draft saved to SQLite database (Draft ID: #{saved_rec.id}).")

        with act_col2:
            md_export = updated_schema.to_markdown()
            st.download_button(
                label="📥 Download Markdown",
                data=md_export,
                file_name=f"content_draft_{target_name or 'project'}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with act_col3:
            raw_text_export = f"{edited_title}\n\n{edited_hook}\n\n{edited_body}\n\n{edited_cta}\n\n{' '.join(edited_tags)}"
            st.download_button(
                label="📄 Download Plain Text",
                data=raw_text_export,
                file_name=f"content_draft_{target_name or 'project'}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with st.expander("📋 Copyable Markdown Block", expanded=False):
            st.code(updated_schema.to_markdown(), language="markdown")

# ----------------- Tab 2: Saved Drafts Management -----------------
with tab_saved:
    st.markdown("### 📂 Saved Draft Library")
    saved_drafts = content_service.list_drafts()

    if not saved_drafts:
        st.info("No saved drafts found in database. Create and save a draft using the generator tab.")
    else:
        for d in saved_drafts:
            with st.container(border=True):
                row1, row2, row3 = st.columns([3, 1.2, 1])
                with row1:
                    st.markdown(f"#### #{d['id']}: {d['title']}")
                    st.caption(
                        f"Repository: **{d['repository_name']}** | "
                        f"Platform: **{d['platform']}** | "
                        f"Format: **{d['content_type']}** | "
                        f"Language: **{d['language'].upper()}**"
                    )
                with row2:
                    st.write(f"Status: `{d['status'].title()}`")
                    st.caption(f"Updated: {d['updated_at'].strftime('%Y-%m-%d %H:%M')}")
                with row3:
                    if st.button("✏️ Load Draft", key=f"load_draft_{d['id']}", use_container_width=True):
                        full_draft = content_service.get_draft(d["id"])
                        if full_draft:
                            st.session_state["studio_draft"] = {
                                "platform": full_draft["platform"],
                                "content_type": full_draft["content_type"],
                                "language": full_draft["language"],
                                "tone": full_draft["tone"],
                                "audience_level": "Intermediate",
                                "title": full_draft["title"],
                                "hook": full_draft["hook"],
                                "body": full_draft["body"],
                                "practical_explanation": "",
                                "visual_demo_suggestions": [],
                                "cta": full_draft["cta"],
                                "hashtags": full_draft["hashtags"],
                                "source_url": full_draft["repository_url"],
                            }
                            st.session_state["current_draft_id"] = d["id"]
                            st.session_state["studio_repo_id"] = full_draft["repository_id"]
                            st.success(f"Loaded Draft #{d['id']}. Switch to Editor tab.")
                            st.rerun()

                    if st.button("🗑️ Delete", key=f"del_draft_{d['id']}", use_container_width=True):
                        content_service.delete_draft(d["id"])
                        st.success(f"Draft #{d['id']} deleted.")
                        st.rerun()

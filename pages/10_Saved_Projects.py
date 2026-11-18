"""Saved Projects — Library of bookmarked repositories and research notes."""

import streamlit as st

from database.repository_store import RepositoryStore
from utils.helpers import render_page_header, render_sidebar_status

st.set_page_config(page_title="Saved Projects — OpenSource Radar", page_icon="🔖", layout="wide")
render_sidebar_status()

render_page_header(
    title="Bookmarked Repositories",
    subtitle="Your personal research collection of saved open-source repositories.",
    icon="🔖",
)

saved_repos = RepositoryStore.list_saved_repositories()

if not saved_repos:
    st.info("No repositories have been bookmarked yet. When discovering projects in **02 Discover**, click 'Save Project' to bookmark them here.")
else:
    st.write(f"Showing **{len(saved_repos)}** saved project(s).")
    for item in saved_repos:
        repo = item["repository"]
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"### [{repo.full_name}]({repo.html_url})")
                st.write(repo.description or "No description provided.")
                if item["notes"]:
                    st.caption(f"📝 Notes: {item['notes']}")
                if item["tags"]:
                    st.caption(f"🏷️ Tags: {', '.join(item['tags'])}")
            with c2:
                st.metric("Stars", f"{repo.stars:,}")
                st.metric("Forks", f"{repo.forks:,}")
                if st.button("🗑️ Remove", key=f"unsave_{item['saved_id']}"):
                    RepositoryStore.unsave_repository(item["repository_id"])
                    st.success(f"Removed {repo.full_name}")
                    st.rerun()

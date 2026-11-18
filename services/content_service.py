"""Content Service orchestrating generation, draft editing, and SQLite persistence."""

from datetime import datetime, timezone
import logging
from typing import Any, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import joinedload

from ai.analysis import ContentDraftSchema
from core.content_generator import content_generator
from core.repository_analyzer import repository_analyzer
from database.connection import get_db
from database.models import ContentDraft, Repository
from database.repository_store import RepositoryStore

logger = logging.getLogger("opensource_radar.service.content")


class ContentService:
    """Manages content synthesis workflows, draft persistence, editing, and exports."""

    @staticmethod
    def generate_draft(
        owner: str,
        repo: str,
        platform: str,
        content_type: str,
        language: str = "en",
        tone: str = "educational",
        audience_level: str = "intermediate",
        additional_instructions: Optional[str] = None,
    ) -> tuple[ContentDraftSchema, str, int]:
        """
        Analyze repository, generate structured draft, and ensure repository is stored.
        Returns: (draft_schema, mode, repository_db_id)
        """
        # Check if repository already exists in database
        db_repo = RepositoryStore.get_by_full_name(f"{owner}/{repo}")
        if db_repo:
            latest_analysis = db_repo.analyses[0] if db_repo.analyses else None
            repo_data = {
                "id": db_repo.id,
                "github_id": db_repo.github_id,
                "full_name": db_repo.full_name,
                "html_url": db_repo.html_url,
                "description": db_repo.description,
                "stars": db_repo.stars,
                "forks": db_repo.forks,
                "primary_language": db_repo.primary_language,
                "license": db_repo.license_name or "Open Source",
            }
            dossier = {
                "repository": repo_data,
                "verified_facts": {
                    "primary_language": db_repo.primary_language,
                },
                "readme_claims": {
                    "problem_solved": (latest_analysis.problem_solved if latest_analysis else db_repo.description) or "",
                    "features_claimed": "\n".join(latest_analysis.key_features) if latest_analysis and latest_analysis.key_features else "",
                    "installation_process": f"git clone {db_repo.html_url}",
                },
                "source_code_observations": {
                    "detected_technologies": latest_analysis.detected_technologies if latest_analysis else {},
                    "dependencies_parsed": latest_analysis.dependencies if latest_analysis else [],
                },
            }
            repo_id = db_repo.id
        else:
            dossier = repository_analyzer.analyze_repository(owner, repo)
            repo_data = dossier["repository"]
            repo_rec = RepositoryStore.upsert_repository(repo_data)
            repo_id = repo_rec.id

        schema, mode = content_generator.generate(
            repo_data=repo_data,
            dossier=dossier,
            platform=platform,
            content_type=content_type,
            language=language,
            tone=tone,
            audience_level=audience_level,
            additional_instructions=additional_instructions,
        )

        return schema, mode, repo_id

    @staticmethod
    def save_draft(
        repository_id: int,
        schema: ContentDraftSchema,
        draft_id: Optional[int] = None,
        status: str = "draft",
    ) -> ContentDraft:
        """Create or update a ContentDraft record in the database."""
        with get_db() as session:
            if draft_id:
                draft = session.get(ContentDraft, draft_id)
                if draft:
                    draft.platform = schema.platform
                    draft.content_type = schema.content_type
                    draft.language = schema.language
                    draft.tone = schema.tone
                    draft.title = schema.title
                    draft.hook = schema.hook
                    draft.body = schema.body
                    draft.cta = schema.cta
                    draft.hashtags = schema.hashtags
                    draft.status = status
                    draft.updated_at = datetime.now(timezone.utc)
                    return draft

            # Create new draft
            new_draft = ContentDraft(
                repository_id=repository_id,
                platform=schema.platform,
                content_type=schema.content_type,
                language=schema.language,
                tone=schema.tone,
                title=schema.title,
                hook=schema.hook,
                body=schema.body,
                cta=schema.cta,
                hashtags=schema.hashtags,
                status=status,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(new_draft)
            return new_draft

    @staticmethod
    def get_draft(draft_id: int) -> Optional[dict[str, Any]]:
        """Fetch a specific draft with related repository metadata."""
        with get_db() as session:
            stmt = select(ContentDraft).options(joinedload(ContentDraft.repository)).where(ContentDraft.id == draft_id)
            draft = session.execute(stmt).scalars().first()
            if not draft:
                return None
            return {
                "id": draft.id,
                "repository_id": draft.repository_id,
                "repository_name": draft.repository.full_name if draft.repository else "Unknown",
                "repository_url": draft.repository.html_url if draft.repository else "",
                "platform": draft.platform,
                "content_type": draft.content_type,
                "language": draft.language,
                "tone": draft.tone,
                "title": draft.title,
                "hook": draft.hook,
                "body": draft.body,
                "cta": draft.cta,
                "hashtags": draft.hashtags or [],
                "status": draft.status,
                "created_at": draft.created_at,
                "updated_at": draft.updated_at,
            }

    @staticmethod
    def list_drafts(repository_id: Optional[int] = None) -> list[dict[str, Any]]:
        """List all saved drafts, optionally filtered by repository."""
        with get_db() as session:
            stmt = select(ContentDraft).options(joinedload(ContentDraft.repository)).order_by(desc(ContentDraft.updated_at))
            if repository_id:
                stmt = stmt.where(ContentDraft.repository_id == repository_id)
            drafts = session.execute(stmt).scalars().all()
            return [
                {
                    "id": d.id,
                    "repository_id": d.repository_id,
                    "repository_name": d.repository.full_name if d.repository else "Unknown",
                    "platform": d.platform,
                    "content_type": d.content_type,
                    "language": d.language,
                    "title": d.title,
                    "status": d.status,
                    "updated_at": d.updated_at,
                }
                for d in drafts
            ]

    @staticmethod
    def delete_draft(draft_id: int) -> bool:
        """Delete a draft from the database."""
        with get_db() as session:
            draft = session.get(ContentDraft, draft_id)
            if draft:
                session.delete(draft)
                return True
            return False


content_service = ContentService()

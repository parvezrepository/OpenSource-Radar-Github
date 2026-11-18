"""Declarative SQLAlchemy models for OpenSource Radar."""

from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database.connection import Base


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class Category(Base):
    """Technology domain classification category."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    default_topics = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    repositories = relationship("Repository", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Category key='{self.key}' name='{self.display_name}'>"


class Repository(Base):
    """Core GitHub repository entity."""

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    github_id = Column(Integer, unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False, index=True)  # owner/repo
    owner = Column(String(128), nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)
    html_url = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    
    # Quantitative metrics
    stars = Column(Integer, default=0, nullable=False, index=True)
    forks = Column(Integer, default=0, nullable=False)
    open_issues = Column(Integer, default=0, nullable=False)
    repo_size_kb = Column(Integer, default=0, nullable=False)
    
    # Metadata
    primary_language = Column(String(64), nullable=True, index=True)
    topics = Column(JSON, default=list, nullable=False)
    license_key = Column(String(64), nullable=True)
    license_name = Column(String(128), nullable=True)
    default_branch = Column(String(64), default="main", nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at_github = Column(DateTime(timezone=True), nullable=True)
    updated_at_github = Column(DateTime(timezone=True), nullable=True)
    pushed_at_github = Column(DateTime(timezone=True), nullable=True, index=True)
    last_scraped_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Classification
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    category = relationship("Category", back_populates="repositories")

    # Relationships
    snapshots = relationship("RepositorySnapshot", back_populates="repository", cascade="all, delete-orphan", order_by="RepositorySnapshot.recorded_at.desc()")
    analyses = relationship("RepositoryAnalysis", back_populates="repository", cascade="all, delete-orphan", order_by="RepositoryAnalysis.analyzed_at.desc()")
    content_drafts = relationship("ContentDraft", back_populates="repository", cascade="all, delete-orphan")
    saved_entry = relationship("SavedRepository", back_populates="repository", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_repos_stars_pushed", "stars", "pushed_at_github"),
        Index("ix_repos_category_stars", "category_id", "stars"),
    )

    def __repr__(self) -> str:
        return f"<Repository full_name='{self.full_name}' stars={self.stars}>"


class RepositorySnapshot(Base):
    """Point-in-time quantitative observation of a repository for historical tracking."""

    __tablename__ = "repository_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    stars = Column(Integer, nullable=False)
    forks = Column(Integer, nullable=False)
    open_issues = Column(Integer, nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    repository = relationship("Repository", back_populates="snapshots")

    __table_args__ = (
        Index("ix_snapshots_repo_recorded", "repository_id", "recorded_at"),
    )


class RepositoryAnalysis(Base):
    """Static and AI-assisted deep technical analysis record."""

    __tablename__ = "repository_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Technical analysis dossier
    summary = Column(Text, nullable=True)
    problem_solved = Column(Text, nullable=True)
    architecture_overview = Column(Text, nullable=True)
    detected_technologies = Column(JSON, default=dict, nullable=False)  # languages, frameworks, DBs
    key_features = Column(JSON, default=list, nullable=False)
    dependencies = Column(JSON, default=list, nullable=False)
    learning_opportunities = Column(JSON, default=list, nullable=False)
    limitations = Column(JSON, default=list, nullable=False)

    # Explainable Scoring (0-100)
    content_opportunity_score = Column(Integer, default=0, nullable=False, index=True)
    score_breakdown = Column(JSON, default=dict, nullable=False)  # 5 pillars
    
    # Metadata
    analysis_type = Column(String(32), default="static", nullable=False)  # "static", "ai_openai", "ai_gemini"
    analyzed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    repository = relationship("Repository", back_populates="analyses")


class ContentDraft(Base):
    """Educational content draft generated for multi-platform distribution."""

    __tablename__ = "content_drafts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    
    platform = Column(String(32), nullable=False, index=True)  # youtube, shorts, facebook, instagram, telegram, blog
    content_type = Column(String(32), nullable=False)          # script, post, review, tutorial
    language = Column(String(16), default="en", nullable=False) # en, bn, banglish
    tone = Column(String(32), default="educational", nullable=False)
    
    title = Column(String(255), nullable=False)
    hook = Column(Text, nullable=True)
    body = Column(Text, nullable=False)
    cta = Column(Text, nullable=True)
    hashtags = Column(JSON, default=list, nullable=False)
    
    status = Column(String(20), default="draft", nullable=False)  # draft, finalized, published
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    repository = relationship("Repository", back_populates="content_drafts")


class SavedRepository(Base):
    """User bookmarked and saved repositories."""

    __tablename__ = "saved_repositories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, default=list, nullable=False)
    saved_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    repository = relationship("Repository", back_populates="saved_entry")


class SearchHistory(Base):
    """Log of user search and filter queries."""

    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_string = Column(String(512), nullable=False)
    filters_applied = Column(JSON, default=dict, nullable=False)
    result_count = Column(Integer, default=0, nullable=False)
    executed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class DiscoveryJob(Base):
    """Scheduled autonomous discovery job configuration."""

    __tablename__ = "discovery_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_name = Column(String(128), unique=True, nullable=False)
    category = Column(String(64), nullable=False)
    query_params = Column(JSON, default=dict, nullable=False)
    cron_expression = Column(String(64), nullable=False)  # e.g. "0 */6 * * *"
    is_enabled = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    logs = relationship("DiscoveryLog", back_populates="job", cascade="all, delete-orphan")


class DiscoveryLog(Base):
    """Execution run log for automated discovery jobs."""

    __tablename__ = "discovery_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("discovery_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    discovered_count = Column(Integer, default=0, nullable=False)
    updated_count = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="RUNNING", nullable=False)  # SUCCESS, FAILED, RATE_LIMITED
    error_message = Column(Text, nullable=True)

    job = relationship("DiscoveryJob", back_populates="logs")


class AppSettings(Base):
    """Persistent key-value configuration overrides."""

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

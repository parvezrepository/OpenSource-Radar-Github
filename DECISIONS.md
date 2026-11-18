# OpenSource Radar — Architecture Decision Records (ADRs)

This document records the architectural and technical decisions made during the design and development of **OpenSource Radar**, along with their rationale, trade-offs, and implications.

---

## ADR 001: Strict Python-Only Stack with Native Streamlit

- **Context**: OpenSource Radar requires an interactive, developer-centric SaaS dashboard, high-performance data processing, and AI integrations. Modern web apps often split between a JS/TS frontend and a Python backend.
- **Decision**: Enforce a strict Python-only stack using Python 3.11+, Streamlit for the UI dashboard, Pandas/Plotly for visual analytics, and SQLite for persistence. Absolutely prohibit Node.js, React, Next.js, Vue, TypeScript, or custom JavaScript components.
- **Rationale**:
  - Eliminates multi-language context switching, build tooling overhead (npm, webpack, vite), and cross-origin authentication complexity.
  - Allows deep integration between data structures, Pydantic models, SQLAlchemy entities, and UI elements.
  - Native Streamlit multipage architecture provides clean, rapid navigation while keeping state management in Python.
- **Consequences**:
  - UI customizations are limited to native Streamlit features and configuration.
  - Client-side interactions must be handled via Streamlit widgets and session state.

---

## ADR 002: SQLite with Write-Ahead Logging (WAL) and SQLAlchemy 2.0

- **Context**: The platform stores repository metadata, historical star snapshots, AI analysis dossiers, content drafts, and scheduler logs locally.
- **Decision**: Use SQLite managed via SQLAlchemy 2.0 ORM, explicitly enforcing `PRAGMA journal_mode=WAL;` and `PRAGMA foreign_keys=ON;` on all connections.
- **Rationale**:
  - Requires zero external infrastructure (e.g., no external PostgreSQL server required to get started).
  - WAL mode permits concurrent readers (Streamlit UI dashboards) while a single writer (the background scheduler process or user save actions) performs updates without `database is locked` errors.
  - SQLAlchemy 2.0 provides type-annotated Declarative Base models (`Mapped[]`, `mapped_column()`), seamless schema migration safety, and database portability if a client later needs Postgres.
- **Consequences**:
  - Must ensure connection lifecycles are properly scoped using context managers or scoped sessions.

---

## ADR 003: Shared Reusable GitHub Client with Defensive Rate Limiting

- **Context**: GitHub REST API imposes rate limits (60 req/hr unauthenticated; 5,000 req/hr authenticated). Discovery and deep inspection can consume dozens of requests rapidly.
- **Decision**: Implement a unified, singleton-capable `GitHubClient` in `core/github_client.py` with rate limit tracking (`rate_limiter.py`) and short-term TTL caching (`cache.py`). Individual Streamlit pages must never construct ad-hoc HTTP clients.
- **Rationale**:
  - Centralizes rate limit header parsing (`X-RateLimit-Remaining`, `X-RateLimit-Reset`).
  - Automatically delays or aborts before encountering hard 403 Forbidden throttling.
  - Ensures consistent error handling (401, 403, 404, 422, 429) across all discovery and analysis flows.
- **Consequences**:
  - All repository queries must flow through the client/service interface.

---

## ADR 004: Dual AI Provider Abstraction with Graceful Non-AI Fallback

- **Context**: Users may prefer OpenAI, Google Gemini, or run the application in an offline/uncredentialed state for pure repository discovery.
- **Decision**: Create an abstract `AIProvider` base class supporting both OpenAI (`gpt-4o`, `gpt-4o-mini`) and Google Gemini (`gemini-1.5-flash`, `gemini-1.5-pro`). Guarantee that all discovery, inspection, and scoring functions operate 100% deterministically without requiring an AI API key.
- **Rationale**:
  - Avoids vendor lock-in.
  - Ensures the platform remains functional and useful as a repository intelligence tool even when zero AI API keys are configured.
  - When AI is available, Pydantic schemas enforce rigid output validation.
- **Consequences**:
  - Static fallback reports must be prepared for the Repository Analyzer when AI keys are omitted.

---

## ADR 005: Decoupled Standalone APScheduler Process

- **Context**: Automated monitoring and snapshot capture need to run periodically without relying on an active browser tab or user session.
- **Decision**: Run the APScheduler daemon in a standalone Python script (`python scheduler.py`), completely separate from `streamlit run app.py`.
- **Rationale**:
  - Streamlit re-executes code upon user interaction; running background schedulers inside Streamlit page contexts leads to thread leaks, duplicate job triggers, and database locks.
  - A detached process ensures continuous scheduled operations even when no user has the dashboard open.
- **Consequences**:
  - Users run the dashboard and scheduler as two cooperating processes sharing the same SQLite database file.

---

## ADR 006: 5-Pillar Explainable Content Opportunity Scoring

- **Context**: Raw GitHub star counts are misleading due to botting, age bias, or artificial inflation. Content creators and researchers need an objective indicator of editorial and educational potential.
- **Decision**: Compute a deterministic 0–100 score across five weighted pillars: Trend Momentum (25%), Uniqueness (20%), Practical Usefulness (20%), Content Appeal (20%), and Project Health (15%). Every score must output human-readable justifications and highlight missing data.
- **Rationale**:
  - Provides transparent, explainable recommendations rather than a black-box ranking.
  - Separates verified observations from missing signals.
- **Consequences**:
  - Repositories without historical snapshots receive a marked preliminary score with clear caveats.

---

## ADR 007: Strict Zero-Code-Execution Policy & Prompt Sanitization

- **Context**: The repository analyzer inspects untrusted third-party codebases, README files, and issue trackers from GitHub.
- **Decision**: Strictly prohibit code execution, dynamic imports, shell script execution, or package installation of target repositories. Wrap all untrusted text in XML delimiters before passing to AI models, accompanied by explicit guardrails against prompt injection.
- **Rationale**:
  - Protects host machine security from malicious repositories.
  - Prevents prompt injection attempts embedded in open-source READMEs from hijacking AI outputs or exfiltrating environment variables.
- **Consequences**:
  - Technical analysis is strictly static (AST parsing, text regex, dependency file inspection).

---

## ADR 008: Multi-Platform Content Generation with Multilingual Deterministic Fallbacks

- **Context**: The Content Creation Studio needs to generate educational scripts, posts, and articles across 7 platforms and 3 languages (English, Bengali, Banglish), whether AI providers are configured or completely offline.
- **Decision**: Implement a strongly-typed Pydantic schema (`ContentDraftSchema`) and dual generation pathways: an AI-driven generator with prompt-injection fences when API keys are available, and a deterministic template generator (`core/content_generator.py`) that extracts verified repository facts, README sections, and manifest files without external network or LLM dependencies.
- **Rationale**:
  - Ensures the platform never fails to produce educational content even in air-gapped, zero-cost, or uncredentialed environments.
  - Generates culturally nuanced Bengali and Banglish content using native phrasing and terminology.
  - Persists all generated drafts into the SQLite `ContentDraft` table for editing, versioning, and multi-format export (.md, .txt).
- **Consequences**:
  - Deterministic outputs follow structured patterns based on static metrics, while AI outputs provide richer narrative variation when keys are configured.

---

## ADR 009: Decoupled Scheduler Daemon with Non-Fabricated Historical Growth Tracking

- **Context**: The platform needs automated recurring discovery and time-series growth tracking without UI lockups, thread leaks, or falsifying star velocity.
- **Decision**: Run APScheduler inside an isolated, standalone process (`scheduler.py`) guarded by a PID-based single-instance lock (`logs/scheduler.pid`). Collect timestamped observations in `RepositorySnapshot` with interval throttling (`SNAPSHOT_MIN_INTERVAL_MINUTES`). Enforce that 24h, 7d, and 30d star growth is computed strictly across verified historical snapshots, explicitly returning `insufficient_data` when fewer than 2 observations exist over time.
- **Rationale**:
  - Eliminates scheduler interference with Streamlit's reactive reload model.
  - Prevents race conditions and multiple scheduler daemons from spamming GitHub API rate limits.
  - Upholds strict data integrity by prohibiting the fabrication of historical growth curves from point-in-time snapshot totals.
- **Consequences**:
  - The background scheduler runs as a separate CLI process (`python scheduler.py`).
  - Repositories without sufficient historical snapshots display transparent "Insufficient Data" state rather than deceptive zero or fabricated metrics.

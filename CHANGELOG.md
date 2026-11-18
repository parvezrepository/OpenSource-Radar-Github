# OpenSource Radar — Changelog

All notable changes to the OpenSource Radar project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

---

## [Phase 9: Cinematic Editorial Design System] — 2026-11-18

### Added
- **Cinematic Editorial Theme**: Complete visual refresh inspired by human-designed editorial publications:
  - Deep matte charcoal canvas (`#181818`), warm beige body text (`#EBDCC4`), muted sage metadata (`#B6A596`), coral-rust primary CTA buttons (`#DC9F85`), 1px deep earth borders (`#66473B`), and burnt umber dividers (`#35211A`).
  - Subtle 3.5% fractal noise SVG texture overlay across the viewport (`.stApp::before`).
  - Strict 4px geometric radius across all containers, metric blocks, input fields, tags, and action buttons (zero pill shapes or soft gradients).
  - High-impact display typography (`Syne` / geometric sans) with tight letter tracking and 4px offset layered outline depth effects.
- **Minimal Navigation & Landing Hero (`app.py`)**:
  - High-positioned protocol bar (`SD—PROTOCOL 01`), center 1px spacer, live telemetry status dot.
  - 12-column editorial content grid pairing an exclusivity mission statement with a dual-purpose access & repository scan console.
  - Rectangular topic badges (`.radar-tag`) and primary coral-rust dossier buttons (`🔬 Analyze`).

---

## [Phase 8: Telegram Alerts & Interactive Repository AI Chat] — 2026-11-18

### Added
- **Telegram Notification Service (`services/telegram_service.py`)**: Real-time push notification engine delivering structured HTML cards with star counts, opportunity score badges, descriptions, and direct links.
- **Background Dispatch Integration**: `scheduler_service.py` and `monitoring_service.py` automatically send Telegram alerts when high-velocity repositories or projects crossing score thresholds are discovered.
- **Telegram Diagnostics UI (`pages/12_Settings.py`)**: One-click "Test Telegram Bot" and "Send Sample Alert" buttons with instant bot verification and masked token display.
- **Interactive Repository AI Chat**:
  - Grounded AI conversational assistant in `pages/07_Repository_Analyzer.py` allowing developers to ask free-form questions about code architecture, Docker setup, and dependencies.
  - Quick-prompt action pills for 1-click inquiries (*Docker deployment*, *Real-world use cases*, *System architecture*, *Key dependencies*).
  - Strict prompt-injection XML isolation fences (`<untrusted_repository_content>`) in `ai/prompts.py`.
  - Deterministic offline intelligence fallback when no AI provider key is configured.
- **Automated Test Coverage**: Added `tests/test_telegram_service.py` and `tests/test_chat_with_repository.py` (total test suite expanded to 81/81 passed).

---

## [Phase 7: Full Integration, Testing & Production Polish] — 2026-11-17

### Added
- **Production UI/UX Design System**: Implemented clean, human-designed SaaS theme with Figma aesthetics:
  - Deep matte charcoal palette (`#0E1117` canvas, `#161B22` card containers, `#21262D` borders).
  - Modern Inter typography, rounded-pill topic tags (`.radar-pill`), and language color dots.
  - Minimalist sidebar with slim telemetry badges and responsive hover transitions on cards and buttons.
- **End-to-End Integration Test Suite (`tests/test_e2e_integration.py`)**: Verified all 20 end-to-end user workflows:

### Fixed
- **GitHub Search API Syntax**: Replaced unsupported multi-topic `OR` clauses (`topic:A OR topic:B`) in `core/search_engine.py` with valid single-topic qualifiers (`topic:ai-agents`, `topic:algorithmic-trading`, `topic:cybersecurity`, `topic:developer-tools`). All 9 discovery modes now return thousands of live repository results.
- **Client Singleton Token Passing**: Fixed default argument in `get_github_client` to `_TOKEN_UNSET` so that the shared instance respects `.env` `GITHUB_TOKEN` rather than falling back to unauthenticated public mode.
- **AI Analysis Schema & License Parsing**: Hardened `ai/prompts.py` against string representations of license fields and cleaned duplicate prompt dead code.
  1. Application initialization & database schema health.
  2. GitHub connection diagnostics.
  3. Technology classification via hierarchical taxonomy.
  4. Search query building with filters.
  5. Repository normalization & SQLite deduplication.
  6. Bookmarking & saved repository management.
  7. Repository details & zero-code-execution source inspection (binary rejection + 100KB guard).
  8. Static README and dependency manifest parsing.
  9. AI Provider structured analysis with strict Pydantic v2 schemas.
  10. Deterministic offline fallback analysis.
  11. Multi-repository side-by-side comparison matrix (2–5 projects) with dependency overlap detection.
  12. Explainable 5-pillar Content Opportunity Scoring (0–100).
  13. Multi-platform content synthesis (YouTube, Shorts, Social, Telegram, Blog, Tutorials).
  14. Multilingual draft generation (English, Bengali, Banglish).
  15. In-dashboard draft editing and persistence in SQLite.
  16. Structured export to Markdown (`.md`) and Plain Text (`.txt`).
  17. Scheduled discovery job configuration and cron parsing.
  18. Standalone scheduler execution with single-instance PID locking (`python scheduler.py --once`).
  19. Historical point-in-time snapshot collection (`RepositorySnapshot`).
  20. Trend analytics with verified 24h, 7d, and 30d star growth and Plotly time-series curves.
- **Production Documentation**: Complete operational guide in `README.md` covering all 12 pages, CLI flags (`--status`, `--once`), troubleshooting tips, and security policies.
- **Full Test Suite Verification**: Total automated test suite passing at 70/70 tests with zero failures across 14 test modules.

## [Phase 6: Automation, Historical Analytics & Monitoring] — 2026-11-17

### Added
- **Historical Trend Tracker (`core/trend_tracker.py`)**: Time-series analysis engine calculating observed 24-hour, 7-day, and 30-day star velocity and percentages exclusively from verified point-in-time snapshots in `RepositorySnapshot`. Strictly rejects metric fabrication and marks insufficient historical data when fewer than 2 snapshots exist.
- **Single-Instance Scheduler Daemon (`scheduler.py`)**: Standalone APScheduler runner running as an isolated Python process (`python scheduler.py`). Features cross-platform PID lockfile acquisition (`logs/scheduler.pid`), graceful shutdown handlers (`SIGINT`, `SIGTERM`), periodic job refresh, `--status` health checks, and `--once` execution mode.
- **Discovery Automation Service (`services/scheduler_service.py`)**: Manages recurring discovery jobs and execution logging (`DiscoveryJob`, `DiscoveryLog`). Automatically seeds 4 default background radars (AI Daily Radar, Agents 6-Hour Radar, Trading & FinTech Monitor, and Snapshot Collector) and handles API failures and rate limits defensively.
- **Extensible Notification Service (`services/monitoring_service.py`)**: Multi-provider alert system broadcasting discoveries, high-potential repository alerts (stars >= 1,000), new releases, and job failures to application logs (`logs/monitoring.log`) and optional Telegram Bot (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
- **Interactive Analytics Dashboard (`pages/11_Analytics.py`)**: 4-tab intelligence view featuring Plotly time-series growth curves, category donut distribution, language frequency bar charts, content score histograms, real-time background scheduler process status, on-demand job execution, and recent run logs.
- **Automated Test Suites**:
  - `tests/test_trend_tracker.py` (5 tests for interval throttling, insufficient data, 24h/7d growth calculation, and velocity ranking).
  - `tests/test_scheduler.py` (6 tests for default seeding, job CRUD, snapshot execution, rate-limit handling, notification dispatch, and PID locks).
  - Test suite expanded to 63 passed tests (0 failed).

## [Phase 5: Content Creation Studio] — 2026-11-17

### Added
- **Multi-Platform Content Schema (`ai/analysis.py`)**: Defined `ContentDraftSchema` Pydantic model enforcing strongly typed outputs (title, hook, body, practical explanation, visual demo suggestions, CTA, hashtags, source URL) and structured markdown export (`to_markdown()`).
- **Prompt Synthesis Engine (`ai/prompts.py`)**: Implemented `build_content_prompt` supporting 7 distribution platforms (YouTube Long-form, YouTube Shorts 30-60s, Facebook, Instagram Reel/Carousel, Telegram, Technical Blog, Tutorials) and 3 languages (English, Bengali, Banglish). Untrusted repo text remains isolated within `<untrusted_repository_content>` XML fences.
- **AI Provider Content Generation**: Extended `AIProvider`, `OpenAIProvider`, and `GeminiProvider` with `generate_content(...)` implementing structured JSON output with temperature calibration.
- **Deterministic Multi-Language Fallback Engine (`core/content_generator.py`)**: Multi-language, multi-platform template engine providing 100% offline generation capability using extracted README sections, verified facts, and detected manifests without AI API keys.
- **Content Service Layer (`services/content_service.py`)**: Business logic orchestrator handling draft generation, database persistence (`ContentDraft`), draft retrieval, listing, updates, and deletion.
- **Interactive Content Studio UI (`pages/09_Content_Studio.py`)**: Native Streamlit interface with dual tabs (Generator & Editor, Saved Drafts Library). Includes live title/hook/body/CTA editing, copyable code blocks, Markdown (`.md`) and Plain Text (`.txt`) downloads, and SQLite draft CRUD operations.
- **Automated Content Studio Tests (`tests/test_content_studio.py`)**: 5 unit and integration tests verifying schema validation, markdown serialization, prompt synthesis, deterministic fallback generation across English/Bengali/Banglish, and database draft lifecycle.

## [Phase 4: AI Intelligence Engine] — 2026-11-17

### Added
- **AI Provider Abstraction (`ai/provider.py`)**: Abstract base class `AIProvider` defining connection testing and structured repository analysis. Supports dynamic factory instantiation (`get_ai_provider`) with seamless offline fallback when credentials are absent.
- **OpenAI GPT Provider (`ai/openai_provider.py`)**: Production-grade integration using OpenAI Python SDK with JSON mode (`response_format={"type": "json_object"}`), temperature pinning, and error wrapping (`AIAuthError`, `AIRateLimitError`, `AITimeoutError`).
- **Google Gemini Provider (`ai/gemini_provider.py`)**: Provider implementation using `google.generativeai` with JSON response MIME types and markdown block stripping.
- **Hardened Prompt Safety Fences (`ai/prompts.py`)**: Strict isolation wrapping untrusted repository content, README excerpts, and file paths inside `<untrusted_repository_content>` tags. Explicit system rules instructing models to reject prompt-injection directives and ground claims in evidence.
- **Pydantic Output Validation (`ai/analysis.py`)**: Strongly-typed `StructuredAnalysis` schema validating plain-language explanations, system architecture, detected technologies, important source files with responsibilities, key functions, practical applications, implementation details, limitations, learning takeaways, research topics, and cited evidence.
- **Dashboard AI Integration (`pages/07_Repository_Analyzer.py`)**: Added "Analyze with AI" trigger, persistent DB caching to eliminate redundant API expenditure, and dedicated AI research dossier display card.
- **Test Suite (`tests/test_ai_provider.py`)**: Added 5 comprehensive tests validating schema validation, prompt injection fences, provider factory fallbacks, mocked OpenAI completions, and deterministic non-AI operation.

## [Phase 3: Repository Intelligence & Analysis] — 2026-11-17

### Added
- **Repository Deep Analyzer (`core/repository_analyzer.py`)**: Static intelligence engine retrieving metadata, language byte distributions, releases, commit cadences, file trees, and dependency manifests. Parses README markdown sections into problem statement, features, installation, usage, and limitations.
- **Strict Zero-Code-Execution Source Inspector**: Safe text file browser with 100KB size guard and immediate rejection of binary file types (`.so`, `.dll`, `.exe`, `.bin`, `.png`, `.zip`, `.pyc`, etc.).
- **Static Dependency Manifest Parser**: Extracted dependencies from `requirements.txt`, `pyproject.toml`, `package.json`, and `Cargo.toml` without dynamic execution or package installation.
- **Explainable 0–100 Content Opportunity Scoring Engine (`core/scoring_engine.py`)**: Multi-dimensional editorial ranking evaluating:
  1. Trend Momentum (25 pts)
  2. Uniqueness (20 pts)
  3. Practical Usefulness (20 pts)
  4. Content Appeal (20 pts)
  5. Project Quality Signals (15 pts)
  Outputs granular positive justifications, missing signal flags, and preliminary markers.
- **Multi-Repository Comparison Matrix Engine (`core/comparison_engine.py`)**: Evaluates 2 to 5 repositories side-by-side across metrics, dependency overlap, licenses, and trade-offs.
- **Dashboard Enhancements**:
  - `pages/07_Repository_Analyzer.py`: Connected multi-tab dossier interface (Overview, Technologies, Features, Architecture, Source Files, Documentation, Health, Content Opportunities) with persistent storage in `RepositoryAnalysis`.
  - `pages/08_Compare.py`: Connected interactive side-by-side comparison matrix with bookmark selectors and shared dependency analysis.
- **Extended Test Suite**:
  - `tests/test_analyzer.py` (5 tests for README parsing, missing docs, manifests, binary rejection, size limits)
  - `tests/test_scoring.py` (2 tests for 5-pillar calculation and explanatory reasons)
  - `tests/test_compare.py` (2 tests for 2-5 repo comparison and bounds validation)

## [Phase 2: Global GitHub Discovery Engine] — 2026-11-17

### Added
- **Technology Taxonomy & Classifier (`core/categorizer.py`)**: Built hierarchical categorization supporting Artificial Intelligence, AI Agents & Automation, Software Development, Cybersecurity, Trading & FinTech, and Emerging Technologies across 60+ subcategories with custom domain extensibility.
- **Advanced Query Builder (`core/search_engine.py`)**: Comprehensive GitHub search query generator supporting 9 discovery modes (Trending, Hidden Gems, New Repositories, Recently Updated, AI Agents, Trading & FinTech, Cybersecurity, DevTools, and Custom Search) with fine-grained parameter qualifiers (language, stars, forks, dates, user, org, archived).
- **Core Discovery Engine (`core/discovery_engine.py`)**: Real GitHub public discovery engine extracting and normalizing all 16 required repository fields, assigning taxonomy domains, and persisting deduplicated records into SQLite.
- **Discovery Service Layer (`services/discovery_service.py`)**: Service orchestrator bridging the Streamlit UI and discovery engines.
- **Standardized Repository Card (`utils/helpers.py`)**: Native Streamlit UI card component displaying metadata, topics, star/fork metrics, live Save/Bookmark actions, and one-click "Analyze" navigation.
- **Multipage Dashboard Enhancements**:
  - `pages/02_Discover.py`: Deep search interface with multi-filter query builder and real-time Search History log tab.
  - `pages/03_Trending.py`: Trending projects radar tracking push velocity and traction.
  - `pages/04_Hidden_Gems.py`: Under-the-radar discovery radar surfacing high-potential low-visibility repositories.
  - `pages/05_AI_Agents.py`: Curated agentic framework and MCP server discovery.
  - `pages/06_Trading_FinTech.py`: Curated algorithmic trading, crypto bot, and quant discovery.
- **Test Suites**:
  - `tests/test_search_engine.py` (5 tests for query syntax and modes)
  - `tests/test_discovery.py` (6 tests for classification, normalization, pagination, deduplication, and rate-limit handling)

## [Phase 1: Core Foundation & Python Dashboard] — 2026-11-17

### Added
- **Configuration Management (`config.py`)**: Pydantic BaseSettings loading from `.env`, strict path resolution, secure secret masking (`_mask_secret`, `masked_github_token`, `masked_openai_key`, `masked_gemini_key`), and zero-leak string representations.
- **Resilient GitHub REST Client (`core/github_client.py`)**: Shared, singleton-capable client supporting authentication, rate limit parsing, exponential retry backoff, caching, and custom exception hierarchy (`GitHubAPIError`, `GitHubAuthError`, `GitHubRateLimitError`, `GitHubNotFoundError`, `GitHubValidationError`).
- **Rate Limiter Guard (`core/rate_limiter.py`)**: Real-time quota and reset tracker extracting `X-RateLimit-*` headers to proactively defend against 403 throttling.
- **In-Memory TTL Cache (`core/cache.py`)**: Lightweight thread-safe cache preventing duplicate external API calls during UI navigation.
- **Database Engine & WAL Mode (`database/connection.py`)**: Thread-safe SQLAlchemy connection pool with automatic SQLite `PRAGMA journal_mode=WAL;` and `PRAGMA foreign_keys=ON;`.
- **Declarative ORM Schema (`database/models.py`)**: Defined all 10 core entities:
  - `Repository`, `RepositorySnapshot`, `RepositoryAnalysis`, `ContentDraft`, `SavedRepository`, `SearchHistory`, `DiscoveryJob`, `DiscoveryLog`, `Category`, `AppSettings`.
- **Category Seed Migration (`database/migrations.py`)**: Auto-creates tables and seeds 8 primary technology domains.
- **Data Access Object (`database/repository_store.py`)**: High-level CRUD operations for repository upserts, deduplication by `github_id`, bookmarking, search logging, and dashboard statistics.
- **Native Streamlit Multipage Dashboard**:
  - `app.py`: Main router with real-time database metrics and telemetry.
  - `pages/01_Overview.py`: Operational dashboard with DB stats, infrastructure health cards, and recent discovery activity.
  - `pages/02_Discover.py`: Multi-filter search engine querying live GitHub REST API.
  - `pages/03_Trending.py`: Trending projects radar shell.
  - `pages/04_Hidden_Gems.py`: High-potential under-the-radar radar shell.
  - `pages/05_AI_Agents.py`: Autonomous agents and MCP servers radar shell.
  - `pages/06_Trading_FinTech.py`: Quantitative finance and crypto bots radar shell.
  - `pages/07_Repository_Analyzer.py`: Deep technical dossier multi-tab layout with zero-code-execution notice.
  - `pages/08_Compare.py`: Side-by-side comparison matrix shell.
  - `pages/09_Content_Studio.py`: Multi-platform educational content studio shell.
  - `pages/10_Saved_Projects.py`: Bookmarked repository manager with live DB removal.
  - `pages/11_Analytics.py`: Historical analytics trajectory shell.
  - `pages/12_Settings.py`: Diagnostic suite with live GitHub connection test, rate limit gauges, DB test, and cache clearing.
- **Automated Test Suites**:
  - `tests/test_config.py` (3 tests)
  - `tests/test_database.py` (5 tests)
  - `tests/test_github_client.py` (7 tests)
  - `tests/test_dashboard_imports.py` (1 test checking all 12 pages + `app.py`)

## [Phase 0: Project Initialization & Architecture] — 2026-11-17

### Added
- **Project Structure**: Created core directory hierarchy:
  - `pages/` (12 multipage Streamlit views)
  - `core/` (GitHub client, engines, scoring, ranking)
  - `ai/` (OpenAI & Gemini providers, prompt templates, output models)
  - `database/` (SQLAlchemy connection, models, store, migrations)
  - `services/` (Discovery, monitoring, content, scheduler services)
  - `utils/` (Formatters, validators, logging, helpers)
  - `data/`, `logs/`, `tests/`
- **Dependencies (`requirements.txt`)**: Defined and pinned all dependencies for Python 3.11+ (Streamlit, SQLAlchemy, Plotly, Pandas, APScheduler, OpenAI, Google Generative AI, Pydantic, HTTPX, Requests, Pytest).
- **Environment Template (`.env.example`)**: Created template for GitHub PAT, AI credentials, database URL, and logging settings.
- **Git Ignore (`.gitignore`)**: Configured exclusions for SQLite databases, environment secrets, logs, cache, and virtual environments.
- **Documentation (`README.md`)**: Comprehensive project overview, quickstart instructions, and security guidelines.
- **Mandatory Memory Files**:
  - `PROJECT_CONTEXT.md` (System vision, operational principles, non-negotiables)
  - `IMPLEMENTATION_PLAN.md` (Phased roadmap and milestone criteria)
  - `ARCHITECTURE.md` (Subsystems, ER diagram, contracts, threat model)
  - `DECISIONS.md` (ADRs 001–007)
  - `CHANGELOG.md` (Initial changelog)
  - `TEST_REPORT.md` (Test framework setup and Phase 0 verification)
  - `CURRENT_STATUS.md` (Phase 0 completion status)

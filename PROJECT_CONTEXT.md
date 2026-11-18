# OpenSource Radar — Project Context & Permanent Memory

## 1. Project Overview & Vision

**OpenSource Radar** is an enterprise-grade, Python-native technology intelligence and content discovery platform. It automates the discovery, static technical analysis, historical trajectory tracking, and educational content synthesis of emerging and high-impact open-source GitHub repositories.

The platform bridges the gap between raw open-source codebase activity on GitHub and actionable intelligence for software engineers, tech creators, educators, and technology researchers.

---

## 2. Core Operational Principles & Non-Negotiables

### A. Strict Python-Only Architecture
- **Language**: Python 3.11+ exclusively.
- **UI Framework**: Native Streamlit components.
- **Persistence**: SQLite with SQLAlchemy 2.0+ ORM (WAL mode enabled for concurrent background writes).
- **Automation**: APScheduler running in an isolated background process.
- **Network**: Requests and HTTPX with exponential backoff and rate limiting.
- **Validation**: Pydantic v2 and `pydantic-settings`.
- **Prohibited**: Under no circumstances shall JavaScript, TypeScript, React, Next.js, Vue, Angular, Node.js, Express, or custom HTML/JS frontend scripts be introduced.

### B. Continuity & Preservation
- Incremental, phased development.
- Zero regression policy: Every phase builds directly on the previous phase and reuses shared services.
- Never recreate existing models, clients, or services unless technically justified and documented in `DECISIONS.md`.
- No mock data in live discovery mode: Only actual data retrieved from GitHub REST API is presented to users. Mocking is restricted exclusively to automated unit tests (`tests/`).

### C. Factual Integrity & Transparent State
- Never claim a feature works without executing verified tests.
- Clearly differentiate between:
  1. Verified repository facts (metadata, file existence, commit history).
  2. README claims (unverified author assertions).
  3. Source-code observations (detected dependencies, language statistics).
  4. AI-generated interpretations (model synthesis).
  5. Missing or unavailable metrics.
- Missing credentials (e.g., absence of `OPENAI_API_KEY` or `GITHUB_TOKEN`) must gracefully degrade the system without crashing the UI or blocking core browsing features.

### D. Security & Safe Execution
- **Zero Execution Policy**: Repository source code, scripts, configuration files, and binaries are NEVER executed or evaluated dynamically.
- **Prompt Injection Defense**: Repository content is treated strictly as untrusted input data, isolated using delimiter tags, and never passed directly as instructions to AI models.
- **Secret Protection**: API tokens are read securely from environment variables, never logged, and masked in all UI representations.

---

## 3. Core Functional Modules

| Module | Purpose | Key Technologies |
| :--- | :--- | :--- |
| **GitHub Client & Core Engines** | REST API consumption, rate limit tracking, caching, search querying | `requests`, `httpx`, `core/` |
| **Database & Repository Store** | Relational schema, deduplication, snapshotting, migration | `SQLAlchemy 2.0`, `SQLite`, `database/` |
| **Technology Discovery Engine** | Domain curation (AI, Agents, Trading, Security, DevTools) & search modes | `core/discovery_engine.py`, `core/search_engine.py` |
| **Repository Analyzer** | Static file tree inspection, dependency parsing, health scoring | `core/repository_analyzer.py` |
| **Content Opportunity Scorer** | 0–100 explainable ranking model based on 5 objective pillars | `core/scoring_engine.py` |
| **Comparison Engine** | 2–5 repository side-by-side technical matrix | `core/comparison_engine.py` |
| **AI Intelligence Engine** | Structured research synthesis with OpenAI & Gemini | `openai`, `google-generativeai`, `ai/` |
| **Content Creation Studio** | Multi-platform, multi-language (EN, BN, Banglish) educational drafts | `services/content_service.py` |
| **Background Scheduler** | Autonomous periodic discovery and historical snapshot capture | `APScheduler`, `scheduler.py` |
| **Streamlit Dashboard** | Multipage SaaS-style dark UI with interactive Plotly visual analytics | `streamlit`, `plotly`, `pages/` |

---

## 4. Mandatory Memory Files & Roles

1. `PROJECT_CONTEXT.md` *(This file)*: Permanent foundational reference, principles, and module overview.
2. `IMPLEMENTATION_PLAN.md`: Granular phase-by-phase roadmap, milestones, and technical tasks.
3. `ARCHITECTURE.md`: Technical design, system component interactions, data models, and API interfaces.
4. `DECISIONS.md`: Architectural Decision Records (ADR), technical trade-offs, and design rationale.
5. `CHANGELOG.md`: Chronological log of code additions, modifications, and bug fixes per phase.
6. `TEST_REPORT.md`: Comprehensive test execution records, pass/fail statuses, and test scenarios.
7. `CURRENT_STATUS.md`: Live tracking of the active phase, completed milestones, blockers, and next actions.

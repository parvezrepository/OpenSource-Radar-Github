"""Static repository intelligence, README parsing, dependency detection, and evidence extraction."""

from datetime import datetime, timezone
import logging
import re
from typing import Any, Optional
from core.github_client import GitHubClient, get_github_client
from database.connection import get_db
from database.models import Repository, RepositoryAnalysis

logger = logging.getLogger("opensource_radar.analyzer")


class RepositoryAnalyzer:
    """Performs strict static analysis on repository metadata, README, and dependency files."""

    def __init__(self, github_client: Optional[GitHubClient] = None) -> None:
        self.client = github_client or get_github_client()

    @staticmethod
    def parse_readme_sections(readme_text: Optional[str]) -> dict[str, str]:
        """Extract structured sections from markdown README using regex headers."""
        if not readme_text or not readme_text.strip():
            return {
                "overview": "No README documentation found in repository.",
                "problem_solved": "Not specified in repository README.",
                "features": "Not specified in repository README.",
                "installation": "Not specified in repository README.",
                "usage": "Not specified in repository README.",
                "limitations": "Not specified in repository README.",
            }

        text = readme_text.strip()
        lines = text.splitlines()

        sections: dict[str, list[str]] = {
            "overview": [],
            "problem_solved": [],
            "features": [],
            "installation": [],
            "usage": [],
            "limitations": [],
            "other": [],
        }

        current_section = "overview"

        for line in lines:
            header_match = re.match(r"^#{1,4}\s+(.*)", line.strip())
            if header_match:
                title = header_match.group(1).lower()
                if any(k in title for k in ["why", "problem", "background", "motivation", "about"]):
                    current_section = "problem_solved"
                elif any(k in title for k in ["feature", "capability", "highlights", "what can"]):
                    current_section = "features"
                elif any(k in title for k in ["install", "setup", "getting started", "quick start", "prerequisites"]):
                    current_section = "installation"
                elif any(k in title for k in ["usage", "how to use", "example", "tutorial"]):
                    current_section = "usage"
                elif any(k in title for k in ["limitation", "caveat", "known issue", "roadmap", "todo"]):
                    current_section = "limitations"
                else:
                    if not sections["overview"]:
                        current_section = "overview"
                    else:
                        current_section = "other"
            else:
                sections[current_section].append(line)

        return {
            "overview": "\n".join(sections["overview"]).strip() or text[:500],
            "problem_solved": "\n".join(sections["problem_solved"]).strip() or "README does not explicitly articulate a problem statement.",
            "features": "\n".join(sections["features"]).strip() or "No dedicated feature list found in README headers.",
            "installation": "\n".join(sections["installation"]).strip() or "No dedicated installation instructions found in README headers.",
            "usage": "\n".join(sections["usage"]).strip() or "No dedicated usage section found in README.",
            "limitations": "\n".join(sections["limitations"]).strip() or "No known limitations or caveats reported in README.",
        }

    @staticmethod
    def parse_manifest_dependencies(filename: str, content: str) -> list[str]:
        """Extract dependency package names from standard package manifests without executing code."""
        dependencies: list[str] = []
        fn = filename.lower()

        if "requirements" in fn or fn.endswith(".txt"):
            for line in content.splitlines():
                clean = line.strip()
                if clean and not clean.startswith("#") and not clean.startswith("-"):
                    pkg_name = re.split(r"[><=~!]", clean)[0].strip()
                    if pkg_name:
                        dependencies.append(pkg_name)

        elif "pyproject.toml" in fn:
            # Simple static regex extraction for dependencies = [...]
            in_dep_block = False
            for line in content.splitlines():
                if "dependencies" in line and "=" in line:
                    in_dep_block = True
                    continue
                if in_dep_block:
                    if "]" in line:
                        in_dep_block = False
                        break
                    match = re.search(r'["\']([a-zA-Z0-9_\-]+)', line)
                    if match:
                        dependencies.append(match.group(1))

        elif "package.json" in fn:
            # Static regex for dependencies and devDependencies
            matches = re.findall(r'"([a-zA-Z0-9@/_\-]+)"\s*:\s*"[^"]+"', content)
            dependencies.extend([m for m in matches if not m.startswith("node:")])

        elif "cargo.toml" in fn:
            in_deps = False
            for line in content.splitlines():
                if re.match(r"^\[.*dependencies.*\]", line):
                    in_deps = True
                    continue
                elif line.startswith("["):
                    in_deps = False
                if in_deps:
                    match = re.match(r"^([a-zA-Z0-9_\-]+)\s*=", line.strip())
                    if match:
                        dependencies.append(match.group(1))

        return list(dict.fromkeys(dependencies))[:50]  # Deduplicate and cap at 50

    @staticmethod
    def detect_technologies(languages: dict[str, int], dependencies: list[str], topics: list[str]) -> dict[str, list[str]]:
        """Categorize detected technologies into languages, frameworks, libraries, and databases."""
        framework_catalog = {
            "fastapi": "FastAPI",
            "flask": "Flask",
            "django": "Django",
            "react": "React",
            "next": "Next.js",
            "express": "Express",
            "pytorch": "PyTorch",
            "torch": "PyTorch",
            "tensorflow": "TensorFlow",
            "keras": "Keras",
            "langchain": "LangChain",
            "llamaindex": "LlamaIndex",
            "autogen": "AutoGen",
            "crewai": "CrewAI",
            "streamlit": "Streamlit",
            "playwright": "Playwright",
            "selenium": "Selenium",
        }

        database_catalog = {
            "sqlalchemy": "SQLAlchemy",
            "sqlite3": "SQLite",
            "psycopg2": "PostgreSQL",
            "asyncpg": "PostgreSQL",
            "redis": "Redis",
            "pymongo": "MongoDB",
            "chromadb": "ChromaDB",
            "pinecone": "Pinecone",
            "qdrant": "Qdrant",
            "weaviate": "Weaviate",
            "milvus": "Milvus",
        }

        found_frameworks = set()
        found_databases = set()
        dep_lower = [d.lower() for d in dependencies] + [t.lower() for t in topics]

        for key, name in framework_catalog.items():
            if any(key in d for d in dep_lower):
                found_frameworks.add(name)

        for key, name in database_catalog.items():
            if any(key in d for d in dep_lower):
                found_databases.add(name)

        return {
            "languages": list(languages.keys()),
            "frameworks": sorted(list(found_frameworks)),
            "databases": sorted(list(found_databases)),
            "dependencies": dependencies[:30],
        }

    def analyze_repository(self, owner: str, repo: str) -> dict[str, Any]:
        """
        Conduct full static intelligence analysis on a repository.
        Returns a structured evidence dossier separating verified facts, README claims, and observations.
        """
        # 1. Fetch metadata & language breakdown
        repo_data = self.client.get_repository(owner, repo)
        languages = self.client.get_languages(owner, repo)
        readme_raw = self.client.get_readme(owner, repo)
        latest_release = self.client.get_latest_release(owner, repo)
        recent_commits = self.client.get_recent_commits(owner, repo, limit=5)
        tree = self.client.get_file_tree(owner, repo, branch=repo_data.get("default_branch", "main"))

        # 2. Inspect file tree for manifests and test folders
        tree_paths = [item.get("path", "") for item in tree]
        manifest_files = [
            p for p in tree_paths
            if any(m in p.lower() for m in ["requirements.txt", "pyproject.toml", "package.json", "cargo.toml", "go.mod"])
        ]
        has_tests = any("test" in p.lower() for p in tree_paths)
        has_ci = any(".github/workflows" in p.lower() for p in tree_paths)
        has_docker = any("dockerfile" in p.lower() or "docker-compose" in p.lower() for p in tree_paths)

        # 3. Read first primary dependency manifest if present (max 100KB)
        dependencies: list[str] = []
        if manifest_files:
            target_manifest = manifest_files[0]
            manifest_content, err = self.client.get_file_content(owner, repo, target_manifest, max_size_kb=100)
            if manifest_content:
                dependencies = self.parse_manifest_dependencies(target_manifest, manifest_content)

        # 4. Parse README sections
        readme_sections = self.parse_readme_sections(readme_raw)

        # 5. Detect tech stack
        tech_detected = self.detect_technologies(languages, dependencies, repo_data.get("topics", []))

        # 6. Maintenance signals
        last_commit_date = None
        if recent_commits:
            commit_obj = recent_commits[0].get("commit", {})
            author_obj = commit_obj.get("author", {}) or commit_obj.get("committer", {})
            last_commit_date = author_obj.get("date")

        # 7. Formulate Evidence Dossier
        dossier = {
            "repository": {
                "github_id": repo_data.get("id"),
                "id": repo_data.get("id"),
                "full_name": repo_data.get("full_name") or f"{owner}/{repo}",
                "owner": owner,
                "name": repo,
                "html_url": repo_data.get("html_url") or f"https://github.com/{owner}/{repo}",
                "description": repo_data.get("description"),
                "stars": repo_data.get("stargazers_count", 0),
                "forks": repo_data.get("forks_count", 0),
                "open_issues": repo_data.get("open_issues_count", 0),
                "license": repo_data.get("license", {}).get("name") if repo_data.get("license") else "No License Detected",
                "default_branch": repo_data.get("default_branch", "main"),
                "is_archived": repo_data.get("archived", False),
                "pushed_at": repo_data.get("pushed_at"),
            },
            "verified_facts": {
                "primary_language": repo_data.get("language") or "Unknown",
                "languages_byte_distribution": languages,
                "latest_release_tag": latest_release.get("tag_name") if latest_release else "No Published Releases",
                "latest_release_date": latest_release.get("published_at") if latest_release else "N/A",
                "last_commit_date": last_commit_date or repo_data.get("pushed_at", "N/A"),
                "recent_commits_count": len(recent_commits),
                "total_indexed_files": len(tree),
                "has_test_suite": has_tests,
                "has_ci_pipeline": has_ci,
                "has_dockerfile": has_docker,
            },
            "readme_claims": {
                "overview": readme_sections["overview"],
                "problem_solved": readme_sections["problem_solved"],
                "features_claimed": readme_sections["features"],
                "installation_process": readme_sections["installation"],
                "usage_instructions": readme_sections["usage"],
                "limitations_reported": readme_sections["limitations"],
            },
            "source_code_observations": {
                "manifest_detected": manifest_files[:3],
                "dependencies_parsed": dependencies,
                "detected_technologies": tech_detected,
            },
            "ai_interpretations": {
                "status": "Pending AI Intelligence (Phase 4)",
                "note": "AI analysis requires active OpenAI or Gemini credentials configured in Phase 4.",
            },
            "unknown_information": [
                "Production reliability benchmarks (unverified in static analysis)",
                "Complete private runtime configurations",
                "Internal proprietary data pipelines",
            ],
            "raw_readme": readme_raw,
            "file_tree": tree_paths[:200],  # Limit to first 200 files for UI display
        }

        return dossier

    @staticmethod
    def persist_analysis(
        repository_id: int,
        dossier: dict[str, Any],
        score: int,
        score_breakdown: dict[str, Any],
    ) -> RepositoryAnalysis:
        """Store or update the static research dossier in the database."""
        with get_db() as session:
            existing = session.query(RepositoryAnalysis).filter(
                RepositoryAnalysis.repository_id == repository_id
            ).first()

            claims = dossier.get("readme_claims", {})
            obs = dossier.get("source_code_observations", {})

            if existing:
                existing.summary = claims.get("overview")
                existing.problem_solved = claims.get("problem_solved")
                existing.detected_technologies = obs.get("detected_technologies", {})
                existing.key_features = [claims.get("features_claimed", "")]
                existing.dependencies = obs.get("dependencies_parsed", [])
                existing.limitations = [claims.get("limitations_reported", "")]
                existing.content_opportunity_score = score
                existing.score_breakdown = score_breakdown
                existing.analysis_type = "static"
                existing.analyzed_at = datetime.now(timezone.utc)
                analysis_record = existing
            else:
                analysis_record = RepositoryAnalysis(
                    repository_id=repository_id,
                    summary=claims.get("overview"),
                    problem_solved=claims.get("problem_solved"),
                    detected_technologies=obs.get("detected_technologies", {}),
                    key_features=[claims.get("features_claimed", "")],
                    dependencies=obs.get("dependencies_parsed", []),
                    limitations=[claims.get("limitations_reported", "")],
                    content_opportunity_score=score,
                    score_breakdown=score_breakdown,
                    analysis_type="static",
                    analyzed_at=datetime.now(timezone.utc),
                )
                session.add(analysis_record)

            return analysis_record

    def analyze_with_ai(
        self,
        owner: str,
        repo: str,
        force_refresh: bool = False,
    ) -> tuple[Any, RepositoryAnalysis]:
        """
        Run structured AI intelligence analysis using configured AI provider.
        Checks database cache first to avoid repeating expensive API calls.
        """
        from ai.provider import AIError, get_ai_provider
        from config import get_settings

        ai_provider = get_ai_provider()
        if not ai_provider:
            raise AIError(
                "No active AI credentials configured. Please set OPENAI_API_KEY or GEMINI_API_KEY in .env."
            )

        # 1. Fetch static dossier
        dossier = self.analyze_repository(owner, repo)
        repo_data = dossier["repository"]

        # Ensure repo exists in database
        from database.repository_store import RepositoryStore
        repo_record = RepositoryStore.upsert_repository(repo_data)

        # 2. Check if existing AI analysis exists and force_refresh is False
        with get_db() as session:
            existing = session.query(RepositoryAnalysis).filter(
                RepositoryAnalysis.repository_id == repo_record.id,
                RepositoryAnalysis.analysis_type.like("ai_%"),
            ).first()

            if existing and not force_refresh:
                from ai.analysis import ImportantFileInsight, StructuredAnalysis
                logger.info(f"Returning cached AI analysis for {owner}/{repo}")
                imp_files = [ImportantFileInsight(**f) for f in existing.detected_technologies.get("important_files", [])]
                cached_ai = StructuredAnalysis(
                    simple_explanation=existing.summary or "",
                    technical_architecture=existing.architecture_overview or "",
                    identified_technologies=existing.detected_technologies.get("languages", []),
                    important_files=imp_files,
                    key_functions=existing.key_features or [],
                    practical_applications=[existing.problem_solved or ""],
                    implementation_details=existing.score_breakdown.get("implementation_details", []),
                    limitations=existing.limitations or [],
                    learning_opportunities=existing.learning_opportunities or [],
                    potential_research_topics=existing.score_breakdown.get("research_topics", []),
                    evidence_sources=existing.score_breakdown.get("evidence_sources", []),
                )
                return cached_ai, existing

        # 3. Call AI provider
        obs = dossier["source_code_observations"]
        ai_res = ai_provider.analyze_repository(
            repo_data=repo_data,
            readme_content=dossier.get("raw_readme"),
            tree_summary=dossier.get("file_tree", []),
            detected_technologies=obs.get("detected_technologies", {}),
            dependencies=obs.get("dependencies_parsed", []),
        )

        # 4. Calculate content score
        from core.scoring_engine import scoring_engine
        score_report = scoring_engine.calculate_score(dossier)

        # 5. Persist AI analysis in SQLite
        settings = get_settings()
        with get_db() as session:
            existing_rec = session.query(RepositoryAnalysis).filter(
                RepositoryAnalysis.repository_id == repo_record.id
            ).first()

            score_data = score_report.to_dict()
            score_data["implementation_details"] = ai_res.implementation_details
            score_data["research_topics"] = ai_res.potential_research_topics
            score_data["evidence_sources"] = ai_res.evidence_sources

            tech_store = {
                "languages": ai_res.identified_technologies,
                "important_files": [f.model_dump() for f in ai_res.important_files],
            }

            if existing_rec:
                existing_rec.summary = ai_res.simple_explanation
                existing_rec.architecture_overview = ai_res.technical_architecture
                existing_rec.problem_solved = "\n".join(ai_res.practical_applications)
                existing_rec.key_features = ai_res.key_functions
                existing_rec.detected_technologies = tech_store
                existing_rec.learning_opportunities = ai_res.learning_opportunities
                existing_rec.limitations = ai_res.limitations
                existing_rec.content_opportunity_score = score_report.total_score
                existing_rec.score_breakdown = score_data
                existing_rec.analysis_type = f"ai_{settings.AI_PROVIDER}"
                existing_rec.analyzed_at = datetime.now(timezone.utc)
                saved_analysis = existing_rec
            else:
                saved_analysis = RepositoryAnalysis(
                    repository_id=repo_record.id,
                    summary=ai_res.simple_explanation,
                    architecture_overview=ai_res.technical_architecture,
                    problem_solved="\n".join(ai_res.practical_applications),
                    key_features=ai_res.key_functions,
                    detected_technologies=tech_store,
                    learning_opportunities=ai_res.learning_opportunities,
                    limitations=ai_res.limitations,
                    content_opportunity_score=score_report.total_score,
                    score_breakdown=score_data,
                    analysis_type=f"ai_{settings.AI_PROVIDER}",
                    analyzed_at=datetime.now(timezone.utc),
                )
                session.add(saved_analysis)

            return ai_res, saved_analysis

    def chat(
        self,
        dossier: dict[str, Any],
        query: str,
        chat_history: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """Interactive Q&A assistant grounded in the repository dossier."""
        from ai.provider import get_ai_provider
        ai_provider = get_ai_provider()
        if ai_provider:
            return ai_provider.chat_with_repository(dossier, query, chat_history=chat_history)

        # Deterministic offline fallback
        repo = dossier.get("repository", {})
        facts = dossier.get("verified_facts", {})
        obs = dossier.get("source_code_observations", {})
        frameworks = obs.get("detected_technologies", {}).get("frameworks", [])
        deps = obs.get("dependencies_parsed", [])
        return (
            f"**[Offline Intelligence Mode]**\n\n"
            f"Here are verified facts about **{repo.get('full_name')}**:\n\n"
            f"- **Primary Language**: `{facts.get('primary_language', 'N/A')}`\n"
            f"- **Stars**: {repo.get('stars', 0):,} | **Forks**: {repo.get('forks', 0):,}\n"
            f"- **Test Suite**: {'✅ Detected' if facts.get('has_test_suite') else '❌ Not detected'}\n"
            f"- **Docker Support**: {'✅ Dockerfile present' if facts.get('has_dockerfile') else '❌ No Dockerfile'}\n"
            f"- **Frameworks**: {', '.join(frameworks) if frameworks else 'Standard Library'}\n"
            f"- **Key Dependencies**: {', '.join(deps[:10]) if deps else 'None parsed'}\n\n"
            f"*To unlock generative AI Q&A with deep code reasoning, configure OPENAI_API_KEY in `.env`.*"
        )


# Global repository analyzer instance
repository_analyzer = RepositoryAnalyzer()

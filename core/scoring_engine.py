"""Explainable 0–100 Content Opportunity Scoring Engine for OpenSource Radar."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Optional


@dataclass
class PillarScore:
    """Individual scoring component with point allocation and explanations."""
    name: str
    score: int
    max_score: int
    reasons: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "max_score": self.max_score,
            "reasons": self.reasons,
            "missing": self.missing,
        }


@dataclass
class ContentOpportunityReport:
    """Overall 0–100 explainable editorial score report."""
    total_score: int
    is_preliminary: bool
    editorial_verdict: str
    trend_momentum: PillarScore
    uniqueness: PillarScore
    practical_usefulness: PillarScore
    content_appeal: PillarScore
    quality_signals: PillarScore

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_score": self.total_score,
            "is_preliminary": self.is_preliminary,
            "editorial_verdict": self.editorial_verdict,
            "pillars": {
                "trend_momentum": self.trend_momentum.to_dict(),
                "uniqueness": self.uniqueness.to_dict(),
                "practical_usefulness": self.practical_usefulness.to_dict(),
                "content_appeal": self.content_appeal.to_dict(),
                "quality_signals": self.quality_signals.to_dict(),
            },
            "all_reasons": (
                self.trend_momentum.reasons
                + self.uniqueness.reasons
                + self.practical_usefulness.reasons
                + self.content_appeal.reasons
                + self.quality_signals.reasons
            ),
            "missing_signals": (
                self.trend_momentum.missing
                + self.uniqueness.missing
                + self.practical_usefulness.missing
                + self.content_appeal.missing
                + self.quality_signals.missing
            ),
        }


class ScoringEngine:
    """Computes transparent, explainable 0–100 content opportunity scores."""

    @staticmethod
    def _parse_pushed_date(pushed_at: Any) -> Optional[datetime]:
        if isinstance(pushed_at, datetime):
            return pushed_at
        elif isinstance(pushed_at, str):
            try:
                return datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def calculate_score(
        self,
        dossier: dict[str, Any],
        has_historical_snapshots: bool = False,
    ) -> ContentOpportunityReport:
        """
        Evaluate research dossier across the 5 pillars (total 100 points).
        """
        repo = dossier.get("repository", {})
        facts = dossier.get("verified_facts", {})
        claims = dossier.get("readme_claims", {})
        obs = dossier.get("source_code_observations", {})
        raw_readme = (dossier.get("raw_readme") or "").lower()

        stars = repo.get("stars", 0)
        forks = repo.get("forks", 0)
        open_issues = repo.get("open_issues", 0)
        pushed_date = self._parse_pushed_date(repo.get("pushed_at"))

        now = datetime.now(timezone.utc)

        # ---------------- 1. Trend Momentum (25 pts) ----------------
        m_score = 0
        m_reasons = []
        m_missing = []

        if pushed_date:
            days_since_push = (now - pushed_date).days
            if days_since_push <= 7:
                m_score += 10
                m_reasons.append(f"Highly active development: committed {days_since_push} day(s) ago (+10 pts).")
            elif days_since_push <= 30:
                m_score += 6
                m_reasons.append(f"Recent development activity within the past month ({days_since_push} days ago, +6 pts).")
            elif days_since_push <= 90:
                m_score += 3
                m_reasons.append("Moderate maintenance activity within 90 days (+3 pts).")
            else:
                m_missing.append(f"Stale development: last commit was {days_since_push} days ago.")
        else:
            m_missing.append("Unable to verify push activity date.")

        if stars >= 500:
            m_score += 10
            m_reasons.append(f"Strong community traction: {stars:,} stars (+10 pts).")
        elif stars >= 100:
            m_score += 7
            m_reasons.append(f"Emerging traction: {stars:,} stars (+7 pts).")
        elif stars >= 25:
            m_score += 4
            m_reasons.append(f"Early stage interest: {stars:,} stars (+4 pts).")
        else:
            m_missing.append("Low star count (<25 stars); traction unconfirmed.")

        if open_issues <= (forks * 2) and (stars > 50):
            m_score += 5
            m_reasons.append("Healthy issue-to-community balance (+5 pts).")
        else:
            m_missing.append("Higher issue ratio or insufficient forks for issue health validation.")

        if not has_historical_snapshots:
            m_missing.append("Historical trajectory snapshot data pending (Phase 6 automation).")

        momentum_pillar = PillarScore(
            name="Trend Momentum",
            score=min(25, m_score),
            max_score=25,
            reasons=m_reasons,
            missing=m_missing,
        )

        # ---------------- 2. Uniqueness (20 pts) ----------------
        u_score = 0
        u_reasons = []
        u_missing = []

        tech_data = obs.get("detected_technologies", {})
        frameworks = tech_data.get("frameworks", [])
        deps = obs.get("dependencies_parsed", [])
        all_tech = [f.lower() for f in frameworks] + [d.lower() for d in deps]

        hot_niches = ["agent", "mcp", "llm", "rag", "backtesting", "quant", "osint", "security", "vector", "diffusion"]
        matched_niches = [n for n in hot_niches if any(n in t for t in all_tech)]

        if len(matched_niches) >= 2:
            u_score += 10
            u_reasons.append(f"High-interest niche overlap ({', '.join(matched_niches)}) (+10 pts).")
        elif len(matched_niches) == 1:
            u_score += 6
            u_reasons.append(f"Trending niche focus: {matched_niches[0]} (+6 pts).")
        else:
            u_missing.append("Does not match top high-interest tech niches.")

        problem_text = claims.get("problem_solved", "")
        if len(problem_text) > 100 and "not specified" not in problem_text.lower():
            u_score += 10
            u_reasons.append("Clear and distinct problem articulation in documentation (+10 pts).")
        else:
            u_score += 4
            u_missing.append("Problem statement is brief or missing dedicated motivation section.")

        uniqueness_pillar = PillarScore(
            name="Uniqueness",
            score=min(20, u_score),
            max_score=20,
            reasons=u_reasons,
            missing=u_missing,
        )

        # ---------------- 3. Practical Usefulness (20 pts) ----------------
        p_score = 0
        p_reasons = []
        p_missing = []

        install_text = claims.get("installation_process", "").lower()
        if any(cmd in install_text for cmd in ["pip install", "npm install", "cargo install", "git clone", "docker run"]):
            p_score += 8
            p_reasons.append("Explicit copy-pasteable installation instructions (+8 pts).")
        elif len(install_text) > 40:
            p_score += 4
            p_reasons.append("Installation section present (+4 pts).")
        else:
            p_missing.append("Missing concise installation instructions in README.")

        usage_text = claims.get("usage_instructions", "").lower()
        if len(usage_text) > 50 and "not specified" not in usage_text:
            p_score += 6
            p_reasons.append("Practical usage examples provided (+6 pts).")
        else:
            p_missing.append("No explicit code or CLI usage walkthrough in README.")

        if facts.get("has_dockerfile"):
            p_score += 6
            p_reasons.append("Containerized environment available (Dockerfile/Docker Compose) (+6 pts).")
        elif any("cli" in d.lower() or "cli" in repo.get("full_name", "").lower() for d in deps):
            p_score += 4
            p_reasons.append("CLI / terminal interface detected (+4 pts).")
        else:
            p_missing.append("No Dockerfile or standalone CLI packaging detected.")

        practical_pillar = PillarScore(
            name="Practical Usefulness",
            score=min(20, p_score),
            max_score=20,
            reasons=p_reasons,
            missing=p_missing,
        )

        # ---------------- 4. Content Appeal (20 pts) ----------------
        c_score = 0
        c_reasons = []
        c_missing = []

        # Check for visual media in markdown: ![alt](url) or <img> or gif
        has_media = bool(re.search(r"!\[.*?\]\(.*?\.(?:png|jpg|gif|svg|webp)\)", raw_readme) or "<img" in raw_readme)
        if has_media:
            c_score += 7
            c_reasons.append("Visual assets / demo GIF / architectural diagrams included in README (+7 pts).")
        else:
            c_missing.append("No visual demo or diagram detected in README (reduces video/social demo appeal).")

        desc = repo.get("description", "")
        if desc and len(desc) >= 30:
            c_score += 7
            c_reasons.append("Strong concise tagline suitable for hooks and titles (+7 pts).")
        else:
            c_missing.append("Description is brief or missing, requiring manual title synthesis.")

        if stars >= 50 or forks >= 10:
            c_score += 6
            c_reasons.append("Sufficient community credibility for audience engagement (+6 pts).")
        else:
            c_missing.append("Very low star count may need stronger educational framing.")

        appeal_pillar = PillarScore(
            name="Content Appeal",
            score=min(20, c_score),
            max_score=20,
            reasons=c_reasons,
            missing=c_missing,
        )

        # ---------------- 5. Project Quality Signals (15 pts) ----------------
        q_score = 0
        q_reasons = []
        q_missing = []

        lic = repo.get("license", "")
        if lic and "no license" not in lic.lower() and lic != "None":
            q_score += 6
            q_reasons.append(f"Recognized open-source license: {lic} (+6 pts).")
        else:
            q_missing.append("No recognized open-source license detected.")

        if facts.get("has_test_suite"):
            q_score += 5
            q_reasons.append("Automated test suite detected in repository (+5 pts).")
        else:
            q_missing.append("No automated test directory found.")

        if not repo.get("is_archived", False):
            q_score += 4
            q_reasons.append("Repository is active and not archived (+4 pts).")
        else:
            q_missing.append("Repository is archived (read-only).")

        quality_pillar = PillarScore(
            name="Project Quality Signals",
            score=min(15, q_score),
            max_score=15,
            reasons=q_reasons,
            missing=q_missing,
        )

        total = momentum_pillar.score + uniqueness_pillar.score + practical_pillar.score + appeal_pillar.score + quality_pillar.score

        if total >= 80:
            verdict = "Exceptional Content Potential — Prime candidate for YouTube, Deep Dive, or Long-form tutorial."
        elif total >= 65:
            verdict = "Strong Technical Candidate — Highly suitable for technical breakdown, Shorts, or newsletter."
        elif total >= 50:
            verdict = "Promising Niche Repository — Good for targeted developer roundups or curated lists."
        else:
            verdict = "Early Stage / Limited Documentation — Requires manual verification before featuring."

        return ContentOpportunityReport(
            total_score=total,
            is_preliminary=not has_historical_snapshots,
            editorial_verdict=verdict,
            trend_momentum=momentum_pillar,
            uniqueness=uniqueness_pillar,
            practical_usefulness=practical_pillar,
            content_appeal=appeal_pillar,
            quality_signals=quality_pillar,
        )


scoring_engine = ScoringEngine()

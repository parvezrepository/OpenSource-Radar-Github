"""Multi-repository comparative matrix engine for side-by-side technical evaluation."""

import logging
from typing import Any, Optional
from core.github_client import GitHubClient, get_github_client
from core.repository_analyzer import repository_analyzer
from core.scoring_engine import scoring_engine

logger = logging.getLogger("opensource_radar.compare")


class ComparisonEngine:
    """Evaluates 2 to 5 repositories side-by-side across quantitative and qualitative facets."""

    def __init__(self, github_client: Optional[GitHubClient] = None) -> None:
        self.client = github_client or get_github_client()

    def compare_repositories(self, repo_identifiers: list[str]) -> dict[str, Any]:
        """
        Compare 2 to 5 repositories by full_name ('owner/repo').
        Returns structured matrix with aligned comparison points.
        """
        clean_ids = [r.strip() for r in repo_identifiers if r and r.strip()]
        if len(clean_ids) < 2:
            raise ValueError("At least 2 repositories are required for comparison.")
        if len(clean_ids) > 5:
            raise ValueError("Maximum 5 repositories can be compared simultaneously.")

        dossiers: list[dict[str, Any]] = []
        scores: list[dict[str, Any]] = []
        errors: dict[str, str] = {}

        for repo_id in clean_ids:
            if "/" not in repo_id:
                errors[repo_id] = "Invalid format. Expected 'owner/repo'."
                continue
            owner, name = repo_id.split("/", 1)
            try:
                d = repository_analyzer.analyze_repository(owner, name)
                score_report = scoring_engine.calculate_score(d)
                dossiers.append(d)
                scores.append(score_report.to_dict())
            except Exception as exc:
                logger.error(f"Failed to analyze repository '{repo_id}' for comparison: {exc}")
                errors[repo_id] = str(exc)

        if len(dossiers) < 2:
            raise ValueError(f"Could not analyze at least 2 valid repositories. Errors: {errors}")

        # Assemble comparison matrix
        matrix: dict[str, Any] = {
            "repositories": [],
            "metrics": {
                "stars": {},
                "forks": {},
                "open_issues": {},
                "content_opportunity_score": {},
                "primary_language": {},
                "license": {},
                "default_branch": {},
                "has_tests": {},
                "has_docker": {},
                "last_commit": {},
            },
            "technologies": {},
            "features_claimed": {},
            "problem_solved": {},
            "dependencies_count": {},
            "common_dependencies": [],
            "strengths": {},
            "limitations": {},
            "errors": errors,
        }

        all_dep_sets = []

        for d, s in zip(dossiers, scores):
            r = d["repository"]
            name = r["full_name"]
            facts = d["verified_facts"]
            claims = d["readme_claims"]
            obs = d["source_code_observations"]

            matrix["repositories"].append(name)
            matrix["metrics"]["stars"][name] = r.get("stars", 0)
            matrix["metrics"]["forks"][name] = r.get("forks", 0)
            matrix["metrics"]["open_issues"][name] = r.get("open_issues", 0)
            matrix["metrics"]["content_opportunity_score"][name] = s.get("total_score", 0)
            matrix["metrics"]["primary_language"][name] = facts.get("primary_language", "Unknown")
            matrix["metrics"]["license"][name] = r.get("license", "Unknown")
            matrix["metrics"]["default_branch"][name] = r.get("default_branch", "main")
            matrix["metrics"]["has_tests"][name] = "Yes" if facts.get("has_test_suite", False) else "No"
            matrix["metrics"]["has_docker"][name] = "Yes" if facts.get("has_dockerfile", False) else "No"
            matrix["metrics"]["last_commit"][name] = str(facts.get("last_commit_date", "Unknown"))[:10]

            matrix["technologies"][name] = obs.get("detected_technologies", {})
            matrix["features_claimed"][name] = claims.get("features_claimed") or "Not reported in README"
            matrix["problem_solved"][name] = claims.get("problem_solved") or "Not reported in README"
            
            deps = obs.get("dependencies_parsed", [])
            matrix["dependencies_count"][name] = len(deps)
            all_dep_sets.append(set(deps))

            # Derive strengths from score reasons
            matrix["strengths"][name] = s["all_reasons"][:4] if s["all_reasons"] else ["Active GitHub repository"]
            matrix["limitations"][name] = (
                [claims.get("limitations_reported")]
                if claims.get("limitations_reported") and "not reported" not in claims.get("limitations_reported", "").lower()
                else s["missing_signals"][:3]
            )

        # Compute common dependency overlap across compared repositories
        if all_dep_sets:
            common = set.intersection(*all_dep_sets)
            matrix["common_dependencies"] = sorted(list(common))

        return matrix


# Global comparison engine instance
comparison_engine = ComparisonEngine()

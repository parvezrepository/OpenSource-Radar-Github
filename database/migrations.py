"""Database schema initialization and category seed migrations."""

import logging
from sqlalchemy import select
from database.connection import get_db, init_db
from database.models import Category

logger = logging.getLogger("opensource_radar.migrations")

DEFAULT_CATEGORIES = [
    {
        "key": "ai",
        "display_name": "Artificial Intelligence",
        "description": "Machine Learning, Deep Learning, LLMs, Computer Vision, and RAG architectures.",
        "default_topics": ["machine-learning", "deep-learning", "llm", "generative-ai", "rag", "pytorch"],
    },
    {
        "key": "agents",
        "display_name": "AI Agents & Automation",
        "description": "Autonomous agents, multi-agent frameworks, MCP servers, and workflow orchestration.",
        "default_topics": ["ai-agents", "autonomous-agents", "mcp", "agentic-ai", "langchain", "autogen"],
    },
    {
        "key": "software",
        "display_name": "Software Development",
        "description": "APIs, backend frameworks, SDKs, databases, and core software tooling.",
        "default_topics": ["fastapi", "django", "flask", "database", "backend", "framework"],
    },
    {
        "key": "security",
        "display_name": "Cybersecurity & Privacy",
        "description": "Defensive security, OSINT, network analysis, vulnerability scanners, and privacy tools.",
        "default_topics": ["cybersecurity", "osint", "security-tools", "penetration-testing", "privacy"],
    },
    {
        "key": "fintech",
        "display_name": "Trading & FinTech",
        "description": "Algorithmic trading, crypto bots, quantitative finance, backtesting, and market indicators.",
        "default_topics": ["algorithmic-trading", "quantitative-finance", "crypto-trading", "backtesting", "fintech"],
    },
    {
        "key": "devtools",
        "display_name": "Developer Tools & CLI",
        "description": "Command line utilities, linters, developer productivity tools, and testing frameworks.",
        "default_topics": ["developer-tools", "cli", "terminal", "devtools", "productivity"],
    },
    {
        "key": "cloud",
        "display_name": "Cloud & DevOps",
        "description": "Docker, Kubernetes, CI/CD pipelines, infrastructure-as-code, and self-hosted services.",
        "default_topics": ["docker", "kubernetes", "devops", "self-hosted", "infrastructure"],
    },
    {
        "key": "other",
        "display_name": "Emerging Technologies",
        "description": "IoT, robotics, blockchain, educational software, and miscellaneous high-potential repos.",
        "default_topics": ["robotics", "iot", "education", "open-source"],
    },
]


def run_migrations() -> None:
    """Initialize tables and seed default categories if not already present."""
    init_db()

    with get_db() as session:
        for cat_data in DEFAULT_CATEGORIES:
            existing = session.execute(
                select(Category).where(Category.key == cat_data["key"])
            ).scalars().first()

            if not existing:
                category = Category(
                    key=cat_data["key"],
                    display_name=cat_data["display_name"],
                    description=cat_data["description"],
                    default_topics=cat_data["default_topics"],
                )
                session.add(category)
                logger.info(f"Seeded category: {cat_data['display_name']} ({cat_data['key']})")

    logger.info("Database migration and seeding completed.")

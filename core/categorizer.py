"""Technology categorization taxonomy and domain classifier for OpenSource Radar."""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SubCategory:
    """Sub-domain within a parent technology category."""
    name: str
    topics: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


@dataclass
class TechCategory:
    """Top-level technology classification."""
    key: str
    display_name: str
    description: str
    subcategories: list[SubCategory] = field(default_factory=list)

    @property
    def all_topics(self) -> list[str]:
        """Aggregate all topics across subcategories."""
        seen = set()
        topics = []
        for sub in self.subcategories:
            for t in sub.topics:
                if t not in seen:
                    seen.add(t)
                    topics.append(t)
        return topics

    @property
    def all_keywords(self) -> list[str]:
        """Aggregate all keywords across subcategories."""
        seen = set()
        keywords = []
        for sub in self.subcategories:
            for kw in sub.keywords:
                if kw not in seen:
                    seen.add(kw)
                    keywords.append(kw)
        return keywords


# Comprehensive taxonomy matching Phase 2 specifications
TAXONOMY: dict[str, TechCategory] = {
    "ai": TechCategory(
        key="ai",
        display_name="Artificial Intelligence",
        description="Core machine learning, deep learning, LLMs, computer vision, and AI research.",
        subcategories=[
            SubCategory("Machine Learning", ["machine-learning", "scikit-learn", "ml"], ["machine learning", "supervised learning"]),
            SubCategory("Deep Learning", ["deep-learning", "pytorch", "tensorflow", "jax", "keras"], ["neural network", "deep learning"]),
            SubCategory("Generative AI", ["generative-ai", "diffusion-models", "stable-diffusion"], ["generative ai", "diffusion"]),
            SubCategory("LLMs", ["llm", "large-language-models", "llama", "transformers", "fine-tuning"], ["llm", "large language model", "foundation model"]),
            SubCategory("Computer Vision", ["computer-vision", "opencv", "yolo", "image-processing"], ["computer vision", "object detection", "image segmentation"]),
            SubCategory("NLP", ["nlp", "natural-language-processing", "spacy", "text-classification"], ["nlp", "text processing"]),
            SubCategory("Speech AI", ["speech-recognition", "whisper", "tts", "voice-ai", "audio-processing"], ["speech to text", "voice synthesis"]),
            SubCategory("RAG", ["rag", "retrieval-augmented-generation", "haystack"], ["rag", "retrieval augmented"]),
            SubCategory("Vector Databases", ["vector-database", "vector-search", "milvus", "qdrant", "chroma", "pinecone"], ["vector database", "embedding index"]),
            SubCategory("AI Inference", ["inference", "vllm", "ollama", "onnx", "tensorrt", "ggml", "llama-cpp"], ["ai inference", "quantization", "model serving"]),
            SubCategory("Local AI", ["local-ai", "on-device-ai", "private-ai"], ["local ai", "offline llm", "self hosted ai"]),
            SubCategory("AI Research", ["ai-research", "paper-code", "neurips", "icml", "cvpr"], ["research paper", "reproduction"]),
        ],
    ),
    "agents": TechCategory(
        key="agents",
        display_name="AI Agents & Automation",
        description="Autonomous agents, multi-agent frameworks, MCP servers, and agent memory.",
        subcategories=[
            SubCategory("Autonomous Agents", ["autonomous-agents", "ai-agents", "agentic-ai", "babyagi"], ["autonomous agent", "agent loop"]),
            SubCategory("Multi-Agent Systems", ["multi-agent", "swarm", "crewai", "autogen", "chatdev"], ["multi agent", "agent collaboration"]),
            SubCategory("MCP Servers", ["mcp", "model-context-protocol", "mcp-server"], ["model context protocol", "mcp server"]),
            SubCategory("Agent Frameworks", ["langchain", "llamaindex", "semantic-kernel", "langgraph"], ["agent framework", "orchestration engine"]),
            SubCategory("AI Coding Agents", ["coding-agent", "ai-programmer", "swe-bench", "aider"], ["coding agent", "code assistant", "automated dev"]),
            SubCategory("Browser Agents", ["browser-agent", "web-agent", "browser-automation", "playwright-ai"], ["browser agent", "web automation"]),
            SubCategory("Research Agents", ["research-agent", "automated-research", "scholar-ai"], ["research agent", "literature review"]),
            SubCategory("Agent Memory", ["agent-memory", "long-term-memory", "memgpt", "zep"], ["agent memory", "episodic memory"]),
            SubCategory("Workflow Automation", ["workflow-automation", "n8n", "automation-pipeline"], ["workflow automation", "pipeline orchestrator"]),
            SubCategory("Agent Orchestration", ["agent-orchestration", "multi-agent-system", "task-planner"], ["agent orchestration", "task planning"]),
        ],
    ),
    "software": TechCategory(
        key="software",
        display_name="Software Development",
        description="APIs, SDKs, backend/frontend frameworks, databases, and core devtools.",
        subcategories=[
            SubCategory("APIs", ["api", "rest-api", "graphql", "grpc", "openapi"], ["rest api", "web api", "graphql"]),
            SubCategory("SDKs", ["sdk", "client-library", "api-wrapper"], ["software development kit", "sdk wrapper"]),
            SubCategory("Python Projects", ["python", "python3", "asyncio"], ["python library", "python framework"]),
            SubCategory("JavaScript Ecosystem", ["javascript", "typescript", "nodejs", "deno", "bun"], ["javascript ecosystem"]),
            SubCategory("Backend Frameworks", ["fastapi", "django", "flask", "express", "actix-web"], ["backend framework", "web framework"]),
            SubCategory("Frontend Frameworks", ["frontend-framework", "ui-library"], ["ui framework", "web components"]),
            SubCategory("Databases", ["database", "sql", "nosql", "postgres", "sqlite", "redis"], ["database engine", "data store"]),
            SubCategory("Developer Tools", ["developer-tools", "devtools", "productivity-tool"], ["developer tools", "dev utility"]),
            SubCategory("CLI Tools", ["cli", "command-line", "terminal-app", "tui"], ["command line", "cli tool"]),
            SubCategory("SaaS Applications", ["saas", "self-hosted", "web-application"], ["saas platform", "open source saas"]),
            SubCategory("Testing Frameworks", ["testing", "pytest", "unit-test", "mocking"], ["test suite", "testing framework"]),
        ],
    ),
    "security": TechCategory(
        key="security",
        display_name="Cybersecurity & OSINT",
        description="Defensive security, OSINT, network analysis, vulnerability scanners, and privacy.",
        subcategories=[
            SubCategory("Defensive Security", ["defensive-security", "blue-team", "siem", "edr"], ["defensive security", "hardening", "incident response"]),
            SubCategory("OSINT", ["osint", "open-source-intelligence", "reconnaissance", "shodan"], ["osint", "information gathering", "recon"]),
            SubCategory("Network Analysis", ["network-analysis", "packet-sniffer", "wireshark", "nmap"], ["network scanner", "traffic analysis"]),
            SubCategory("Privacy Tools", ["privacy", "anonymity", "tor", "vpn", "anti-tracking"], ["privacy tool", "data protection"]),
            SubCategory("Vulnerability Research", ["vulnerability-scanner", "cve", "exploit-research"], ["vulnerability assessment", "cve research"]),
            SubCategory("Security Monitoring", ["security-monitoring", "ids", "ips", "intrusion-detection"], ["security monitor", "log analysis"]),
            SubCategory("Security Automation", ["security-automation", "soar", "devsecops"], ["security automation", "automated audit"]),
        ],
    ),
    "fintech": TechCategory(
        key="fintech",
        display_name="Trading & FinTech",
        description="Algorithmic trading, crypto bots, quantitative finance, backtesting, and market indicators.",
        subcategories=[
            SubCategory("Forex Bots", ["forex", "forex-trading", "currency-trading"], ["forex bot", "foreign exchange trading"]),
            SubCategory("Crypto Bots", ["crypto-bot", "cryptocurrency-trading", "binance-bot", "ccxt"], ["crypto trading bot", "arbitrage bot"]),
            SubCategory("Algorithmic Trading", ["algorithmic-trading", "algo-trading", "automated-trading"], ["algorithmic trading", "automated execution"]),
            SubCategory("Quantitative Trading", ["quantitative-trading", "quant", "hft"], ["quantitative finance", "quant strategy"]),
            SubCategory("MT4 / MT5 EAs", ["metatrader", "mt4", "mt5", "expert-advisor", "mql5"], ["expert advisor", "metatrader script"]),
            SubCategory("Trading Indicators", ["trading-indicators", "technical-analysis", "ta-lib"], ["technical indicators", "market signals"]),
            SubCategory("Backtesting", ["backtesting", "backtrader", "zipline", "vectorbt"], ["backtesting engine", "historical simulation"]),
            SubCategory("Portfolio Analysis", ["portfolio-management", "asset-allocation", "pyfolio"], ["portfolio optimization", "risk parity"]),
            SubCategory("Risk Management", ["risk-management", "var", "drawdown-analysis"], ["financial risk", "drawdown calculator"]),
            SubCategory("Financial Data Analysis", ["financial-data", "market-data", "stock-screener", "yfinance"], ["financial data", "stock market analysis"]),
        ],
    ),
    "other": TechCategory(
        key="other",
        display_name="Emerging & Other Technologies",
        description="Cloud, DevOps, Docker, Kubernetes, Self-Hosted, Web3, Robotics, IoT, and Games.",
        subcategories=[
            SubCategory("Cloud", ["cloud-computing", "aws", "gcp", "azure"], ["cloud platform"]),
            SubCategory("DevOps", ["devops", "ci-cd", "github-actions"], ["devops pipeline", "continuous integration"]),
            SubCategory("Docker", ["docker", "docker-compose", "containerization"], ["docker container"]),
            SubCategory("Kubernetes", ["kubernetes", "k8s", "helm"], ["kubernetes cluster"]),
            SubCategory("Self-Hosted Software", ["self-hosted", "homelab", "awesome-selfhosted"], ["self hosted", "homelab"]),
            SubCategory("Blockchain & Web3", ["blockchain", "web3", "smart-contracts", "ethereum", "solana"], ["smart contract", "web3"]),
            SubCategory("Robotics", ["robotics", "ros", "ros2", "autonomous-robots"], ["robotics framework", "robot os"]),
            SubCategory("IoT", ["iot", "internet-of-things", "embedded", "esp32", "arduino"], ["iot device", "embedded system"]),
            SubCategory("Data Science & Big Data", ["data-science", "big-data", "spark", "kafka"], ["data science", "data pipeline"]),
            SubCategory("Education", ["education", "tutorial", "learning-resources", "curriculum"], ["educational project", "course code"]),
            SubCategory("Productivity", ["productivity", "note-taking", "task-management"], ["productivity app"]),
            SubCategory("Open Source Games", ["game-engine", "godot", "pygame", "open-source-game"], ["game engine", "open source game"]),
        ],
    ),
}


class TechnologyCategorizer:
    """Classifies repositories into taxonomy categories based on topics and metadata."""

    def __init__(self, custom_categories: Optional[dict[str, TechCategory]] = None) -> None:
        self.taxonomy = dict(TAXONOMY)
        if custom_categories:
            self.taxonomy.update(custom_categories)

    def get_category(self, key: str) -> Optional[TechCategory]:
        """Retrieve category by key."""
        return self.taxonomy.get(key)

    def list_categories(self) -> list[TechCategory]:
        """Return list of all registered categories."""
        return list(self.taxonomy.values())

    def classify_repository(
        self,
        topics: list[str],
        description: Optional[str] = None,
        name: Optional[str] = None,
    ) -> tuple[str, str, float]:
        """
        Classify repository into (category_key, subcategory_name, confidence).
        Returns ("other", "General", 0.0) if no strong match found.
        """
        topics_lower = [t.lower().strip() for t in (topics or [])]
        text_blob = f"{(name or '')} {(description or '')}".lower()

        best_cat_key = "other"
        best_sub_name = "General"
        best_score = 0.0

        for cat_key, cat in self.taxonomy.items():
            for sub in cat.subcategories:
                score = 0.0
                
                # Check topic matches (high weight: 3 points each)
                matched_topics = set(topics_lower).intersection([t.lower() for t in sub.topics])
                score += len(matched_topics) * 3.0

                # Check keyword matches in description/name (weight: 1.5 points each)
                for kw in sub.keywords:
                    if kw.lower() in text_blob:
                        score += 1.5

                if score > best_score:
                    best_score = score
                    best_cat_key = cat_key
                    best_sub_name = sub.name

        confidence = min(1.0, best_score / 6.0) if best_score > 0 else 0.0
        return best_cat_key, best_sub_name, confidence

    def add_custom_category(self, category: TechCategory) -> None:
        """Register a custom technology category."""
        self.taxonomy[category.key] = category


# Global categorizer singleton
categorizer = TechnologyCategorizer()

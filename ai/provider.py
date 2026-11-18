"""Abstract base class and provider factory for AI intelligence engines."""

from abc import ABC, abstractmethod
import logging
from typing import Any, Optional

from ai.analysis import ContentDraftSchema, StructuredAnalysis
from config import get_settings

logger = logging.getLogger("opensource_radar.ai")


class AIError(Exception):
    """Base exception for AI provider operations."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class AIAuthError(AIError):
    """Raised when AI API credentials fail authentication."""
    pass


class AIRateLimitError(AIError):
    """Raised when AI provider rate or quota limit is exceeded."""
    pass


class AITimeoutError(AIError):
    """Raised when an AI request exceeds timeout limits."""
    pass


class AIValidationError(AIError):
    """Raised when model response fails schema validation."""
    pass


class AIProvider(ABC):
    """Abstract interface defining required AI analysis and generation contracts."""

    @abstractmethod
    def test_connection(self) -> dict[str, Any]:
        """Verify API credentials and connectivity."""
        pass

    @abstractmethod
    def analyze_repository(
        self,
        repo_data: dict[str, Any],
        readme_content: Optional[str],
        tree_summary: list[str],
        detected_technologies: dict[str, list[str]],
        dependencies: list[str],
    ) -> StructuredAnalysis:
        """Conduct evidence-grounded AI analysis of a repository."""
        pass

    @abstractmethod
    def generate_content(
        self,
        repo_data: dict[str, Any],
        dossier: dict[str, Any],
        platform: str,
        content_type: str,
        language: str,
        tone: str,
        audience_level: str,
        additional_instructions: Optional[str] = None,
    ) -> ContentDraftSchema:
        """Synthesize educational multi-platform content."""
        pass

    @abstractmethod
    def chat_with_repository(
        self,
        dossier: dict[str, Any],
        query: str,
        chat_history: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """Answer interactive user questions grounded strictly in the repository dossier."""
        pass


def get_ai_provider(provider_override: Optional[str] = None) -> Optional[AIProvider]:
    """
    Factory creating the configured AI provider singleton.
    Returns None if provider is 'none' or required credentials are not configured.
    """
    settings = get_settings()
    provider_name = (provider_override or settings.AI_PROVIDER).lower().strip()

    if provider_name == "none":
        return None

    if provider_name == "openai":
        if not settings.has_openai_credentials:
            logger.info("OpenAI provider selected but OPENAI_API_KEY is not configured.")
            return None
        from ai.openai_provider import OpenAIProvider
        return OpenAIProvider()

    elif provider_name == "gemini":
        if not settings.has_gemini_credentials:
            logger.info("Gemini provider selected but GEMINI_API_KEY is not configured.")
            return None
        from ai.gemini_provider import GeminiProvider
        return GeminiProvider()

    logger.warning(f"Unknown AI provider '{provider_name}'. Defaulting to None.")
    return None

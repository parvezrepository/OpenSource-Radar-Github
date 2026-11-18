"""OpenAI GPT integration provider for OpenSource Radar."""

import json
import logging
from typing import Any, Optional
import openai
from openai import OpenAI

from ai.analysis import ContentDraftSchema, StructuredAnalysis
from ai.prompts import SYSTEM_ANALYSIS_PROMPT, build_analysis_user_prompt, build_content_prompt
from ai.provider import (
    AIAuthError,
    AIError,
    AIProvider,
    AIRateLimitError,
    AITimeoutError,
    AIValidationError,
)
from config import get_settings

logger = logging.getLogger("opensource_radar.ai.openai")


class OpenAIProvider(AIProvider):
    """OpenAI implementation of AIProvider utilizing JSON mode and strict validation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise AIAuthError("OPENAI_API_KEY is not configured.")

        self.model = model or settings.OPENAI_MODEL
        base_url = None
        if self.api_key.startswith("sk-or-"):
            base_url = "https://openrouter.ai/api/v1"
            if "/" not in self.model:
                self.model = f"openai/{self.model}"
            logger.info("Configured OpenAI provider via OpenRouter gateway (model: %s).", self.model)

        self.client = OpenAI(api_key=self.api_key, base_url=base_url, timeout=45.0)

    def test_connection(self) -> dict[str, Any]:
        """Verify OpenAI credentials by listing models or running a minimal query."""
        try:
            self.client.models.list()
            return {
                "provider": "openai",
                "status": "connected",
                "model": self.model,
                "authenticated": True,
            }
        except openai.AuthenticationError as exc:
            return {
                "provider": "openai",
                "status": "auth_failed",
                "authenticated": False,
                "error": "Invalid OpenAI API Key.",
            }
        except openai.RateLimitError as exc:
            return {
                "provider": "openai",
                "status": "rate_limited",
                "authenticated": True,
                "error": "OpenAI quota or rate limit exceeded.",
            }
        except Exception as exc:
            return {
                "provider": "openai",
                "status": "error",
                "authenticated": False,
                "error": str(exc),
            }

    def analyze_repository(
        self,
        repo_data: dict[str, Any],
        readme_content: Optional[str],
        tree_summary: list[str],
        detected_technologies: dict[str, list[str]],
        dependencies: list[str],
    ) -> StructuredAnalysis:
        """Call OpenAI model with prompt isolation and parse into StructuredAnalysis."""
        user_prompt = build_analysis_user_prompt(
            repo_data=repo_data,
            readme_content=readme_content,
            tree_summary=tree_summary,
            detected_technologies=detected_technologies,
            dependencies=dependencies,
        )

        messages = [
            {"role": "system", "content": SYSTEM_ANALYSIS_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content_str = response.choices[0].message.content or "{}"
            raw_json = json.loads(content_str)
            return StructuredAnalysis.model_validate(raw_json)

        except openai.AuthenticationError as exc:
            logger.error("OpenAI authentication failure.")
            raise AIAuthError("Invalid OpenAI API credentials.") from exc
        except openai.RateLimitError as exc:
            logger.error("OpenAI rate limit or quota exceeded.")
            raise AIRateLimitError("OpenAI API rate limit or quota exceeded.") from exc
        except openai.APITimeoutError as exc:
            logger.error("OpenAI request timed out.")
            raise AITimeoutError("OpenAI request timed out.") from exc
        except openai.APIConnectionError as exc:
            logger.error("OpenAI network connection failure.")
            raise AIError("Network connection failure with OpenAI API.") from exc
        except json.JSONDecodeError as exc:
            logger.error(f"OpenAI returned malformed JSON: {exc}")
            raise AIValidationError("OpenAI model returned invalid JSON syntax.") from exc
        except Exception as exc:
            logger.error(f"OpenAI analysis failure: {exc}")
            raise AIValidationError(f"Response validation failed: {str(exc)}") from exc

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
        """Synthesize educational multi-platform content using OpenAI."""
        user_prompt = build_content_prompt(
            repo_data=repo_data,
            dossier=dossier,
            platform=platform,
            content_type=content_type,
            language=language,
            tone=tone,
            audience_level=audience_level,
            additional_instructions=additional_instructions,
        )

        messages = [
            {"role": "system", "content": SYSTEM_ANALYSIS_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            content_str = response.choices[0].message.content or "{}"
            raw_json = json.loads(content_str)
            return ContentDraftSchema.model_validate(raw_json)

        except openai.AuthenticationError as exc:
            raise AIAuthError("Invalid OpenAI credentials.") from exc
        except openai.RateLimitError as exc:
            raise AIRateLimitError("OpenAI rate limit or quota exceeded.") from exc
        except openai.APITimeoutError as exc:
            raise AITimeoutError("OpenAI request timed out.") from exc
        except json.JSONDecodeError as exc:
            raise AIValidationError(f"OpenAI returned malformed JSON: {exc}") from exc
        except Exception as exc:
            raise AIValidationError(f"Content generation validation failed: {exc}") from exc

    def chat_with_repository(
        self,
        dossier: dict[str, Any],
        query: str,
        chat_history: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """Answer interactive user questions grounded strictly in the repository dossier."""
        from ai.prompts import SYSTEM_CHAT_PROMPT, build_chat_prompt

        user_prompt = build_chat_prompt(
            dossier=dossier,
            query=query,
            chat_history=chat_history,
        )

        messages = [
            {"role": "system", "content": SYSTEM_CHAT_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=1000,
            )
            return response.choices[0].message.content or "No response generated by model."
        except openai.AuthenticationError as exc:
            raise AIAuthError("Invalid OpenAI credentials.") from exc
        except openai.RateLimitError as exc:
            raise AIRateLimitError("OpenAI rate limit or quota exceeded.") from exc
        except openai.APITimeoutError as exc:
            raise AITimeoutError("OpenAI request timed out.") from exc
        except Exception as exc:
            raise AIError(f"AI repository chat failed: {exc}") from exc

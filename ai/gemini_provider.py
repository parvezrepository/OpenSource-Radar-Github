"""Google Gemini integration provider for OpenSource Radar."""

import json
import logging
import re
from typing import Any, Optional
import google.generativeai as genai

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

logger = logging.getLogger("opensource_radar.ai.gemini")


class GeminiProvider(AIProvider):
    """Google Gemini implementation of AIProvider."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise AIAuthError("GEMINI_API_KEY is not configured.")

        self.model_name = model or settings.GEMINI_MODEL
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=SYSTEM_ANALYSIS_PROMPT,
            generation_config={"response_mime_type": "application/json", "temperature": 0.2},
        )

    def test_connection(self) -> dict[str, Any]:
        """Verify Gemini API credentials with a lightweight ping."""
        try:
            resp = self.client.generate_content("Ping. Respond with {'status': 'ok'}.")
            return {
                "provider": "gemini",
                "status": "connected",
                "model": self.model_name,
                "authenticated": True,
            }
        except Exception as exc:
            err_msg = str(exc)
            if "API_KEY_INVALID" in err_msg or "401" in err_msg or "403" in err_msg:
                return {
                    "provider": "gemini",
                    "status": "auth_failed",
                    "authenticated": False,
                    "error": "Invalid Gemini API Key.",
                }
            return {
                "provider": "gemini",
                "status": "error",
                "authenticated": False,
                "error": err_msg,
            }

    def analyze_repository(
        self,
        repo_data: dict[str, Any],
        readme_content: Optional[str],
        tree_summary: list[str],
        detected_technologies: dict[str, list[str]],
        dependencies: list[str],
    ) -> StructuredAnalysis:
        """Call Gemini model and validate structured JSON response."""
        user_prompt = build_analysis_user_prompt(
            repo_data=repo_data,
            readme_content=readme_content,
            tree_summary=tree_summary,
            detected_technologies=detected_technologies,
            dependencies=dependencies,
        )

        try:
            response = self.client.generate_content(user_prompt)
            content_text = response.text or "{}"
            
            # Clean markdown codeblocks if model wrapped output in ```json ... ```
            clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", content_text.strip(), flags=re.MULTILINE)
            raw_json = json.loads(clean_json)
            return StructuredAnalysis.model_validate(raw_json)

        except json.JSONDecodeError as exc:
            logger.error(f"Gemini returned invalid JSON: {exc}")
            raise AIValidationError("Gemini model returned malformed JSON syntax.") from exc
        except Exception as exc:
            err_str = str(exc)
            if "quota" in err_str.lower() or "429" in err_str:
                raise AIRateLimitError("Gemini quota or rate limit exceeded.") from exc
            logger.error(f"Gemini analysis failure: {exc}")
            raise AIError(f"Gemini request failed: {err_str}") from exc

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
        """Synthesize educational multi-platform content using Google Gemini."""
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

        try:
            response = self.client.generate_content(user_prompt)
            content_text = response.text or "{}"
            clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", content_text.strip(), flags=re.MULTILINE)
            raw_json = json.loads(clean_json)
            return ContentDraftSchema.model_validate(raw_json)
        except json.JSONDecodeError as exc:
            raise AIValidationError(f"Gemini returned invalid JSON: {exc}") from exc
        except Exception as exc:
            err_str = str(exc)
            if "quota" in err_str.lower() or "429" in err_str:
                raise AIRateLimitError("Gemini quota or rate limit exceeded.") from exc
            raise AIError(f"Gemini content generation failed: {err_str}") from exc

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

        full_prompt = f"{SYSTEM_CHAT_PROMPT}\n\n{user_prompt}"
        try:
            response = self.client.generate_content(full_prompt)
            return response.text or "No response generated by model."
        except Exception as exc:
            err_str = str(exc)
            if "quota" in err_str.lower() or "429" in err_str:
                raise AIRateLimitError("Gemini quota or rate limit exceeded.") from exc
            raise AIError(f"Gemini repository chat failed: {err_str}") from exc

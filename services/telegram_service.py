"""Telegram notification service for real-time repository alerts and scheduled dispatch."""

import logging
from typing import Any, Optional
import requests

from config import get_settings

logger = logging.getLogger("opensource_radar.telegram")

_UNSET = object()


class TelegramService:
    """Dispatches real-time alerts and telemetry summaries to Telegram."""

    def __init__(
        self,
        bot_token: Any = _UNSET,
        chat_id: Any = _UNSET,
        timeout: int = 10,
    ) -> None:
        settings = get_settings()
        self.bot_token = settings.TELEGRAM_BOT_TOKEN if bot_token is _UNSET else bot_token
        self.chat_id = settings.TELEGRAM_CHAT_ID if chat_id is _UNSET else chat_id
        self.timeout = timeout
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    @property
    def is_configured(self) -> bool:
        """Check if Telegram token and chat ID are both provided."""
        return bool(self.bot_token and self.chat_id and self.bot_token.strip() and self.chat_id.strip())

    def send_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = False,
    ) -> bool:
        """
        Send a text message to the configured Telegram chat.
        Returns True on HTTP 200 success, False otherwise without raising exceptions.
        """
        if not self.is_configured:
            logger.debug("Telegram notification skipped: bot token or chat_id not configured.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                logger.info("Telegram notification successfully delivered.")
                return True
            else:
                logger.warning(
                    "Telegram notification failed (HTTP %s): %s",
                    response.status_code,
                    response.text,
                )
                return False
        except Exception as exc:
            logger.error("Exception occurred while sending Telegram notification: %s", exc)
            return False

    def send_repository_alert(
        self,
        repo_data: dict[str, Any],
        score_report: Optional[dict[str, Any]] = None,
        reason: str = "High Velocity Mover",
    ) -> bool:
        """
        Format and dispatch a structured repository alert card.
        """
        if not self.is_configured:
            return False

        full_name = repo_data.get("full_name") or f"{repo_data.get('owner', '')}/{repo_data.get('name', '')}"
        html_url = repo_data.get("html_url") or f"https://github.com/{full_name}"
        stars = repo_data.get("stars") or repo_data.get("stargazers_count", 0)
        forks = repo_data.get("forks") or repo_data.get("forks_count", 0)
        language = repo_data.get("primary_language") or repo_data.get("language") or "General"
        description = repo_data.get("description") or "No description provided."
        
        # Clean description for HTML
        safe_desc = description.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")[:240]
        if len(description) > 240:
            safe_desc += "..."

        score_text = "N/A"
        grade_text = ""
        if score_report:
            score = score_report.get("total_score", 0)
            score_text = f"{score}/100"
            if score >= 80:
                grade_text = " 🔥 (Elite Opportunity)"
            elif score >= 60:
                grade_text = " ⭐ (Strong Potential)"

        topics = repo_data.get("topics") or []
        topics_str = " ".join([f"#{t.replace('-', '_')}" for t in topics[:5]]) if topics else "#OpenSource"

        message = (
            f"📡 <b>OpenSource Radar Alert: {reason}</b>\n\n"
            f"📦 <b><a href=\"{html_url}\">{full_name}</a></b>\n"
            f"⭐ <b>Stars</b>: {stars:,} | 🍴 <b>Forks</b>: {forks:,} | 💻 <b>{language}</b>\n"
            f"🎯 <b>Opportunity Score</b>: <b>{score_text}</b>{grade_text}\n\n"
            f"📝 <i>{safe_desc}</i>\n\n"
            f"🏷️ {topics_str}\n"
            f"🔗 <a href=\"{html_url}\">Inspect on GitHub</a>"
        )

        return self.send_message(message, parse_mode="HTML")

    def test_connection(self) -> dict[str, Any]:
        """Verify Telegram bot credentials and send a test ping to the configured chat."""
        if not self.bot_token or not self.bot_token.strip():
            return {"status": "error", "error": "TELEGRAM_BOT_TOKEN is not configured in .env."}
        if not self.chat_id or not self.chat_id.strip():
            return {"status": "error", "error": "TELEGRAM_CHAT_ID is not configured in .env."}

        # 1. Check getMe
        me_url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
        try:
            resp = requests.get(me_url, timeout=self.timeout)
            if resp.status_code != 200:
                return {
                    "status": "auth_failed",
                    "error": f"Bot authentication failed (HTTP {resp.status_code}): {resp.text}",
                }
            bot_info = resp.json().get("result", {})
            bot_username = bot_info.get("username", "UnknownBot")
            bot_name = bot_info.get("first_name", "Bot")
        except Exception as exc:
            return {"status": "error", "error": f"Connection error: {str(exc)}"}

        # 2. Send test ping
        test_msg = (
            f"✅ <b>OpenSource Radar Connected!</b>\n\n"
            f"🤖 Bot: <b>@{bot_username}</b> ({bot_name})\n"
            f"💬 Chat ID: <code>{self.chat_id}</code>\n"
            f"⏱️ Telemetry notifications and high-velocity repository alerts are active."
        )
        ping_success = self.send_message(test_msg, parse_mode="HTML")

        if ping_success:
            return {
                "status": "connected",
                "bot_username": bot_username,
                "bot_name": bot_name,
                "chat_id": self.chat_id,
            }
        else:
            return {
                "status": "chat_failed",
                "bot_username": bot_username,
                "error": f"Bot @{bot_username} authenticated, but failed to deliver message to Chat ID '{self.chat_id}'. Make sure you clicked 'Start' in the bot or added it to the channel.",
            }


# Module singleton instance
telegram_service = TelegramService()

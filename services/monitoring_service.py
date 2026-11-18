"""Extensible notification service supporting alerts and monitoring events."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import logging
from typing import Any, Optional
import requests

from config import get_settings

logger = logging.getLogger("opensource_radar.monitoring")


class NotificationEvent:
    """Standardized event classifications for monitoring alerts."""

    NEW_DISCOVERY = "new_discovery"
    HIGH_POTENTIAL = "high_potential"
    NEW_RELEASE = "new_release"
    MONITORING_FAILURE = "monitoring_failure"
    SCHEDULER_FAILURE = "scheduler_failure"


class BaseNotificationProvider(ABC):
    """Abstract interface for dispatching notification alerts."""

    @abstractmethod
    def send(
        self,
        event_type: str,
        title: str,
        message: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Deliver a notification payload. Returns True if successfully sent."""
        pass


class LogNotificationProvider(BaseNotificationProvider):
    """Standard default provider that logs events to dedicated application log."""

    def send(
        self,
        event_type: str,
        title: str,
        message: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        log_line = f"[{event_type.upper()}] {title} — {message}"
        if metadata:
            log_line += f" | Details: {metadata}"

        if "failure" in event_type.lower():
            logger.error(log_line)
        else:
            logger.info(log_line)
        return True


class TelegramNotificationProvider(BaseNotificationProvider):
    """Optional Telegram Bot alert channel using HTTP POST."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        settings = get_settings()
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_CHAT_ID

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send(
        self,
        event_type: str,
        title: str,
        message: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        if not self.is_configured:
            logger.debug("Telegram notifications skipped: credentials not configured.")
            return False

        icon = {
            NotificationEvent.NEW_DISCOVERY: "🌟",
            NotificationEvent.HIGH_POTENTIAL: "🔥",
            NotificationEvent.NEW_RELEASE: "🚀",
            NotificationEvent.MONITORING_FAILURE: "⚠️",
            NotificationEvent.SCHEDULER_FAILURE: "🚨",
        }.get(event_type, "📢")

        text = (
            f"{icon} <b>OpenSource Radar Alert</b>\n"
            f"<b>Event</b>: {event_type}\n"
            f"<b>Title</b>: {title}\n\n"
            f"{message}\n"
        )
        if metadata and "url" in metadata:
            text += f"\n🔗 <a href='{metadata['url']}'>View Repository</a>"

        from services.telegram_service import telegram_service
        return telegram_service.send_message(text, parse_mode="HTML")


class MonitoringService:
    """Dispatches monitoring alerts across active notification channels."""

    def __init__(self):
        self.providers: list[BaseNotificationProvider] = [
            LogNotificationProvider(),
            TelegramNotificationProvider(),
        ]
        self._notification_history: list[dict[str, Any]] = []

    def notify(
        self,
        event_type: str,
        title: str,
        message: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Broadcast alert to all registered providers."""
        meta = metadata or {}
        record = {
            "event_type": event_type,
            "title": title,
            "message": message,
            "metadata": meta,
            "timestamp": datetime.now(timezone.utc),
        }
        self._notification_history.append(record)
        # Cap memory history to recent 100 entries
        if len(self._notification_history) > 100:
            self._notification_history = self._notification_history[-100:]

        dispatch_results = {}
        for p in self.providers:
            name = p.__class__.__name__
            try:
                success = p.send(event_type, title, message, meta)
                dispatch_results[name] = success
            except Exception as e:
                logger.error("Provider %s failed: %s", name, str(e))
                dispatch_results[name] = False

        return {
            "event_type": event_type,
            "title": title,
            "dispatched": dispatch_results,
            "timestamp": record["timestamp"],
        }

    def get_recent_alerts(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return in-memory log of recent notifications."""
        return list(reversed(self._notification_history[-limit:]))


# Global singleton
monitoring_service = MonitoringService()

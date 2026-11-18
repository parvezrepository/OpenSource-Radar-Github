"""Tests for TelegramService notification dispatch and connection testing."""

from unittest.mock import MagicMock, patch
import pytest

from services.telegram_service import TelegramService


@pytest.fixture
def configured_service():
    """Return a TelegramService with mock credentials."""
    return TelegramService(bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", chat_id="987654321")


@pytest.fixture
def unconfigured_service():
    """Return a TelegramService without credentials."""
    return TelegramService(bot_token="", chat_id="")


def test_is_configured_flag(configured_service, unconfigured_service):
    """Verify is_configured accurately reflects credential readiness."""
    assert configured_service.is_configured is True
    assert unconfigured_service.is_configured is False


def test_send_message_unconfigured(unconfigured_service):
    """Unconfigured service should gracefully return False without network call."""
    res = unconfigured_service.send_message("Test hello")
    assert res is False


@patch("requests.post")
def test_send_message_success(mock_post, configured_service):
    """Successful HTTP 200 delivery returns True."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True}
    mock_post.return_value = mock_resp

    result = configured_service.send_message("<b>Hello Telegram!</b>", parse_mode="HTML")
    assert result is True
    assert mock_post.called
    args, kwargs = mock_post.call_args
    assert "https://api.telegram.org/bot123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11/sendMessage" in args[0]
    assert kwargs["json"]["chat_id"] == "987654321"
    assert kwargs["json"]["text"] == "<b>Hello Telegram!</b>"


@patch("requests.post")
def test_send_message_http_error(mock_post, configured_service):
    """HTTP 400 error returns False without exception."""
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = '{"ok":false,"description":"Bad Request: chat not found"}'
    mock_post.return_value = mock_resp

    result = configured_service.send_message("Fail test")
    assert result is False


@patch("requests.post")
def test_send_repository_alert(mock_post, configured_service):
    """Test repository alert message structuring and delivery."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    repo_data = {
        "full_name": "Significant-Gravitas/AutoGPT",
        "html_url": "https://github.com/Significant-Gravitas/AutoGPT",
        "stars": 169000,
        "forks": 42000,
        "primary_language": "Python",
        "description": "AutoGPT is an experimental open-source attempt to make GPT-4 fully autonomous.",
        "topics": ["ai-agents", "autonomous", "llm"],
    }
    score_report = {"total_score": 92}

    success = configured_service.send_repository_alert(repo_data, score_report=score_report, reason="Elite Mover")
    assert success is True
    args, kwargs = mock_post.call_args
    sent_text = kwargs["json"]["text"]
    assert "Elite Mover" in sent_text
    assert "Significant-Gravitas/AutoGPT" in sent_text
    assert "92/100" in sent_text
    assert "ai_agents" in sent_text


@patch("requests.get")
@patch("requests.post")
def test_test_connection_success(mock_post, mock_get, configured_service):
    """Verify test_connection returns status connected on valid bot & ping."""
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = {"ok": True, "result": {"username": "RadarBot", "first_name": "OpenSource Radar"}}
    mock_get.return_value = mock_get_resp

    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post.return_value = mock_post_resp

    res = configured_service.test_connection()
    assert res["status"] == "connected"
    assert res["bot_username"] == "RadarBot"
    assert res["chat_id"] == "987654321"


def test_test_connection_unconfigured(unconfigured_service):
    """Unconfigured service test_connection returns error dict without calling requests."""
    res = unconfigured_service.test_connection()
    assert res["status"] == "error"
    assert "TELEGRAM_BOT_TOKEN" in res["error"]

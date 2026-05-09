import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.tools.notify import send_slack_message


@pytest.mark.asyncio
async def test_send_slack_message():
    with patch("src.tools.notify.settings") as mock_settings:
        mock_settings.slack_webhook_url = "https://hooks.slack.com/test"
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            mock_post.return_value = mock_resp
            result = await send_slack_message("测试消息")
            assert result is True


@pytest.mark.asyncio
async def test_send_slack_message_no_webhook():
    with patch("src.tools.notify.settings") as mock_settings:
        mock_settings.slack_webhook_url = ""
        result = await send_slack_message("测试")
        assert result is False

"""Tests for the Telegram integration and channel API.

The actual Telegram Bot API is mocked -- no real bot token or network calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestTelegramBotInitialization:
    """Verify TelegramBot can be instantiated without external services."""

    def test_telegram_bot_can_be_instantiated(self):
        """TelegramBot constructor should not call any external services."""
        from app.integrations.telegram import TelegramBot

        ws_manager = AsyncMock()
        db_session_factory = AsyncMock()

        bot = TelegramBot(
            bot_token="fake-bot-token-12345",
            ws_manager=ws_manager,
            db_session_factory=db_session_factory,
        )

        assert bot.bot_token == "fake-bot-token-12345"
        assert bot.ws_manager is ws_manager
        assert bot.db_session_factory is db_session_factory
        assert bot._app is None  # Not started yet
        assert bot._polling_task is None

    def test_telegram_bot_has_empty_history_initially(self):
        """Fresh bot instance should have empty conversation history."""
        from app.integrations.telegram import TelegramBot

        bot = TelegramBot(
            bot_token="fake-token",
            ws_manager=AsyncMock(),
            db_session_factory=AsyncMock(),
        )
        assert len(bot._history) == 0

    def test_telegram_bot_is_channel_adapter(self):
        """TelegramBot should be a subclass of ChannelAdapter."""
        from app.integrations.base import ChannelAdapter
        from app.integrations.telegram import TelegramBot

        assert issubclass(TelegramBot, ChannelAdapter)


class TestChannelCreationAPI:
    """Test the channel CRUD endpoints."""

    async def test_create_telegram_channel(self, client: AsyncClient):
        """POST /api/channels with telegram type returns 201."""
        payload = {
            "type": "telegram",
            "name": "Test Telegram Channel",
            "config": {"bot_token": "fake-token-123"},
            "is_active": True,
        }
        resp = await client.post("/api/channels/", json=payload)
        assert resp.status_code == 201

        body = resp.json()
        assert body["type"] == "telegram"
        assert body["name"] == "Test Telegram Channel"
        assert body["config"] == {"bot_token": "fake-token-123"}
        assert body["is_active"] is True
        assert "id" in body
        assert "created_at" in body

    async def test_create_channel_with_agent_id(
        self, client: AsyncClient, sample_agent_data: dict
    ):
        """A channel can be linked to an existing agent."""
        # First create an agent
        agent_resp = await client.post("/api/agents/", json=sample_agent_data)
        agent_id = agent_resp.json()["id"]

        payload = {
            "type": "telegram",
            "name": "Agent-linked Channel",
            "config": {},
            "agent_id": agent_id,
            "is_active": True,
        }
        resp = await client.post("/api/channels/", json=payload)
        assert resp.status_code == 201
        assert resp.json()["agent_id"] == agent_id

    async def test_list_channels(self, client: AsyncClient):
        """GET /api/channels returns all channels."""
        payload1 = {
            "type": "telegram",
            "name": "Channel A",
            "config": {},
        }
        payload2 = {
            "type": "telegram",
            "name": "Channel B",
            "config": {},
        }
        await client.post("/api/channels/", json=payload1)
        await client.post("/api/channels/", json=payload2)

        resp = await client.get("/api/channels/")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 2
        names = {c["name"] for c in body}
        assert "Channel A" in names
        assert "Channel B" in names

    async def test_delete_channel(self, client: AsyncClient):
        """DELETE /api/channels/{id} removes the channel."""
        payload = {
            "type": "telegram",
            "name": "Deletable Channel",
            "config": {},
        }
        create_resp = await client.post("/api/channels/", json=payload)
        channel_id = create_resp.json()["id"]

        delete_resp = await client.delete(f"/api/channels/{channel_id}")
        assert delete_resp.status_code == 204

    async def test_delete_channel_not_found(self, client: AsyncClient):
        """DELETE /api/channels/{id} with non-existent id returns 404."""
        import uuid

        fake_id = str(uuid.uuid4())
        resp = await client.delete(f"/api/channels/{fake_id}")
        assert resp.status_code == 404

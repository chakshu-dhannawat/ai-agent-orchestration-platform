"""Abstract base class for channel adapters (Telegram, Slack, Discord, etc.)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ChannelAdapter(ABC):
    """Base class every messaging-platform integration must implement.

    Sub-classes are responsible for:
    - Connecting to the external service (``start``/``stop``).
    - Forwarding incoming user messages to the orchestration engine.
    - Sending bot responses back to the external service.
    """

    @abstractmethod
    async def start(self) -> None:
        """Start listening for incoming messages (polling, webhook, etc.)."""

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully disconnect and release resources."""

    @abstractmethod
    async def send_message(self, chat_id: str | int, text: str) -> Any:
        """Send a text message to the given chat/conversation.

        Parameters
        ----------
        chat_id:
            Platform-specific identifier for the target conversation.
        text:
            The message body to send.
        """

    @abstractmethod
    async def handle_incoming(self, message: dict) -> None:
        """Process a single inbound message from the platform.

        Parameters
        ----------
        message:
            Platform-specific message payload.
        """

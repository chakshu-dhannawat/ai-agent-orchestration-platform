"""Optional LangChain callbacks for additional streaming and logging."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


class WorkflowStreamingCallback(AsyncCallbackHandler):
    """Async callback that streams LLM tokens and lifecycle events via WebSocket."""

    def __init__(
        self,
        ws_manager,
        execution_id: str,
        node_id: str,
        agent_name: str,
    ):
        super().__init__()
        self.ws_manager = ws_manager
        self.execution_id = execution_id
        self.node_id = node_id
        self.agent_name = agent_name

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Stream individual tokens to the frontend."""
        await self.ws_manager.broadcast_to_execution(
            self.execution_id,
            {
                "type": "token",
                "node_id": self.node_id,
                "agent_name": self.agent_name,
                "token": token,
            },
        )

    async def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        logger.debug(
            "LLM start: node=%s agent=%s run=%s",
            self.node_id,
            self.agent_name,
            run_id,
        )

    async def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        logger.debug(
            "Chat model start: node=%s agent=%s run=%s",
            self.node_id,
            self.agent_name,
            run_id,
        )

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        logger.debug(
            "LLM end: node=%s agent=%s run=%s",
            self.node_id,
            self.agent_name,
            run_id,
        )

    async def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        logger.error(
            "LLM error in node=%s agent=%s: %s",
            self.node_id,
            self.agent_name,
            error,
        )
        await self.ws_manager.broadcast_to_execution(
            self.execution_id,
            {
                "type": "error",
                "node_id": self.node_id,
                "agent_name": self.agent_name,
                "error": str(error),
            },
        )

"""Telegram bot integration using python-telegram-bot v21+ (async).

Supports POLLING mode (default, works without a public URL) for local
development and testing.  Set ``TELEGRAM_MODE=polling`` (the default) in your
``.env`` to use this mode.

The bot looks up the ``Channel`` record whose ``config.bot_token`` matches the
token it was initialised with.  Depending on whether that channel links to a
``workflow_id`` or an ``agent_id`` it will either run a full workflow execution
or have a direct LLM conversation with the linked agent.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.integrations.base import ChannelAdapter
from app.models.agent import Agent
from app.models.channel import Channel
from app.models.execution import ExecutionLog, WorkflowExecution
from app.models.message import AgentMessage
from app.models.workflow import Workflow

logger = logging.getLogger(__name__)

# Maximum number of previous turns (pairs) to keep per chat for context.
_MAX_HISTORY_TURNS = 40


class TelegramBot(ChannelAdapter):
    """Telegram bot adapter -- polling mode.

    Parameters
    ----------
    bot_token:
        The Telegram Bot API token (from BotFather).
    ws_manager:
        ``ConnectionManager`` instance for pushing real-time WebSocket events.
    db_session_factory:
        An ``async_sessionmaker[AsyncSession]`` to obtain database sessions.
    """

    def __init__(
        self,
        bot_token: str,
        ws_manager: Any,
        db_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.bot_token = bot_token
        self.ws_manager = ws_manager
        self.db_session_factory = db_session_factory

        # Per-chat conversation history: chat_id -> list[BaseMessage]
        self._history: dict[int, list] = defaultdict(list)

        # The python-telegram-bot Application instance (created in start()).
        self._app: Application | None = None
        self._polling_task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # ChannelAdapter interface
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Build the Application, register handlers and start polling."""

        builder = Application.builder().token(self.bot_token)
        self._app = builder.build()

        # Register command handlers
        self._app.add_handler(CommandHandler("start", self._cmd_start))
        self._app.add_handler(CommandHandler("help", self._cmd_help))
        self._app.add_handler(CommandHandler("reset", self._cmd_reset))

        # Catch-all for normal text messages
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message)
        )

        # Register an error handler
        self._app.add_error_handler(self._error_handler)

        # Initialize and start polling in a background task so the caller
        # (FastAPI lifespan) is not blocked.
        await self._app.initialize()
        await self._app.start()

        self._polling_task = asyncio.create_task(
            self._run_polling(), name="telegram-polling"
        )

        logger.info("Telegram bot started in polling mode.")

    async def stop(self) -> None:
        """Gracefully shut down the polling loop and the Application."""

        if self._app is None:
            return

        logger.info("Stopping Telegram bot ...")

        # Signal the updater to stop polling
        if self._app.updater and self._app.updater.running:
            await self._app.updater.stop()

        # Cancel the wrapper task if it's still alive
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass

        await self._app.stop()
        await self._app.shutdown()

        logger.info("Telegram bot stopped.")

    async def send_message(self, chat_id: str | int, text: str) -> Any:
        """Send *text* to a Telegram chat identified by *chat_id*."""

        if self._app is None:
            raise RuntimeError("Telegram bot has not been started yet.")

        # Telegram has a 4096-char limit per message.  Split if needed.
        max_len = 4096
        if len(text) <= max_len:
            return await self._app.bot.send_message(chat_id=int(chat_id), text=text)

        # Split on paragraph boundaries when possible.
        chunks = _split_text(text, max_len)
        last_result = None
        for chunk in chunks:
            last_result = await self._app.bot.send_message(
                chat_id=int(chat_id), text=chunk
            )
        return last_result

    async def handle_incoming(self, message: dict) -> None:
        """Not used directly -- the python-telegram-bot dispatcher routes
        updates to ``_on_message`` automatically.  Provided for interface
        compliance."""

        logger.debug("handle_incoming called with raw dict: %s", message)

    # ------------------------------------------------------------------
    # Internal: polling loop
    # ------------------------------------------------------------------

    async def _run_polling(self) -> None:
        """Wrapper around ``updater.start_polling`` so it runs inside an
        asyncio task."""

        try:
            await self._app.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES,
            )
            # Keep the task alive until cancelled.
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            logger.debug("Polling task cancelled.")
        except Exception:
            logger.exception("Telegram polling loop crashed.")

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------

    async def _cmd_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the ``/start`` command."""

        welcome = (
            "Welcome to the AI Agent Orchestration Platform!\n\n"
            "I'm connected to a powerful AI backend that can run workflows "
            "and chat with specialised agents.\n\n"
            "Just type your message and I'll get to work.\n\n"
            "Commands:\n"
            "/help  - Show available commands\n"
            "/reset - Clear conversation history"
        )
        await update.message.reply_text(welcome)

    async def _cmd_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the ``/help`` command."""

        help_text = (
            "Available commands:\n\n"
            "/start - Welcome message and bot info\n"
            "/help  - Show this help message\n"
            "/reset - Clear conversation history and start fresh\n\n"
            "You can also just send any text message and I'll process it "
            "through the connected AI agent or workflow."
        )
        await update.message.reply_text(help_text)

    async def _cmd_reset(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle the ``/reset`` command -- clears per-chat history."""

        chat_id = update.effective_chat.id
        self._history.pop(chat_id, None)
        await update.message.reply_text(
            "Conversation history cleared. Send a new message to start fresh."
        )

    # ------------------------------------------------------------------
    # Message handler (core logic)
    # ------------------------------------------------------------------

    async def _on_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Process an incoming user text message."""

        if not update.message or not update.message.text:
            return

        chat_id = update.effective_chat.id
        user_text = update.message.text
        user_name = update.effective_user.full_name if update.effective_user else "User"

        logger.info(
            "Telegram message from %s (chat %s): %s",
            user_name,
            chat_id,
            user_text[:120],
        )

        # Show "typing..." indicator while we process.
        await update.message.chat.send_action("typing")

        try:
            # 1. Look up the Channel record for this bot token.
            channel, agent, workflow = await self._resolve_channel()

            if channel is None:
                await update.message.reply_text(
                    "This bot is not linked to any channel configuration yet. "
                    "Please set up a Telegram channel in the platform dashboard."
                )
                return

            # 2. Dispatch to workflow execution or direct agent chat.
            if workflow is not None:
                response_text = await self._execute_workflow(
                    workflow=workflow,
                    channel=channel,
                    chat_id=chat_id,
                    user_text=user_text,
                    user_name=user_name,
                )
            elif agent is not None:
                response_text = await self._chat_with_agent(
                    agent=agent,
                    channel=channel,
                    chat_id=chat_id,
                    user_text=user_text,
                    user_name=user_name,
                )
            else:
                response_text = (
                    "This channel has no agent or workflow assigned. "
                    "Please configure one in the platform dashboard."
                )

            # 3. Send the reply.
            await self.send_message(chat_id, response_text)

        except Exception:
            logger.exception("Error processing Telegram message from chat %s", chat_id)
            await update.message.reply_text(
                "Sorry, something went wrong while processing your message. "
                "Please try again in a moment."
            )

    # ------------------------------------------------------------------
    # Channel / agent / workflow resolution
    # ------------------------------------------------------------------

    async def _resolve_channel(
        self,
    ) -> tuple[Channel | None, Agent | None, Workflow | None]:
        """Find the Channel row whose ``config['bot_token']`` matches ours
        and eagerly load the related Agent and Workflow."""

        async with self.db_session_factory() as db:
            result = await db.execute(
                select(Channel)
                .options(
                    selectinload(Channel.agent),
                    selectinload(Channel.workflow),
                )
                .where(Channel.type == "telegram", Channel.is_active.is_(True))
            )
            channels = result.scalars().all()

        for ch in channels:
            cfg = ch.config or {}
            if cfg.get("bot_token") == self.bot_token:
                return ch, ch.agent, ch.workflow

        # Fallback: if there is exactly one active Telegram channel, use it
        # even if it doesn't store the token (backwards-compat convenience).
        if len(channels) == 1:
            ch = channels[0]
            return ch, ch.agent, ch.workflow

        return None, None, None

    # ------------------------------------------------------------------
    # Workflow execution path
    # ------------------------------------------------------------------

    async def _execute_workflow(
        self,
        workflow: Workflow,
        channel: Channel,
        chat_id: int,
        user_text: str,
        user_name: str,
    ) -> str:
        """Create a WorkflowExecution, compile and run the workflow, return
        the final output text."""

        # Lazy import to avoid circular dependencies at module level.
        from app.engine.runtime import WorkflowRuntime

        execution_id = str(uuid.uuid4())

        # Persist the execution record.
        async with self.db_session_factory() as db:
            execution = WorkflowExecution(
                id=uuid.UUID(execution_id),
                workflow_id=workflow.id,
                status="pending",
                input_data={
                    "message": user_text,
                    "source": "telegram",
                    "chat_id": chat_id,
                    "user_name": user_name,
                },
            )
            db.add(execution)
            await db.commit()

        # Build agent map from the graph definition.
        agents_map = await self._build_agents_map(workflow)

        # Compile and execute.
        runtime = WorkflowRuntime(
            ws_manager=self.ws_manager,
            db_session_factory=self.db_session_factory,
        )

        try:
            graph = await runtime.compile(
                workflow_dict=workflow.graph_definition,
                agents_map=agents_map,
                execution_id=execution_id,
            )
            result_state = await runtime.execute(
                execution_id=execution_id,
                workflow_id=str(workflow.id),
                graph=graph,
                input_data={"message": user_text},
            )

            final_output = result_state.get("final_output")
            if final_output:
                return str(final_output)
            return "Workflow completed but produced no output."

        except Exception as exc:
            logger.exception(
                "Workflow execution %s failed for chat %s", execution_id, chat_id
            )

            # Mark execution as failed.
            async with self.db_session_factory() as db:
                result = await db.execute(
                    select(WorkflowExecution).where(
                        WorkflowExecution.id == uuid.UUID(execution_id)
                    )
                )
                ex = result.scalar_one_or_none()
                if ex:
                    ex.status = "failed"
                    ex.error = str(exc)
                    ex.completed_at = datetime.now(timezone.utc)
                    await db.commit()

            return (
                "I encountered an error while running the workflow. "
                "Please try again or contact the administrator."
            )

    async def _build_agents_map(self, workflow: Workflow) -> dict[str, dict]:
        """Build the ``agents_map`` dict required by ``WorkflowRuntime.compile``.

        It maps agent UUIDs to config dicts by reading the Agent rows
        referenced in the workflow's graph definition.
        """

        graph_def = workflow.graph_definition or {}
        nodes = graph_def.get("nodes", [])

        agent_ids: set[str] = set()
        for node in nodes:
            aid = node.get("data", {}).get("agent_id")
            if aid:
                agent_ids.add(aid)

        if not agent_ids:
            return {}

        async with self.db_session_factory() as db:
            result = await db.execute(
                select(Agent).where(
                    Agent.id.in_([uuid.UUID(a) for a in agent_ids])
                )
            )
            agents = result.scalars().all()

        agents_map: dict[str, dict] = {}
        for ag in agents:
            agents_map[str(ag.id)] = {
                "name": ag.name,
                "role": ag.role,
                "system_prompt": ag.system_prompt,
                "model": ag.model,
                "temperature": ag.temperature,
                "max_tokens": ag.max_tokens,
                "guardrails": ag.guardrails or {},
                "tools": ag.tools or [],
            }

        return agents_map

    # ------------------------------------------------------------------
    # Direct agent chat path
    # ------------------------------------------------------------------

    async def _chat_with_agent(
        self,
        agent: Agent,
        channel: Channel,
        chat_id: int,
        user_text: str,
        user_name: str,
    ) -> str:
        """Have a direct LLM conversation with the linked agent, keeping
        per-chat history for multi-turn context."""

        # Append the new user message to history.
        history = self._history[chat_id]
        history.append(HumanMessage(content=user_text))

        # Trim history to the last N messages to keep token usage bounded.
        if len(history) > _MAX_HISTORY_TURNS:
            history[:] = history[-_MAX_HISTORY_TURNS:]

        # Build the messages list for the LLM.
        messages: list = []
        system_prompt = agent.system_prompt or ""
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.extend(history)

        # Create a WorkflowExecution record so the message is tracked in the DB.
        execution_id = str(uuid.uuid4())

        # We create a minimal execution record linked to a pseudo-workflow.
        # Since there is no workflow, we still need a workflow_id FK.
        # We'll create a lightweight record approach: persist messages directly.
        async with self.db_session_factory() as db:
            # Persist incoming user message.
            db.add(
                AgentMessage(
                    execution_id=uuid.UUID(execution_id),
                    from_agent=user_name,
                    to_agent=agent.name,
                    content=user_text,
                    message_type="text",
                    metadata_={
                        "source": "telegram",
                        "chat_id": chat_id,
                    },
                )
            )
            # We need a WorkflowExecution row for the FK.  Create a stub one
            # that can be attached to the agent's first workflow or a sentinel.
            # -- To avoid FK issues with workflow_id being NOT NULL, we first
            #    check if there's a default workflow, otherwise we skip
            #    persisting under an execution.
            #
            # For robustness we create the execution only if there's a
            # workflow, otherwise just persist the AgentMessage standalone.
            # Since AgentMessage requires execution_id FK, we need a valid
            # WorkflowExecution.  Let's create a "direct-chat" stub workflow
            # lazily.
            stub_wf = await self._get_or_create_direct_chat_workflow(db)
            execution = WorkflowExecution(
                id=uuid.UUID(execution_id),
                workflow_id=stub_wf.id,
                status="running",
                input_data={
                    "message": user_text,
                    "source": "telegram",
                    "chat_id": chat_id,
                    "user_name": user_name,
                },
                started_at=datetime.now(timezone.utc),
            )
            db.add(execution)
            await db.commit()

        # Call the LLM.
        try:
            llm = ChatOpenAI(
                model=agent.model or "gpt-4o-mini",
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
            )
            response = await llm.ainvoke(messages)
            reply_text = response.content

            # Track token usage.
            usage = getattr(response, "usage_metadata", None) or {}
            prompt_tokens = usage.get("input_tokens", 0)
            completion_tokens = usage.get("output_tokens", 0)

        except Exception as exc:
            logger.exception("Agent LLM call failed for chat %s", chat_id)
            reply_text = (
                "I'm having trouble connecting to the AI service right now. "
                "Please try again in a moment."
            )
            prompt_tokens = 0
            completion_tokens = 0

        # Append assistant reply to history.
        history.append(AIMessage(content=reply_text))

        # Persist the bot response and update the execution.
        async with self.db_session_factory() as db:
            db.add(
                AgentMessage(
                    execution_id=uuid.UUID(execution_id),
                    from_agent=agent.name,
                    to_agent=user_name,
                    content=reply_text,
                    message_type="text",
                    metadata_={
                        "source": "telegram",
                        "chat_id": chat_id,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "model": agent.model,
                    },
                )
            )
            result = await db.execute(
                select(WorkflowExecution).where(
                    WorkflowExecution.id == uuid.UUID(execution_id)
                )
            )
            ex = result.scalar_one_or_none()
            if ex:
                ex.status = "completed"
                ex.completed_at = datetime.now(timezone.utc)
                ex.output_data = {"final_output": reply_text}
                ex.total_tokens = prompt_tokens + completion_tokens
                ex.prompt_tokens = prompt_tokens
                ex.completion_tokens = completion_tokens
            await db.commit()

        # Push a dashboard event so the UI updates in real time.
        await self.ws_manager.broadcast_to_dashboard(
            {
                "type": "telegram_message",
                "chat_id": chat_id,
                "user_name": user_name,
                "agent_name": agent.name,
                "execution_id": execution_id,
            }
        )

        return reply_text

    async def _get_or_create_direct_chat_workflow(
        self, db: AsyncSession
    ) -> Workflow:
        """Return a stub ``Workflow`` used to anchor direct-chat executions.

        If one doesn't exist yet it will be created.  This avoids FK
        violations on ``WorkflowExecution.workflow_id`` which is NOT NULL.
        """

        _STUB_NAME = "__telegram_direct_chat__"

        result = await db.execute(
            select(Workflow).where(Workflow.name == _STUB_NAME)
        )
        stub = result.scalar_one_or_none()
        if stub is not None:
            return stub

        stub = Workflow(
            name=_STUB_NAME,
            description="Internal stub workflow for Telegram direct agent chats.",
            is_template=False,
            graph_definition={"nodes": [], "edges": []},
        )
        db.add(stub)
        await db.flush()
        await db.refresh(stub)
        return stub

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    async def _error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Log errors caused by Updates."""

        logger.error(
            "Telegram update caused error: %s",
            context.error,
            exc_info=context.error,
        )

        if isinstance(update, Update) and update.effective_chat:
            try:
                await self._app.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "An unexpected error occurred. "
                        "Please try again or contact the administrator."
                    ),
                )
            except Exception:
                logger.exception("Failed to send error message to user.")


# ------------------------------------------------------------------
# Utility helpers
# ------------------------------------------------------------------


def _split_text(text: str, max_len: int) -> list[str]:
    """Split *text* into chunks of at most *max_len* characters, preferring
    paragraph boundaries."""

    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    remaining = text

    while remaining:
        if len(remaining) <= max_len:
            chunks.append(remaining)
            break

        # Try to split at the last double-newline within the limit.
        split_at = remaining.rfind("\n\n", 0, max_len)
        if split_at == -1:
            # Fall back to single newline.
            split_at = remaining.rfind("\n", 0, max_len)
        if split_at == -1:
            # Fall back to space.
            split_at = remaining.rfind(" ", 0, max_len)
        if split_at == -1:
            # Hard split.
            split_at = max_len

        chunks.append(remaining[: split_at + 1].rstrip())
        remaining = remaining[split_at + 1 :].lstrip()

    return chunks

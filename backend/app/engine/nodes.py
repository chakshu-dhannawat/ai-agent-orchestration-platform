"""Agent node factory: builds async callables that serve as LangGraph nodes."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from app.engine.callbacks import WorkflowStreamingCallback
from app.engine.state import WorkflowState
from app.engine.tools import get_tools_by_names
from app.models.execution import ExecutionLog
from app.models.message import AgentMessage

logger = logging.getLogger(__name__)

# Cost per 1M tokens (input / output) by model name
MODEL_COSTS: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini-2024-07-18": (0.15, 0.60),
    "gpt-4o-2024-08-06": (2.50, 10.00),
}

# Fallback cost for unknown models
_DEFAULT_COST = (1.00, 3.00)


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Return estimated cost in USD for given token counts."""
    input_cost, output_cost = MODEL_COSTS.get(model, _DEFAULT_COST)
    return (prompt_tokens * input_cost + completion_tokens * output_cost) / 1_000_000


def _check_guardrails(content: str, guardrails: dict) -> str | None:
    """Check content against guardrails. Returns an error message if blocked, else None."""
    blocked_topics = guardrails.get("blocked_topics", [])
    if not blocked_topics:
        return None

    content_lower = content.lower()
    for topic in blocked_topics:
        if topic.lower() in content_lower:
            return f"Content blocked by guardrail: contains blocked topic '{topic}'"
    return None


def create_agent_node(
    agent_config: dict,
    tools: list,
    ws_manager,
    execution_id: str,
    db_session_factory,
    node_id: str,
) -> Callable[[WorkflowState], Coroutine[Any, Any, WorkflowState]]:
    """Create an async callable that acts as a LangGraph node for one agent.

    Parameters
    ----------
    agent_config : dict
        Agent definition with keys: name, role, system_prompt, model,
        temperature, max_tokens, guardrails, tools, etc.
    tools : list
        Resolved LangChain tool objects this agent may call.
    ws_manager :
        ConnectionManager for pushing WebSocket events.
    execution_id : str
        Current workflow execution id.
    db_session_factory :
        An async_sessionmaker that yields AsyncSession instances.
    node_id : str
        The graph node id (e.g. ``"agent-1"``).
    """

    agent_name = agent_config.get("name", node_id)
    model_name = agent_config.get("model", "gpt-4o-mini")
    temperature = agent_config.get("temperature", 0.7)
    max_tokens = agent_config.get("max_tokens", 4096)
    system_prompt = agent_config.get("system_prompt", "")
    guardrails = agent_config.get("guardrails", {})

    async def agent_node(state: WorkflowState) -> WorkflowState:
        """Execute the agent: call LLM, handle tool calls, persist results."""

        # ----- Build the LLM --------------------------------------------------
        callback = WorkflowStreamingCallback(
            ws_manager=ws_manager,
            execution_id=execution_id,
            node_id=node_id,
            agent_name=agent_name,
        )
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            callbacks=[callback],
        )

        if tools:
            llm_with_tools = llm.bind_tools(tools)
        else:
            llm_with_tools = llm

        # ----- Assemble messages -----------------------------------------------
        messages: list = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        # Include conversation history from state
        messages.extend(state["messages"])

        # ----- Guardrail: check input ------------------------------------------
        last_human = next(
            (m.content for m in reversed(messages) if isinstance(m, HumanMessage)),
            "",
        )
        block_msg = _check_guardrails(last_human, guardrails)
        if block_msg:
            logger.warning("Guardrail blocked input for %s: %s", agent_name, block_msg)
            blocked_ai = AIMessage(content=block_msg)
            return {
                "messages": [blocked_ai],
                "intermediate_results": {
                    **state.get("intermediate_results", {}),
                    node_id: {"blocked": True, "reason": block_msg},
                },
                "metadata": state.get("metadata", {}),
            }

        # ----- Emit "node started" event via WS --------------------------------
        await ws_manager.broadcast_to_execution(
            execution_id,
            {
                "type": "node_started",
                "node_id": node_id,
                "agent_name": agent_name,
            },
        )

        # ----- Call the LLM ----------------------------------------------------
        total_prompt_tokens = 0
        total_completion_tokens = 0

        try:
            response = await llm_with_tools.ainvoke(messages)
        except Exception as exc:
            logger.error("LLM call failed for %s: %s", agent_name, exc)
            error_ai = AIMessage(
                content=f"Agent '{agent_name}' encountered an error: {exc}"
            )
            # Persist error log
            async with db_session_factory() as db:
                db.add(
                    ExecutionLog(
                        execution_id=execution_id,
                        level="error",
                        node_id=node_id,
                        agent_name=agent_name,
                        message=f"LLM call failed: {exc}",
                    )
                )
                await db.commit()

            # Broadcast the error log via WebSocket
            await ws_manager.broadcast_to_execution(
                execution_id,
                {
                    "type": "log",
                    "payload": {
                        "execution_id": execution_id,
                        "level": "error",
                        "node_id": node_id,
                        "agent_name": agent_name,
                        "message": f"LLM call failed: {exc}",
                        "metadata": {},
                    },
                },
            )

            await ws_manager.broadcast_to_execution(
                execution_id,
                {
                    "type": "node_error",
                    "node_id": node_id,
                    "agent_name": agent_name,
                    "error": str(exc),
                },
            )
            return {
                "messages": [error_ai],
                "intermediate_results": {
                    **state.get("intermediate_results", {}),
                    node_id: {"error": str(exc)},
                },
                "metadata": state.get("metadata", {}),
            }

        # Track token usage from initial call
        usage = getattr(response, "usage_metadata", None) or {}
        total_prompt_tokens += usage.get("input_tokens", 0)
        total_completion_tokens += usage.get("output_tokens", 0)

        # ----- Tool call loop --------------------------------------------------
        collected_messages = [response]
        tool_map = {t.name: t for t in tools} if tools else {}
        virtual_files: dict[str, str] = {}

        max_tool_rounds = 10
        round_count = 0
        while response.tool_calls and round_count < max_tool_rounds:
            round_count += 1
            tool_messages: list[ToolMessage] = []

            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                tool_call_id = tc["id"]

                logger.info(
                    "Agent %s calling tool %s with args %s",
                    agent_name,
                    tool_name,
                    tool_args,
                )

                await ws_manager.broadcast_to_execution(
                    execution_id,
                    {
                        "type": "tool_call",
                        "node_id": node_id,
                        "agent_name": agent_name,
                        "tool": tool_name,
                        "args": tool_args,
                    },
                )

                if tool_name in tool_map:
                    try:
                        tool_result = await tool_map[tool_name].ainvoke(tool_args)
                    except Exception as tool_exc:
                        tool_result = f"Tool error: {tool_exc}"

                    # Handle virtual file writes
                    if (
                        isinstance(tool_result, str)
                        and tool_result.startswith("__FILE_WRITE__:")
                    ):
                        parts = tool_result.split(":", 2)
                        if len(parts) == 3:
                            fname = parts[1]
                            fcontent = parts[2]
                            virtual_files[fname] = fcontent
                            tool_result = f"File '{fname}' written successfully ({len(fcontent)} chars)."
                else:
                    tool_result = f"Tool '{tool_name}' not found."

                tool_messages.append(
                    ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call_id,
                    )
                )

                await ws_manager.broadcast_to_execution(
                    execution_id,
                    {
                        "type": "tool_result",
                        "node_id": node_id,
                        "agent_name": agent_name,
                        "tool": tool_name,
                        "result": str(tool_result)[:500],
                    },
                )

            collected_messages.extend(tool_messages)

            # Call LLM again with tool results
            follow_up_messages = messages + collected_messages
            try:
                response = await llm_with_tools.ainvoke(follow_up_messages)
            except Exception as exc:
                logger.error(
                    "Follow-up LLM call failed for %s after tool use: %s",
                    agent_name,
                    exc,
                )
                response = AIMessage(
                    content=f"Agent encountered an error processing tool results: {exc}"
                )
                break

            usage = getattr(response, "usage_metadata", None) or {}
            total_prompt_tokens += usage.get("input_tokens", 0)
            total_completion_tokens += usage.get("output_tokens", 0)
            collected_messages.append(response)

        # The final AI response content
        final_content = response.content if isinstance(response, AIMessage) else str(response)

        # ----- Guardrail: check output ------------------------------------------
        block_msg = _check_guardrails(final_content, guardrails)
        if block_msg:
            logger.warning("Guardrail blocked output for %s: %s", agent_name, block_msg)
            final_content = block_msg

        # ----- Persist AgentMessage to DB ---------------------------------------
        async with db_session_factory() as db:
            agent_msg = AgentMessage(
                execution_id=execution_id,
                from_agent=agent_name,
                to_agent="workflow",
                content=final_content,
                message_type="text",
                metadata_={
                    "node_id": node_id,
                    "model": model_name,
                    "prompt_tokens": total_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                },
            )
            db.add(agent_msg)

            # Log entry
            db.add(
                ExecutionLog(
                    execution_id=execution_id,
                    level="info",
                    node_id=node_id,
                    agent_name=agent_name,
                    message=f"Agent '{agent_name}' completed. Tokens: {total_prompt_tokens}+{total_completion_tokens}",
                    metadata_={
                        "prompt_tokens": total_prompt_tokens,
                        "completion_tokens": total_completion_tokens,
                        "model": model_name,
                    },
                )
            )
            await db.commit()

        # ----- Emit events via WS -----------------------------------------------
        # Broadcast the agent message so the frontend can display it in real-time
        await ws_manager.broadcast_to_execution(
            execution_id,
            {
                "type": "message",
                "payload": {
                    "execution_id": execution_id,
                    "from_agent": agent_name,
                    "to_agent": "workflow",
                    "content": final_content,
                    "message_type": "text",
                    "metadata": {
                        "node_id": node_id,
                        "model": model_name,
                        "prompt_tokens": total_prompt_tokens,
                        "completion_tokens": total_completion_tokens,
                    },
                },
            },
        )

        # Broadcast the log entry so the frontend log stream updates in real-time
        await ws_manager.broadcast_to_execution(
            execution_id,
            {
                "type": "log",
                "payload": {
                    "execution_id": execution_id,
                    "level": "info",
                    "node_id": node_id,
                    "agent_name": agent_name,
                    "message": f"Agent '{agent_name}' completed. Tokens: {total_prompt_tokens}+{total_completion_tokens}",
                    "metadata": {
                        "prompt_tokens": total_prompt_tokens,
                        "completion_tokens": total_completion_tokens,
                        "model": model_name,
                    },
                },
            },
        )

        await ws_manager.broadcast_to_execution(
            execution_id,
            {
                "type": "node_completed",
                "node_id": node_id,
                "agent_name": agent_name,
            },
        )

        # ----- Calculate cost ---------------------------------------------------
        cost = _estimate_cost(model_name, total_prompt_tokens, total_completion_tokens)

        # ----- Build updated metadata -------------------------------------------
        prev_meta = state.get("metadata", {})
        new_meta = {
            **prev_meta,
            "total_prompt_tokens": prev_meta.get("total_prompt_tokens", 0) + total_prompt_tokens,
            "total_completion_tokens": prev_meta.get("total_completion_tokens", 0) + total_completion_tokens,
            "total_tokens": (
                prev_meta.get("total_tokens", 0) + total_prompt_tokens + total_completion_tokens
            ),
            "total_cost_usd": prev_meta.get("total_cost_usd", 0.0) + cost,
        }

        # ----- Node result ------------------------------------------------------
        node_result: dict[str, Any] = {
            "content": final_content,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "cost_usd": cost,
            "model": model_name,
        }
        if virtual_files:
            node_result["files"] = virtual_files

        intermediate = {**state.get("intermediate_results", {}), node_id: node_result}

        # Return the state update (LangGraph merges this via reducers)
        return {
            "messages": collected_messages,
            "intermediate_results": intermediate,
            "final_output": final_content,
            "metadata": new_meta,
        }

    return agent_node

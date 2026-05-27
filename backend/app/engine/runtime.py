"""WorkflowRuntime: compiles visual workflow graphs into executable LangGraph StateGraphs and runs them."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy import select

from app.engine.nodes import _estimate_cost, create_agent_node
from app.engine.state import WorkflowState
from app.engine.tools import get_tools_by_names
from app.models.execution import ExecutionLog, WorkflowExecution

logger = logging.getLogger(__name__)


class WorkflowRuntime:
    """Compiles visual workflow definitions into LangGraph StateGraphs and executes them."""

    def __init__(self, ws_manager, db_session_factory):
        """
        Parameters
        ----------
        ws_manager :
            ConnectionManager for pushing WebSocket events.
        db_session_factory :
            An ``async_sessionmaker`` that yields ``AsyncSession`` instances.
        """
        self.ws_manager = ws_manager
        self.db_session_factory = db_session_factory

    # ------------------------------------------------------------------
    # Compile
    # ------------------------------------------------------------------

    async def compile(
        self,
        workflow_dict: dict,
        agents_map: dict[str, dict],
        execution_id: str,
    ) -> CompiledStateGraph:
        """Compile a graph_definition JSON into a runnable CompiledStateGraph.

        Parameters
        ----------
        workflow_dict : dict
            The ``graph_definition`` from the Workflow model, containing
            ``nodes`` and ``edges`` arrays in React Flow format.
        agents_map : dict[str, dict]
            Mapping of agent_id -> agent config dict (with name, model, etc.)
        execution_id : str
            The execution id to attach to agent nodes for DB/WS context.
        """

        nodes_def: list[dict] = workflow_dict.get("nodes", [])
        edges_def: list[dict] = workflow_dict.get("edges", [])

        # Build the graph
        graph = StateGraph(WorkflowState)

        # Track which node ids exist and their types
        node_types: dict[str, str] = {}  # node_id -> type
        condition_options: dict[str, list[str]] = {}  # condition_node_id -> list of option labels
        start_node_id: str | None = None
        end_node_ids: set[str] = set()

        # ------------------------------------------------------------------
        # 1. Register nodes
        # ------------------------------------------------------------------
        for node_def in nodes_def:
            nid = node_def["id"]
            ntype = node_def.get("type", "agent")
            data = node_def.get("data", {})
            node_types[nid] = ntype

            if ntype == "start":
                start_node_id = nid

                async def _start_node(state: WorkflowState) -> WorkflowState:
                    """Pass-through start node."""
                    return state

                graph.add_node(nid, _start_node)

            elif ntype == "end":
                end_node_ids.add(nid)

                async def _end_node(state: WorkflowState) -> WorkflowState:
                    """Pass-through end node."""
                    return state

                graph.add_node(nid, _end_node)

            elif ntype == "agent":
                # Support both camelCase (from seed/frontend) and snake_case
                agent_id = data.get("agentId") or data.get("agent_id") or ""
                agent_config = agents_map.get(agent_id, {})

                if not agent_config:
                    # Fallback: create a minimal config from the node data
                    agent_config = {
                        "name": data.get("label", nid),
                        "model": "gpt-4o-mini",
                        "temperature": 0.7,
                        "max_tokens": 4096,
                        "system_prompt": "",
                        "guardrails": {},
                        "tools": [],
                    }

                # Resolve tools
                tool_names = agent_config.get("tools", [])
                resolved_tools = get_tools_by_names(tool_names) if tool_names else []

                agent_callable = create_agent_node(
                    agent_config=agent_config,
                    tools=resolved_tools,
                    ws_manager=self.ws_manager,
                    execution_id=execution_id,
                    db_session_factory=self.db_session_factory,
                    node_id=nid,
                )
                graph.add_node(nid, agent_callable)

            elif ntype == "condition":
                options = data.get("options", [])
                condition_label = data.get("condition", "")
                condition_options[nid] = options

                # We create the condition router function later when adding edges
                # But we still need to register a node that is a pass-through.
                async def _condition_passthrough(state: WorkflowState) -> WorkflowState:
                    """Pass-through for condition node (routing is handled on edges)."""
                    return state

                graph.add_node(nid, _condition_passthrough)

            else:
                # Unknown type: treat as pass-through
                async def _passthrough(state: WorkflowState) -> WorkflowState:
                    return state

                graph.add_node(nid, _passthrough)

        # ------------------------------------------------------------------
        # 2. Set entry point
        # ------------------------------------------------------------------
        if start_node_id:
            graph.set_entry_point(start_node_id)
        elif nodes_def:
            # Fallback: use the first node
            graph.set_entry_point(nodes_def[0]["id"])

        # ------------------------------------------------------------------
        # 3. Add edges
        # ------------------------------------------------------------------

        # Group edges by source to detect conditional fan-out
        edges_by_source: dict[str, list[dict]] = {}
        for edge in edges_def:
            src = edge["source"]
            edges_by_source.setdefault(src, []).append(edge)

        # Track which sources we've already handled (for condition nodes)
        handled_sources: set[str] = set()

        for source_id, source_edges in edges_by_source.items():
            source_type = node_types.get(source_id, "")

            # --- Condition node: use conditional edges -----------------------
            if source_type == "condition":
                handled_sources.add(source_id)
                options = condition_options.get(source_id, [])
                condition_data = {}
                for nd in nodes_def:
                    if nd["id"] == source_id:
                        condition_data = nd.get("data", {})
                        break
                condition_label = condition_data.get("condition", "classify")

                # Build mapping: option_label -> target_node_id
                # Templates may store the condition value in several places:
                #   edge.data.condition, edge.data.branch, or edge.label
                option_to_target: dict[str, str] = {}
                default_target: str | None = None
                for edge in source_edges:
                    edge_data = edge.get("data", {})
                    cond_value = (
                        edge_data.get("condition")
                        or edge.get("label")
                        or edge_data.get("branch")
                        or ""
                    )
                    target = edge["target"]
                    if cond_value:
                        option_to_target[cond_value] = target
                    else:
                        default_target = target

                # Build the router function using LLM-based classification
                router = _build_condition_router(
                    condition_label=condition_label,
                    options=list(option_to_target.keys()),
                    option_to_target=option_to_target,
                    default_target=default_target,
                    ws_manager=self.ws_manager,
                    execution_id=execution_id,
                    node_id=source_id,
                    db_session_factory=self.db_session_factory,
                )

                # Collect the full path mapping for add_conditional_edges
                path_map: dict[str, str] = dict(option_to_target)
                if default_target:
                    path_map["__default__"] = default_target

                graph.add_conditional_edges(source_id, router, path_map)

            # --- End nodes: connect to LangGraph END -------------------------
            elif source_type == "end":
                # An end node shouldn't have outgoing edges, but handle it gracefully
                pass

            # --- Normal edges -------------------------------------------------
            else:
                for edge in source_edges:
                    target = edge["target"]
                    target_type = node_types.get(target, "")
                    if target_type == "end":
                        # Connect to the end node, then the end node connects to END
                        graph.add_edge(source_id, target)
                    else:
                        graph.add_edge(source_id, target)

        # Connect all end nodes to LangGraph's END
        for end_id in end_node_ids:
            graph.add_edge(end_id, END)

        # ------------------------------------------------------------------
        # 4. Compile
        # ------------------------------------------------------------------
        compiled = graph.compile()
        return compiled

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    async def execute(
        self,
        execution_id: str,
        workflow_id: str,
        graph: CompiledStateGraph,
        input_data: dict,
    ) -> dict:
        """Run a compiled graph to completion.

        Parameters
        ----------
        execution_id : str
            The WorkflowExecution id.
        workflow_id : str
            The Workflow id (for logging).
        graph : CompiledStateGraph
            A compiled LangGraph state graph from :meth:`compile`.
        input_data : dict
            Must contain at least ``{"message": "..."}`` with the user input.
        """

        exec_id = execution_id
        user_message = (
            input_data.get("message")
            or input_data.get("query")
            or input_data.get("input")
            or str(input_data)
        )

        # ----- Update status to running ----------------------------------------
        async with self.db_session_factory() as db:
            result = await db.execute(
                select(WorkflowExecution).where(WorkflowExecution.id == exec_id)
            )
            execution = result.scalar_one_or_none()
            if execution:
                execution.status = "running"
                execution.started_at = datetime.now(timezone.utc)
                await db.commit()

        await self.ws_manager.broadcast_to_execution(
            execution_id,
            {
                "type": "execution_started",
                "execution_id": execution_id,
                "workflow_id": workflow_id,
            },
        )

        # ----- Build initial state ---------------------------------------------
        initial_state: WorkflowState = {
            "messages": [HumanMessage(content=user_message)],
            "current_input": user_message,
            "intermediate_results": {},
            "final_output": None,
            "metadata": {
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "workflow_id": workflow_id,
                "execution_id": execution_id,
            },
        }

        # ----- Stream through the graph ----------------------------------------
        final_state: dict[str, Any] = dict(initial_state)

        try:
            async for event in graph.astream(initial_state, stream_mode="updates"):
                # event is a dict { node_name: state_update }
                for node_name, state_update in event.items():
                    if not isinstance(state_update, dict):
                        continue

                    logger.info(
                        "Execution %s: node '%s' completed",
                        execution_id,
                        node_name,
                    )

                    # Update current node in DB
                    async with self.db_session_factory() as db:
                        result = await db.execute(
                            select(WorkflowExecution).where(
                                WorkflowExecution.id == exec_id
                            )
                        )
                        execution = result.scalar_one_or_none()
                        if execution:
                            execution.current_node = node_name
                            await db.commit()

                    # Emit step event
                    await self.ws_manager.broadcast_to_execution(
                        execution_id,
                        {
                            "type": "step_completed",
                            "execution_id": execution_id,
                            "node_id": node_name,
                        },
                    )

                    # Merge updates into our tracking copy
                    for key, value in state_update.items():
                        if key == "intermediate_results" and isinstance(value, dict):
                            final_state.setdefault("intermediate_results", {}).update(value)
                        elif key == "metadata" and isinstance(value, dict):
                            final_state["metadata"] = value
                        elif key == "messages" and isinstance(value, list):
                            final_state.setdefault("messages", []).extend(value)
                        else:
                            final_state[key] = value

        except Exception as exc:
            logger.error("Execution %s failed: %s", execution_id, exc, exc_info=True)

            # ----- Mark as failed -----------------------------------------------
            async with self.db_session_factory() as db:
                result = await db.execute(
                    select(WorkflowExecution).where(
                        WorkflowExecution.id == exec_id
                    )
                )
                execution = result.scalar_one_or_none()
                if execution:
                    meta = final_state.get("metadata", {})
                    execution.status = "failed"
                    execution.error = str(exc)
                    execution.completed_at = datetime.now(timezone.utc)
                    execution.total_tokens = meta.get("total_tokens", 0)
                    execution.prompt_tokens = meta.get("total_prompt_tokens", 0)
                    execution.completion_tokens = meta.get("total_completion_tokens", 0)
                    execution.estimated_cost_usd = meta.get("total_cost_usd", 0.0)

                db.add(
                    ExecutionLog(
                        execution_id=exec_id,
                        level="error",
                        message=f"Execution failed: {exc}",
                    )
                )
                await db.commit()

            await self.ws_manager.broadcast_to_execution(
                execution_id,
                {
                    "type": "execution_failed",
                    "execution_id": execution_id,
                    "error": str(exc),
                },
            )
            return final_state

        # ----- Mark as completed -----------------------------------------------
        meta = final_state.get("metadata", {})
        final_output = final_state.get("final_output", "")

        async with self.db_session_factory() as db:
            result = await db.execute(
                select(WorkflowExecution).where(WorkflowExecution.id == exec_id)
            )
            execution = result.scalar_one_or_none()
            if execution:
                execution.status = "completed"
                execution.completed_at = datetime.now(timezone.utc)
                execution.output_data = {
                    "final_output": final_output,
                    "intermediate_results": final_state.get("intermediate_results", {}),
                }
                execution.total_tokens = meta.get("total_tokens", 0)
                execution.prompt_tokens = meta.get("total_prompt_tokens", 0)
                execution.completion_tokens = meta.get("total_completion_tokens", 0)
                execution.estimated_cost_usd = meta.get("total_cost_usd", 0.0)

            db.add(
                ExecutionLog(
                    execution_id=exec_id,
                    level="info",
                    message=(
                        f"Execution completed. "
                        f"Tokens: {meta.get('total_tokens', 0)}, "
                        f"Cost: ${meta.get('total_cost_usd', 0.0):.4f}"
                    ),
                    metadata_=meta,
                )
            )
            await db.commit()

        await self.ws_manager.broadcast_to_execution(
            execution_id,
            {
                "type": "execution_completed",
                "execution_id": execution_id,
                "final_output": final_output,
                "total_tokens": meta.get("total_tokens", 0),
                "total_cost_usd": meta.get("total_cost_usd", 0.0),
            },
        )

        await self.ws_manager.broadcast_to_dashboard(
            {
                "type": "execution_update",
                "execution_id": execution_id,
                "status": "completed",
                "total_tokens": meta.get("total_tokens", 0),
                "total_cost_usd": meta.get("total_cost_usd", 0.0),
            }
        )

        return final_state


# ======================================================================
# Condition router builder (module-level helper)
# ======================================================================


def _build_condition_router(
    condition_label: str,
    options: list[str],
    option_to_target: dict[str, str],
    default_target: str | None,
    ws_manager,
    execution_id: str,
    node_id: str,
    db_session_factory,
):
    """Return an async function that uses an LLM to classify the last message
    into one of the given options, returning the chosen option string as a
    routing key for ``add_conditional_edges``."""

    async def router(state: WorkflowState) -> str:
        # Get the last AI message content to classify
        last_content = ""
        for msg in reversed(state.get("messages", [])):
            if isinstance(msg, (AIMessage, HumanMessage)):
                last_content = msg.content
                break

        if not last_content:
            last_content = state.get("current_input", "")

        options_str = ", ".join(f'"{o}"' for o in options)
        classification_prompt = (
            f"You are a classifier. Based on the following content, choose exactly one "
            f"of these options: [{options_str}].\n\n"
            f"Condition to evaluate: {condition_label}\n\n"
            f"Content to classify:\n{last_content}\n\n"
            f"Respond with ONLY the chosen option, nothing else. "
            f"Your response must be exactly one of: {options_str}"
        )

        try:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=50)
            response = await llm.ainvoke([
                SystemMessage(content="You are a precise classifier. Respond with only the exact option text."),
                HumanMessage(content=classification_prompt),
            ])

            chosen = response.content.strip().strip('"').strip("'").lower()

            # Track token usage for the classification call
            usage = getattr(response, "usage_metadata", None) or {}
            class_prompt_tokens = usage.get("input_tokens", 0)
            class_completion_tokens = usage.get("output_tokens", 0)

            # Update metadata with classification cost
            meta = state.get("metadata", {})
            cost = _estimate_cost("gpt-4o-mini", class_prompt_tokens, class_completion_tokens)
            meta["total_prompt_tokens"] = meta.get("total_prompt_tokens", 0) + class_prompt_tokens
            meta["total_completion_tokens"] = meta.get("total_completion_tokens", 0) + class_completion_tokens
            meta["total_tokens"] = meta.get("total_tokens", 0) + class_prompt_tokens + class_completion_tokens
            meta["total_cost_usd"] = meta.get("total_cost_usd", 0.0) + cost

            # Match against options (case-insensitive)
            for opt in options:
                if opt.lower() == chosen or chosen in opt.lower():
                    logger.info(
                        "Condition %s (%s): classified as '%s'",
                        node_id,
                        condition_label,
                        opt,
                    )
                    await ws_manager.broadcast_to_execution(
                        execution_id,
                        {
                            "type": "condition_evaluated",
                            "node_id": node_id,
                            "condition": condition_label,
                            "result": opt,
                        },
                    )

                    # Persist log
                    async with db_session_factory() as db:
                        db.add(
                            ExecutionLog(
                                execution_id=execution_id,
                                level="info",
                                node_id=node_id,
                                message=f"Condition '{condition_label}' evaluated to '{opt}'",
                                metadata_={
                                    "condition": condition_label,
                                    "result": opt,
                                    "prompt_tokens": class_prompt_tokens,
                                    "completion_tokens": class_completion_tokens,
                                },
                            )
                        )
                        await db.commit()

                    return opt

            # If no exact match, try partial matching
            for opt in options:
                if opt.lower() in chosen or chosen in opt.lower():
                    logger.warning(
                        "Condition %s: partial match '%s' -> '%s'",
                        node_id,
                        chosen,
                        opt,
                    )
                    return opt

            # Fallback to default or first option
            logger.warning(
                "Condition %s: no match for '%s', using default",
                node_id,
                chosen,
            )
            if default_target:
                return "__default__"
            return options[0] if options else "__default__"

        except Exception as exc:
            logger.error("Condition router error for %s: %s", node_id, exc)
            await ws_manager.broadcast_to_execution(
                execution_id,
                {
                    "type": "condition_error",
                    "node_id": node_id,
                    "error": str(exc),
                },
            )
            # Fallback: return first option or default
            if default_target:
                return "__default__"
            return options[0] if options else "__default__"

    return router

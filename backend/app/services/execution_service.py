import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent import Agent
from app.models.execution import ExecutionLog, WorkflowExecution
from app.models.message import AgentMessage
from app.models.workflow import Workflow
from app.schemas.execution import ExecutionCreate


class ExecutionService:

    @staticmethod
    async def get_all(db: AsyncSession, limit: int = 50, offset: int = 0) -> list[WorkflowExecution]:
        result = await db.execute(
            select(WorkflowExecution)
            .order_by(WorkflowExecution.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, execution_id: str) -> WorkflowExecution | None:
        result = await db.execute(
            select(WorkflowExecution)
            .options(
                selectinload(WorkflowExecution.logs),
                selectinload(WorkflowExecution.messages),
            )
            .where(WorkflowExecution.id == execution_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def start(db: AsyncSession, data: ExecutionCreate) -> tuple[WorkflowExecution | None, Workflow | None]:
        """Create a WorkflowExecution record and return it along with the Workflow.

        Returns (None, None) when the workflow does not exist.
        The caller is responsible for launching the actual engine execution
        as a background task.
        """
        # Fetch the workflow
        workflow_result = await db.execute(
            select(Workflow).where(Workflow.id == data.workflow_id)
        )
        workflow = workflow_result.scalar_one_or_none()
        if workflow is None:
            return None, None

        execution = WorkflowExecution(
            workflow_id=data.workflow_id,
            status="pending",
            input_data=data.input_data,
        )
        db.add(execution)
        await db.flush()

        # Add initial log entry
        log = ExecutionLog(
            execution_id=execution.id,
            level="info",
            message=f"Execution created for workflow '{workflow.name}'",
            metadata_={
                "workflow_id": str(workflow.id),
                "input_data": data.input_data,
            },
        )
        db.add(log)
        await db.flush()
        await db.refresh(execution)

        return execution, workflow

    @staticmethod
    async def fetch_agents_for_workflow(
        db: AsyncSession, graph_definition: dict
    ) -> dict[str, dict]:
        """Extract agent IDs from the graph nodes and fetch the corresponding
        Agent records from the database.

        Returns a dict mapping agent_id (str) -> agent config dict suitable for
        the WorkflowRuntime.compile() ``agents_map`` parameter.

        Agent nodes may reference agents by:
          - ``data.agentId`` (camelCase, set by the seed / frontend)
          - ``data.agent_id`` (snake_case)

        Additionally, if no explicit agent_id is present, the method attempts
        to match by ``data.agentName`` against Agent.name.
        """
        nodes = graph_definition.get("nodes", [])

        # Collect all agent IDs referenced in nodes
        agent_ids: set[str] = set()
        name_lookup_nodes: list[dict] = []  # nodes that need name-based lookup

        for node in nodes:
            if node.get("type") != "agent":
                continue
            data = node.get("data", {})
            # Try camelCase first (from seed), then snake_case
            aid = data.get("agentId") or data.get("agent_id") or ""
            if aid:
                # Validate it looks like a UUID, otherwise fall back to name lookup
                try:
                    uuid.UUID(str(aid))
                    agent_ids.add(str(aid))
                except (ValueError, AttributeError):
                    name_lookup_nodes.append(node)
            else:
                name_lookup_nodes.append(node)

        agents_map: dict[str, dict] = {}

        # Batch-fetch agents by ID
        if agent_ids:
            result = await db.execute(
                select(Agent).where(Agent.id.in_(agent_ids))
            )
            for agent in result.scalars().all():
                agents_map[str(agent.id)] = _agent_to_config(agent)

        # Name-based fallback lookup
        if name_lookup_nodes:
            agent_names = set()
            for node in name_lookup_nodes:
                data = node.get("data", {})
                name = data.get("agentName") or data.get("label") or ""
                if name:
                    agent_names.add(name)

            if agent_names:
                result = await db.execute(
                    select(Agent).where(Agent.name.in_(agent_names))
                )
                name_to_agent: dict[str, Agent] = {}
                for agent in result.scalars().all():
                    name_to_agent[agent.name] = agent

                # Map these agents and update the node data with agentId
                # so runtime.compile can find them
                for node in name_lookup_nodes:
                    data = node.get("data", {})
                    name = data.get("agentName") or data.get("label") or ""
                    if name in name_to_agent:
                        agent = name_to_agent[name]
                        agent_id_str = str(agent.id)
                        data["agentId"] = agent_id_str
                        if agent_id_str not in agents_map:
                            agents_map[agent_id_str] = _agent_to_config(agent)

        return agents_map

    @staticmethod
    async def cancel(db: AsyncSession, execution_id: str) -> WorkflowExecution | None:
        execution = await ExecutionService.get_by_id(db, execution_id)
        if execution is None:
            return None

        if execution.status in ("completed", "failed", "cancelled"):
            return execution

        execution.status = "cancelled"
        execution.completed_at = datetime.now(timezone.utc)

        log = ExecutionLog(
            execution_id=execution.id,
            level="warning",
            message="Execution cancelled by user",
        )
        db.add(log)
        await db.flush()
        await db.refresh(execution)

        return execution

    @staticmethod
    async def get_messages(db: AsyncSession, execution_id: str) -> list[AgentMessage]:
        result = await db.execute(
            select(AgentMessage)
            .where(AgentMessage.execution_id == execution_id)
            .order_by(AgentMessage.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_logs(db: AsyncSession, execution_id: str) -> list[ExecutionLog]:
        result = await db.execute(
            select(ExecutionLog)
            .where(ExecutionLog.execution_id == execution_id)
            .order_by(ExecutionLog.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_status(
        db: AsyncSession,
        execution_id: str,
        status: str,
        output_data: dict | None = None,
        error: str | None = None,
        current_node: str | None = None,
        total_tokens: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> WorkflowExecution | None:
        result = await db.execute(
            select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        )
        execution = result.scalar_one_or_none()
        if execution is None:
            return None

        execution.status = status
        if output_data is not None:
            execution.output_data = output_data
        if error is not None:
            execution.error = error
        if current_node is not None:
            execution.current_node = current_node

        execution.total_tokens = total_tokens
        execution.prompt_tokens = prompt_tokens
        execution.completion_tokens = completion_tokens
        execution.estimated_cost_usd = estimated_cost_usd

        if status in ("completed", "failed"):
            execution.completed_at = datetime.now(timezone.utc)

        await db.flush()
        await db.refresh(execution)
        return execution

    @staticmethod
    async def add_log(
        db: AsyncSession,
        execution_id: str,
        level: str,
        message: str,
        node_id: str | None = None,
        agent_name: str | None = None,
        metadata: dict | None = None,
    ) -> ExecutionLog:
        log = ExecutionLog(
            execution_id=execution_id,
            level=level,
            node_id=node_id,
            agent_name=agent_name,
            message=message,
            metadata_=metadata or {},
        )
        db.add(log)
        await db.flush()
        await db.refresh(log)
        return log


def _agent_to_config(agent: Agent) -> dict:
    """Convert an Agent ORM model to the config dict expected by the runtime."""
    return {
        "name": agent.name,
        "role": agent.role,
        "model": agent.model,
        "temperature": agent.temperature,
        "max_tokens": agent.max_tokens,
        "system_prompt": agent.system_prompt,
        "guardrails": agent.guardrails or {},
        "tools": agent.tools or [],
    }

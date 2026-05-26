import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
    async def get_by_id(db: AsyncSession, execution_id: uuid.UUID) -> WorkflowExecution | None:
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
    async def start(db: AsyncSession, data: ExecutionCreate) -> WorkflowExecution | None:
        # Verify workflow exists
        workflow_result = await db.execute(
            select(Workflow).where(Workflow.id == data.workflow_id)
        )
        workflow = workflow_result.scalar_one_or_none()
        if workflow is None:
            return None

        execution = WorkflowExecution(
            workflow_id=data.workflow_id,
            status="running",
            input_data=data.input_data,
            started_at=datetime.now(timezone.utc),
        )
        db.add(execution)
        await db.flush()

        # Add initial log entry
        log = ExecutionLog(
            execution_id=execution.id,
            level="info",
            message=f"Execution started for workflow '{workflow.name}'",
            metadata_={
                "workflow_id": str(workflow.id),
                "input_data": data.input_data,
            },
        )
        db.add(log)
        await db.flush()
        await db.refresh(execution)

        return execution

    @staticmethod
    async def cancel(db: AsyncSession, execution_id: uuid.UUID) -> WorkflowExecution | None:
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
    async def get_messages(db: AsyncSession, execution_id: uuid.UUID) -> list[AgentMessage]:
        result = await db.execute(
            select(AgentMessage)
            .where(AgentMessage.execution_id == execution_id)
            .order_by(AgentMessage.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_logs(db: AsyncSession, execution_id: uuid.UUID) -> list[ExecutionLog]:
        result = await db.execute(
            select(ExecutionLog)
            .where(ExecutionLog.execution_id == execution_id)
            .order_by(ExecutionLog.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_status(
        db: AsyncSession,
        execution_id: uuid.UUID,
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
        execution_id: uuid.UUID,
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

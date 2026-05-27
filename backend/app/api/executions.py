import asyncio
import copy
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory, get_db
from app.schemas.execution import ExecutionCreate, ExecutionLogResponse, ExecutionResponse
from app.schemas.message import MessageResponse
from app.services.execution_service import ExecutionService

logger = logging.getLogger(__name__)

router = APIRouter()


async def _run_execution(
    runtime,
    execution_id: str,
    workflow_id: str,
    graph_definition: dict,
    agents_map: dict[str, dict],
    input_data: dict,
    ws_manager,
):
    """Background coroutine that compiles the graph and runs the execution.

    This runs outside the request lifecycle, so it creates its own DB sessions
    via the runtime's db_session_factory.
    """
    try:
        # Notify dashboard that execution is starting
        await ws_manager.broadcast_to_dashboard({
            "type": "execution_update",
            "execution_id": execution_id,
            "status": "running",
        })

        # Compile the workflow graph into a runnable LangGraph
        compiled_graph = await runtime.compile(
            workflow_dict=graph_definition,
            agents_map=agents_map,
            execution_id=execution_id,
        )

        # Execute the graph (handles DB updates, WS events, etc.)
        await runtime.execute(
            execution_id=execution_id,
            workflow_id=workflow_id,
            graph=compiled_graph,
            input_data=input_data,
        )

    except Exception as exc:
        logger.error(
            "Background execution %s failed: %s", execution_id, exc, exc_info=True
        )

        # Mark as failed in DB
        try:
            async with async_session_factory() as db:
                await ExecutionService.update_status(
                    db,
                    execution_id,
                    status="failed",
                    error=str(exc),
                )
                await db.commit()
        except Exception:
            logger.exception("Failed to update execution status after error.")

        # Notify via WebSocket
        try:
            await ws_manager.broadcast_to_execution(execution_id, {
                "type": "execution_failed",
                "execution_id": execution_id,
                "error": str(exc),
            })
            await ws_manager.broadcast_to_dashboard({
                "type": "execution_update",
                "execution_id": execution_id,
                "status": "failed",
                "error": str(exc),
            })
        except Exception:
            logger.exception("Failed to send failure notification via WebSocket.")


@router.post("/", response_model=ExecutionResponse, status_code=201)
async def start_execution(
    data: ExecutionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow execution and launch it as a background task.

    The endpoint returns immediately with the execution record (status=pending).
    The frontend can connect to /ws/executions/{execution_id} to stream
    real-time events as the engine processes the graph.
    """
    # 1. Create the execution record and fetch the workflow
    result = await ExecutionService.start(db, data)
    execution, workflow = result
    if execution is None or workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # 2. Fetch all agents referenced in the workflow graph from DB
    graph_definition = copy.deepcopy(workflow.graph_definition)
    agents_map = await ExecutionService.fetch_agents_for_workflow(db, graph_definition)

    # Commit the pending execution record so it is visible to the background task
    # (the get_db dependency will commit on success, but we need to ensure
    # the data is flushed before launching the background task)
    await db.commit()

    # 3. Get the runtime and ws_manager from app.state
    runtime = request.app.state.workflow_runtime
    ws_manager = request.app.state.ws_manager

    execution_id_str = str(execution.id)
    workflow_id_str = str(workflow.id)

    # 4. Launch the execution as a background asyncio task
    asyncio.create_task(
        _run_execution(
            runtime=runtime,
            execution_id=execution_id_str,
            workflow_id=workflow_id_str,
            graph_definition=graph_definition,
            agents_map=agents_map,
            input_data=data.input_data,
            ws_manager=ws_manager,
        ),
        name=f"execution-{execution_id_str}",
    )

    logger.info(
        "Execution %s launched for workflow %s (%s)",
        execution_id_str,
        workflow.name,
        workflow_id_str,
    )

    # 5. Return the execution record immediately
    return execution


@router.get("/", response_model=list[ExecutionResponse])
async def list_executions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    executions = await ExecutionService.get_all(db, limit=limit, offset=offset)
    return executions


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: str, db: AsyncSession = Depends(get_db)):
    execution = await ExecutionService.get_by_id(db, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.post("/{execution_id}/cancel", response_model=ExecutionResponse)
async def cancel_execution(
    execution_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    execution = await ExecutionService.cancel(db, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")

    # Notify WebSocket clients about the cancellation
    ws_manager = request.app.state.ws_manager
    exec_id_str = str(execution_id)
    await ws_manager.broadcast_to_execution(exec_id_str, {
        "type": "execution_cancelled",
        "execution_id": exec_id_str,
    })
    await ws_manager.broadcast_to_dashboard({
        "type": "execution_update",
        "execution_id": exec_id_str,
        "status": "cancelled",
    })

    return execution


@router.get("/{execution_id}/messages", response_model=list[MessageResponse])
async def get_execution_messages(
    execution_id: str, db: AsyncSession = Depends(get_db)
):
    # Verify execution exists
    execution = await ExecutionService.get_by_id(db, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")

    messages = await ExecutionService.get_messages(db, execution_id)
    return messages


@router.get("/{execution_id}/logs", response_model=list[ExecutionLogResponse])
async def get_execution_logs(
    execution_id: str, db: AsyncSession = Depends(get_db)
):
    execution = await ExecutionService.get_by_id(db, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")

    logs = await ExecutionService.get_logs(db, execution_id)
    return logs

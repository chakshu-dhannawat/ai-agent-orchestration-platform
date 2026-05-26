import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.execution import ExecutionCreate, ExecutionLogResponse, ExecutionResponse
from app.schemas.message import MessageResponse
from app.services.execution_service import ExecutionService

router = APIRouter()


@router.post("/", response_model=ExecutionResponse, status_code=201)
async def start_execution(data: ExecutionCreate, db: AsyncSession = Depends(get_db)):
    execution = await ExecutionService.start(db, data)
    if execution is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
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
async def get_execution(execution_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    execution = await ExecutionService.get_by_id(db, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.post("/{execution_id}/cancel", response_model=ExecutionResponse)
async def cancel_execution(execution_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    execution = await ExecutionService.cancel(db, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.get("/{execution_id}/messages", response_model=list[MessageResponse])
async def get_execution_messages(
    execution_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    # Verify execution exists
    execution = await ExecutionService.get_by_id(db, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")

    messages = await ExecutionService.get_messages(db, execution_id)
    return messages


@router.get("/{execution_id}/logs", response_model=list[ExecutionLogResponse])
async def get_execution_logs(
    execution_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    execution = await ExecutionService.get_by_id(db, execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")

    logs = await ExecutionService.get_logs(db, execution_id)
    return logs

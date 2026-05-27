from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.workflow import WorkflowCreate, WorkflowResponse, WorkflowUpdate
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.get("/", response_model=list[WorkflowResponse])
async def list_workflows(db: AsyncSession = Depends(get_db)):
    workflows = await WorkflowService.get_all(db, include_templates=False)
    return workflows


@router.post("/", response_model=WorkflowResponse, status_code=201)
async def create_workflow(data: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    workflow = await WorkflowService.create(db, data)
    return workflow


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    workflow = await WorkflowService.get_by_id(db, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
):
    workflow = await WorkflowService.update(db, workflow_id, data)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await WorkflowService.delete(db, workflow_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.post("/{workflow_id}/validate")
async def validate_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    workflow = await WorkflowService.get_by_id(db, workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    result = WorkflowService.validate_graph(workflow.graph_definition)
    return result

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.workflow import WorkflowResponse
from app.services.workflow_service import WorkflowService

router = APIRouter()


class InstantiateRequest(BaseModel):
    name: str | None = None


@router.get("/", response_model=list[WorkflowResponse])
async def list_templates(db: AsyncSession = Depends(get_db)):
    templates = await WorkflowService.get_templates(db)
    return templates


@router.post("/{template_id}/instantiate", response_model=WorkflowResponse, status_code=201)
async def instantiate_template(
    template_id: uuid.UUID,
    body: InstantiateRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    name = body.name if body else None
    workflow = await WorkflowService.instantiate_template(db, template_id, name=name)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail="Template not found or the specified workflow is not a template",
        )
    return workflow

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.workflow import WorkflowResponse
from app.services.workflow_service import WorkflowService
from app.templates import TEMPLATES, get_template_by_id

router = APIRouter()


class InstantiateRequest(BaseModel):
    name: str | None = None


class TemplateInfo(BaseModel):
    """Lightweight template descriptor returned by the catalog endpoint."""

    id: str
    name: str
    description: str
    agent_count: int
    node_count: int
    edge_count: int
    agents: list[dict]
    graph_definition: dict


@router.get("/catalog", response_model=list[TemplateInfo])
async def list_template_catalog():
    """Return the built-in template catalog (static data, no DB required)."""
    result = []
    for t in TEMPLATES:
        result.append(
            TemplateInfo(
                id=t["id"],
                name=t["name"],
                description=t["description"],
                agent_count=len(t["agents"]),
                node_count=len(t["graph_definition"].get("nodes", [])),
                edge_count=len(t["graph_definition"].get("edges", [])),
                agents=t["agents"],
                graph_definition=t["graph_definition"],
            )
        )
    return result


@router.get("/catalog/{template_id}", response_model=TemplateInfo)
async def get_template_detail(template_id: str):
    """Return details for a specific built-in template."""
    t = get_template_by_id(template_id)
    if t is None:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")
    return TemplateInfo(
        id=t["id"],
        name=t["name"],
        description=t["description"],
        agent_count=len(t["agents"]),
        node_count=len(t["graph_definition"].get("nodes", [])),
        edge_count=len(t["graph_definition"].get("edges", [])),
        agents=t["agents"],
        graph_definition=t["graph_definition"],
    )


@router.get("/", response_model=list[WorkflowResponse])
async def list_templates(db: AsyncSession = Depends(get_db)):
    """Return all workflow templates stored in the database."""
    templates = await WorkflowService.get_templates(db)
    return templates


@router.post("/{template_id}/instantiate", response_model=WorkflowResponse, status_code=201)
async def instantiate_template(
    template_id: uuid.UUID,
    body: InstantiateRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow instance from a database template."""
    name = body.name if body else None
    workflow = await WorkflowService.instantiate_template(db, template_id, name=name)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail="Template not found or the specified workflow is not a template",
        )
    return workflow

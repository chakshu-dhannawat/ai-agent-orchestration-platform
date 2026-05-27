import copy
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import Agent
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowResponse
from app.services.workflow_service import WorkflowService
from app.templates import TEMPLATES, get_template_by_id

logger = logging.getLogger(__name__)

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


@router.post(
    "/catalog/{template_id}/instantiate",
    response_model=WorkflowResponse,
    status_code=201,
)
async def instantiate_catalog_template(
    template_id: str,
    body: InstantiateRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow + agents from a built-in catalog template.

    This is the handler for "Use Template" in the UI.  It:
      1. Looks up the template from the in-memory catalog.
      2. Creates Agent DB records for every agent in the template.
      3. Enriches the graph definition with the new agent IDs.
      4. Creates a Workflow DB record with the enriched graph.
    """
    template = get_template_by_id(template_id)
    if template is None:
        raise HTTPException(
            status_code=404,
            detail=f"Catalog template '{template_id}' not found",
        )

    # Create agent records and collect role -> agent_id mapping
    agent_ids: dict[str, str] = {}
    for agent_data in template["agents"]:
        agent = Agent(**agent_data)
        db.add(agent)
        await db.flush()
        await db.refresh(agent)
        agent_ids[agent_data["role"]] = agent.id
        logger.info(
            "Created agent '%s' (id=%s) from catalog template '%s'",
            agent.name,
            agent.id,
            template_id,
        )

    # Enrich the graph definition with actual agent IDs
    graph = _enrich_graph_with_agent_ids(template["graph_definition"], agent_ids)

    # Create the workflow
    name = (body.name if body and body.name else None) or f"{template['name']} (Instance)"
    workflow = Workflow(
        name=name,
        description=template["description"],
        is_template=False,
        graph_definition=graph,
    )
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)

    logger.info(
        "Created workflow '%s' (id=%s) from catalog template '%s'",
        workflow.name,
        workflow.id,
        template_id,
    )

    return workflow


@router.get("/", response_model=list[WorkflowResponse])
async def list_templates(db: AsyncSession = Depends(get_db)):
    """Return all workflow templates stored in the database."""
    templates = await WorkflowService.get_templates(db)
    return templates


@router.post("/{template_id}/instantiate", response_model=WorkflowResponse, status_code=201)
async def instantiate_template(
    template_id: str,
    body: InstantiateRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow instance from a database template.

    This copies the workflow (and creates agents if the template graph
    references agents that exist in the DB).
    """
    name = body.name if body else None
    workflow = await WorkflowService.instantiate_template(db, template_id, name=name)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail="Template not found or the specified workflow is not a template",
        )
    return workflow


def _enrich_graph_with_agent_ids(
    graph_def: dict, agent_ids: dict[str, str]
) -> dict:
    """Return a copy of graph_def with agent UUIDs injected into node data."""
    graph = copy.deepcopy(graph_def)
    for node in graph.get("nodes", []):
        role = node.get("data", {}).get("role")
        if role and role in agent_ids:
            node["data"]["agentId"] = str(agent_ids[role])
    return graph

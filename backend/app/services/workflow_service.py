from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate


class WorkflowService:

    @staticmethod
    async def get_all(db: AsyncSession, include_templates: bool = True) -> list[Workflow]:
        query = select(Workflow).order_by(Workflow.created_at.desc())
        if not include_templates:
            query = query.where(Workflow.is_template == False)  # noqa: E712
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_templates(db: AsyncSession) -> list[Workflow]:
        result = await db.execute(
            select(Workflow)
            .where(Workflow.is_template == True)  # noqa: E712
            .order_by(Workflow.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, workflow_id: str) -> Workflow | None:
        result = await db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: WorkflowCreate) -> Workflow:
        workflow = Workflow(**data.model_dump())
        db.add(workflow)
        await db.flush()
        await db.refresh(workflow)
        return workflow

    @staticmethod
    async def update(
        db: AsyncSession, workflow_id: str, data: WorkflowUpdate
    ) -> Workflow | None:
        workflow = await WorkflowService.get_by_id(db, workflow_id)
        if workflow is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workflow, field, value)

        await db.flush()
        await db.refresh(workflow)
        return workflow

    @staticmethod
    async def delete(db: AsyncSession, workflow_id: str) -> bool:
        workflow = await WorkflowService.get_by_id(db, workflow_id)
        if workflow is None:
            return False

        await db.delete(workflow)
        await db.flush()
        return True

    @staticmethod
    def validate_graph(graph_definition: dict) -> dict:
        """Validate a workflow graph definition and return validation results."""
        errors: list[str] = []
        warnings: list[str] = []

        if not graph_definition:
            errors.append("Graph definition is empty")
            return {"valid": False, "errors": errors, "warnings": warnings}

        nodes = graph_definition.get("nodes", [])
        edges = graph_definition.get("edges", [])

        if not nodes:
            errors.append("Graph must contain at least one node")

        node_ids = {node.get("id") for node in nodes if isinstance(node, dict)}

        for node in nodes:
            if not isinstance(node, dict):
                errors.append(f"Invalid node format: {node}")
                continue
            if not node.get("id"):
                errors.append("All nodes must have an 'id' field")
            if not node.get("type"):
                warnings.append(f"Node '{node.get('id', 'unknown')}' has no type specified")

        for edge in edges:
            if not isinstance(edge, dict):
                errors.append(f"Invalid edge format: {edge}")
                continue
            source = edge.get("source")
            target = edge.get("target")
            if source and source not in node_ids:
                errors.append(f"Edge source '{source}' references unknown node")
            if target and target not in node_ids:
                errors.append(f"Edge target '{target}' references unknown node")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    @staticmethod
    async def instantiate_template(
        db: AsyncSession, template_id: str, name: str | None = None
    ) -> Workflow | None:
        template = await WorkflowService.get_by_id(db, template_id)
        if template is None or not template.is_template:
            return None

        workflow = Workflow(
            name=name or f"{template.name} (Copy)",
            description=template.description,
            is_template=False,
            template_id=template.id,
            graph_definition=template.graph_definition,
        )
        db.add(workflow)
        await db.flush()
        await db.refresh(workflow)
        return workflow

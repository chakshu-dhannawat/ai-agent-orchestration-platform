"""
Seed script for the AI Agent Orchestration Platform.

Creates pre-built workflow templates and sample data in the database.
Idempotent: checks for existing records before inserting.

Usage:
    python -m app.seed
"""

import asyncio
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, async_session_factory, engine
from app.models.agent import Agent
from app.models.channel import Channel
from app.models.workflow import Workflow
from app.templates import TEMPLATES

logger = logging.getLogger(__name__)


async def _seed_template(db: AsyncSession, template: dict) -> bool:
    """Seed a single workflow template and its agents.

    Returns True if the template was created, False if it already existed.
    """
    template_id = template["id"]

    # Check if a workflow with this template_id marker already exists.
    # We store the template string id inside the workflow's description metadata
    # and use is_template=True + name match for idempotency.
    existing = await db.execute(
        select(Workflow).where(
            Workflow.is_template == True,  # noqa: E712
            Workflow.name == template["name"],
        )
    )
    if existing.scalar_one_or_none() is not None:
        logger.info("Template '%s' already exists, skipping.", template["name"])
        return False

    # Create agent records and build a mapping of role -> agent_id for the graph
    agent_ids: dict[str, uuid.UUID] = {}
    for agent_data in template["agents"]:
        agent = Agent(**agent_data)
        db.add(agent)
        await db.flush()
        await db.refresh(agent)
        agent_ids[agent_data["role"]] = agent.id
        logger.info("  Created agent: %s (id=%s)", agent.name, agent.id)

    # Enrich the graph definition with actual agent IDs so the frontend
    # can link nodes to agent records.
    graph = _enrich_graph_with_agent_ids(template["graph_definition"], agent_ids)

    # Create the workflow template
    workflow = Workflow(
        name=template["name"],
        description=template["description"],
        is_template=True,
        graph_definition=graph,
    )
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)
    logger.info(
        "  Created template workflow: %s (id=%s)", workflow.name, workflow.id
    )

    return True


def _enrich_graph_with_agent_ids(
    graph_def: dict, agent_ids: dict[str, uuid.UUID]
) -> dict:
    """Return a copy of graph_def with agent UUIDs injected into node data."""
    import copy

    graph = copy.deepcopy(graph_def)
    for node in graph.get("nodes", []):
        role = node.get("data", {}).get("role")
        if role and role in agent_ids:
            node["data"]["agentId"] = str(agent_ids[role])
    return graph


async def _seed_sample_channel(db: AsyncSession) -> bool:
    """Create a sample Telegram channel entry (inactive by default).

    Returns True if created, False if it already existed.
    """
    existing = await db.execute(
        select(Channel).where(
            Channel.type == "telegram",
            Channel.name == "Sample Telegram Channel",
        )
    )
    if existing.scalar_one_or_none() is not None:
        logger.info("Sample Telegram channel already exists, skipping.")
        return False

    channel = Channel(
        type="telegram",
        name="Sample Telegram Channel",
        config={
            "chat_id": "",
            "description": "A sample Telegram channel for demonstration purposes. "
            "Configure with a real chat_id to activate.",
        },
        is_active=False,
    )
    db.add(channel)
    await db.flush()
    await db.refresh(channel)
    logger.info("Created sample Telegram channel (id=%s, inactive)", channel.id)
    return True


async def run_seed() -> None:
    """Run the full seed process."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        try:
            created_count = 0

            logger.info("Seeding workflow templates...")
            for template in TEMPLATES:
                logger.info("Processing template: %s", template["name"])
                created = await _seed_template(db, template)
                if created:
                    created_count += 1

            logger.info("Seeding sample channels...")
            channel_created = await _seed_sample_channel(db)

            await db.commit()

            # Summary
            print()
            print("=" * 50)
            print("Seed completed successfully!")
            print(f"  Templates created: {created_count}/{len(TEMPLATES)}")
            print(f"  Sample channel created: {'Yes' if channel_created else 'Already existed'}")
            print("=" * 50)

        except Exception:
            await db.rollback()
            logger.exception("Seed failed, rolling back.")
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())

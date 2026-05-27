from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentService:

    @staticmethod
    async def get_all(db: AsyncSession) -> list[Agent]:
        result = await db.execute(
            select(Agent).order_by(Agent.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, agent_id: str) -> Agent | None:
        result = await db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: AgentCreate) -> Agent:
        agent = Agent(**data.model_dump())
        db.add(agent)
        await db.flush()
        await db.refresh(agent)
        return agent

    @staticmethod
    async def update(
        db: AsyncSession, agent_id: str, data: AgentUpdate
    ) -> Agent | None:
        agent = await AgentService.get_by_id(db, agent_id)
        if agent is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)

        await db.flush()
        await db.refresh(agent)
        return agent

    @staticmethod
    async def delete(db: AsyncSession, agent_id: str) -> bool:
        agent = await AgentService.get_by_id(db, agent_id)
        if agent is None:
            return False

        await db.delete(agent)
        await db.flush()
        return True

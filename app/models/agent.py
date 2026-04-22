from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Agent
from app.schemas.agent import AgentCreate, AgentUpdate


async def generate_api_key() -> str:
    return f"agk_{uuid4().hex}"


async def create_agent(db: AsyncSession, data: AgentCreate, api_key: str) -> Agent:
    agent = Agent(
        id=str(uuid4()),
        name=data.name,
        api_key=api_key,
        description=data.description,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


async def get_agent(db: AsyncSession, agent_id: str) -> Agent | None:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    return result.scalar_one_or_none()


async def get_agent_by_api_key(db: AsyncSession, api_key: str) -> Agent | None:
    result = await db.execute(
        select(Agent).where(Agent.api_key == api_key, Agent.enabled == True)
    )
    return result.scalar_one_or_none()


async def list_agents(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> tuple[list[Agent], int]:
    result = await db.execute(select(Agent).offset(skip).limit(limit))
    agents = result.scalars().all()

    count_result = await db.execute(select(Agent))
    total = len(count_result.scalars().all())

    return list(agents), total


async def update_agent(
    db: AsyncSession, agent_id: str, data: AgentUpdate
) -> Agent | None:
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_agent(db, agent_id)

    update_data["updated_at"] = datetime.utcnow()
    await db.execute(update(Agent).where(Agent.id == agent_id).values(**update_data))
    await db.commit()
    return await get_agent(db, agent_id)


async def delete_agent(db: AsyncSession, agent_id: str) -> bool:
    agent = await get_agent(db, agent_id)
    if not agent:
        return False
    await db.delete(agent)
    await db.commit()
    return True

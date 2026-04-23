from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import LLMConfig
from app.schemas.llm_config import LLMConfigCreate, LLMConfigUpdate


async def create_llm_config(db: AsyncSession, data: LLMConfigCreate) -> LLMConfig:
    config = LLMConfig(
        id=str(uuid4()),
        name=data.name,
        provider=data.provider,
        api_key=data.api_key,
        model=data.model,
        base_url=data.base_url,
        enabled=True,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


async def get_llm_config(db: AsyncSession, config_id: str) -> LLMConfig | None:
    result = await db.execute(select(LLMConfig).where(LLMConfig.id == config_id))
    return result.scalar_one_or_none()


async def get_enabled_llm_config(db: AsyncSession) -> LLMConfig | None:
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.enabled == True).limit(1)
    )
    return result.scalar_one_or_none()


async def list_llm_configs(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> tuple[list[LLMConfig], int]:
    result = await db.execute(select(LLMConfig).offset(skip).limit(limit))
    configs = result.scalars().all()

    count_result = await db.execute(select(LLMConfig))
    total = len(count_result.scalars().all())

    return list(configs), total


async def update_llm_config(
    db: AsyncSession, config_id: str, data: LLMConfigUpdate
) -> LLMConfig | None:
    config = await get_llm_config(db, config_id)
    if not config:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return config

    update_data["updated_at"] = datetime.utcnow()
    await db.execute(
        update(LLMConfig).where(LLMConfig.id == config_id).values(**update_data)
    )
    await db.commit()
    return await get_llm_config(db, config_id)


async def delete_llm_config(db: AsyncSession, config_id: str) -> bool:
    config = await get_llm_config(db, config_id)
    if not config:
        return False
    await db.delete(config)
    await db.commit()
    return True

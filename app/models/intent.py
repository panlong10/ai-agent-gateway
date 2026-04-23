import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Intent
from app.schemas.intent import IntentCreate, IntentUpdate


async def create_intent(db: AsyncSession, data: IntentCreate) -> Intent:
    intent = Intent(
        id=str(uuid4()),
        name=data.name,
        description=data.description,
        pattern=data.pattern,
        service_id=data.service_id,
        params_mapping=data.params_mapping,
        enabled=True,
    )
    db.add(intent)
    await db.commit()
    await db.refresh(intent)
    return intent


async def get_intent(db: AsyncSession, intent_id: str) -> Intent | None:
    result = await db.execute(select(Intent).where(Intent.id == intent_id))
    return result.scalar_one_or_none()


async def get_intent_by_name(db: AsyncSession, name: str) -> Intent | None:
    result = await db.execute(
        select(Intent).where(Intent.name == name, Intent.enabled == True)
    )
    return result.scalar_one_or_none()


async def match_intent(db: AsyncSession, query: str) -> Intent | None:
    result = await db.execute(select(Intent).where(Intent.enabled == True))
    intents = result.scalars().all()

    for intent in intents:
        if intent.pattern and intent.pattern.lower() in query.lower():
            return intent

    return None


async def list_intents(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> tuple[list[Intent], int]:
    result = await db.execute(select(Intent).offset(skip).limit(limit))
    intents = result.scalars().all()

    count_result = await db.execute(select(Intent))
    total = len(count_result.scalars().all())

    return list(intents), total


async def update_intent(
    db: AsyncSession, intent_id: str, data: IntentUpdate
) -> Intent | None:
    intent = await get_intent(db, intent_id)
    if not intent:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return intent

    update_data["updated_at"] = datetime.utcnow()
    await db.execute(update(Intent).where(Intent.id == intent_id).values(**update_data))
    await db.commit()
    return await get_intent(db, intent_id)


async def delete_intent(db: AsyncSession, intent_id: str) -> bool:
    intent = await get_intent(db, intent_id)
    if not intent:
        return False
    await db.delete(intent)
    await db.commit()
    return True

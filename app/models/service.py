from datetime import datetime
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Service
from app.schemas.service import ServiceCreate, ServiceUpdate


async def create_service(db: AsyncSession, data: ServiceCreate) -> Service:
    service = Service(
        id=str(uuid4()),
        name=data.name,
        path=data.path,
        method=data.method,
        target_url=data.target_url,
        timeout=data.timeout,
        enabled=data.enabled,
        config=data.config,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


async def get_service(db: AsyncSession, service_id: str) -> Service | None:
    result = await db.execute(select(Service).where(Service.id == service_id))
    return result.scalar_one_or_none()


async def get_service_by_path(
    db: AsyncSession, path: str, method: str
) -> Service | None:
    result = await db.execute(
        select(Service).where(
            Service.path == path, Service.method == method, Service.enabled == True
        )
    )
    return result.scalar_one_or_none()


async def list_services(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> tuple[list[Service], int]:
    result = await db.execute(select(Service).offset(skip).limit(limit))
    services = result.scalars().all()

    count_result = await db.execute(select(Service))
    total = len(count_result.scalars().all())

    return list(services), total


async def update_service(
    db: AsyncSession, service_id: str, data: ServiceUpdate
) -> Service | None:
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return await get_service(db, service_id)

    update_data["updated_at"] = datetime.utcnow()
    await db.execute(
        update(Service).where(Service.id == service_id).values(**update_data)
    )
    await db.commit()
    return await get_service(db, service_id)


async def delete_service(db: AsyncSession, service_id: str) -> bool:
    service = await get_service(db, service_id)
    if not service:
        return False
    await db.delete(service)
    await db.commit()
    return True

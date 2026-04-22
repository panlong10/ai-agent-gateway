from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Agent, RequestLog, Service


async def create_log(
    db: AsyncSession,
    path: str,
    method: str,
    agent_id: str | None = None,
    service_id: str | None = None,
    request_body: str | None = None,
    response_body: str | None = None,
    status_code: int | None = None,
    duration_ms: int | None = None,
    ip_address: str | None = None,
) -> RequestLog:
    log = RequestLog(
        id=str(uuid4()),
        agent_id=agent_id,
        service_id=service_id,
        path=path,
        method=method,
        request_body=request_body,
        response_body=response_body,
        status_code=status_code,
        duration_ms=duration_ms,
        ip_address=ip_address,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def list_logs(
    db: AsyncSession,
    agent_id: str | None = None,
    service_id: str | None = None,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[RequestLog], int]:
    query = select(RequestLog)

    if agent_id:
        query = query.where(RequestLog.agent_id == agent_id)
    if service_id:
        query = query.where(RequestLog.service_id == service_id)
    if from_time:
        query = query.where(RequestLog.created_at >= from_time)
    if to_time:
        query = query.where(RequestLog.created_at <= to_time)

    query = query.order_by(RequestLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    count_query = select(func.count()).select_from(RequestLog)
    if agent_id:
        count_query = count_query.where(RequestLog.agent_id == agent_id)
    if service_id:
        count_query = count_query.where(RequestLog.service_id == service_id)
    if from_time:
        count_query = count_query.where(RequestLog.created_at >= from_time)
    if to_time:
        count_query = count_query.where(RequestLog.created_at <= to_time)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return list(logs), total


async def get_stats(db: AsyncSession) -> dict:
    total_requests_result = await db.execute(
        select(func.count()).select_from(RequestLog)
    )
    total_requests = total_requests_result.scalar() or 0

    total_agents_result = await db.execute(select(func.count()).select_from(Agent))
    total_agents = total_agents_result.scalar() or 0

    total_services_result = await db.execute(select(func.count()).select_from(Service))
    total_services = total_services_result.scalar() or 0

    from datetime import timedelta

    hour_ago = datetime.utcnow() - timedelta(hours=1)
    last_hour_result = await db.execute(
        select(func.count())
        .select_from(RequestLog)
        .where(RequestLog.created_at >= hour_ago)
    )
    requests_last_hour = last_hour_result.scalar() or 0

    avg_time_result = await db.execute(
        select(func.avg(RequestLog.duration_ms)).select_from(RequestLog)
    )
    avg_response_time = avg_time_result.scalar() or 0.0

    return {
        "total_requests": total_requests,
        "total_agents": total_agents,
        "total_services": total_services,
        "requests_last_hour": requests_last_hour,
        "avg_response_time_ms": float(avg_response_time),
    }

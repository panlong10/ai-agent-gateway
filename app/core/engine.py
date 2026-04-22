import httpx
import httpcore
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import agent as agent_model
from app.models import service as service_model


async def forward_request(
    db: AsyncSession,
    service_id: str,
    request: Request,
    agent_api_key: str | None = None,
):
    service = await service_model.get_service(db, service_id)
    if not service or not service.enabled:
        raise ValueError("Service not found or disabled")

    settings = get_settings()
    timeout = service.timeout or settings.default_timeout

    target_url = service.target_url
    if target_url.endswith("/"):
        target_url = target_url[:-1]

    request_path = request.url.path.replace("/proxy", "", 1)
    full_url = f"{target_url}{request_path}"
    print(f"FULL_URL: {full_url}")

    headers = dict(request.headers)
    headers.pop("host", None)

    if agent_api_key:
        headers["X-Agent-Token"] = agent_api_key

    has_body = request.method in ["POST", "PUT", "PATCH"]
    body = await request.body() if has_body else None

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=5),
        ) as client:
            response = await client.request(
                method=request.method,
                url=full_url,
                headers=headers,
                content=body,
                params=request.query_params,
            )
        return response.text
    except httpcore.ConnectError as e:
        raise ValueError(f"Connection error: {str(e)}")
    except httpcore.ReadTimeout as e:
        raise ValueError(f"Read timeout: {str(e)}")
    except Exception as e:
        raise ValueError(f"Request failed: {str(e)}")


async def get_service_by_path(
    db: AsyncSession,
    path: str,
    method: str,
):
    return await service_model.get_service_by_path(db, path, method)


async def verify_agent(
    db: AsyncSession,
    api_key: str,
):
    return await agent_model.get_agent_by_api_key(db, api_key)

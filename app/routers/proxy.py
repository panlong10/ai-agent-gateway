import json
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette.responses import JSONResponse, PlainTextResponse

from app.database import get_db, Service
from app.core import engine as core_engine


router = APIRouter(prefix="/proxy", tags=["代理转发"])


@router.api_route(
    "/{service_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_request(
    service_path: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    method = request.method
    path = f"/{service_path}"

    api_key = getattr(request.state, "agent_api_key", None)
    is_admin = getattr(request.state, "is_admin", False)

    if not is_admin and api_key:
        agent = await core_engine.verify_agent(db, api_key)
        if not agent:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API Key"},
            )
        agent_key = api_key
    elif is_admin:
        agent_key = api_key
    else:
        agent_key = None

    result = await db.execute(
        select(Service).where(
            Service.path == path, Service.method == method, Service.enabled == True
        )
    )
    service = result.scalar_one_or_none()

    if not service:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"Service not found for path: {path}"},
        )

    try:
        response_text = await core_engine.forward_request(
            db, service.id, request, agent_key
        )

        try:
            data = json.loads(response_text)
            http_code = data.get("code", 200) if isinstance(data, dict) else 200
            return JSONResponse(content=data, status_code=http_code)
        except json.JSONDecodeError:
            return PlainTextResponse(content=response_text, status_code=200)

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": f"Failed to forward request: {str(e)}"},
        )

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import agent as agent_model
from app.models import log as log_model
from app.models import service as service_model
from app.models import intent as intent_model
from app.models import llm_config as llm_config_model
from app.schemas import (
    AgentCreate,
    AgentListResponse,
    AgentResponse,
    AgentUpdate,
    LogListResponse,
    ServiceCreate,
    ServiceListResponse,
    ServiceResponse,
    ServiceUpdate,
    StatsResponse,
)

router = APIRouter(prefix="/admin", tags=["管理接口"])


@router.post(
    "/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED
)
async def create_agent(
    data: AgentCreate,
    db: AsyncSession = Depends(get_db),
):
    api_key = data.api_key if data.api_key else await agent_model.generate_api_key()
    agent = await agent_model.create_agent(db, data, api_key)
    return agent


@router.get("/agents", response_model=AgentListResponse)
async def list_agents(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    agents, total = await agent_model.list_agents(db, skip, page_size)
    items = [AgentResponse.model_validate(a) for a in agents]
    return AgentListResponse(total=total, items=items)


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    agent = await agent_model.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    return agent


@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
):
    agent = await agent_model.update_agent(db, agent_id, data)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    return agent


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
):
    success = await agent_model.delete_agent(db, agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )


@router.post(
    "/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED
)
async def create_service(
    data: ServiceCreate,
    db: AsyncSession = Depends(get_db),
):
    service = await service_model.create_service(db, data)
    return service


@router.get("/services", response_model=ServiceListResponse)
async def list_services(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    services, total = await service_model.list_services(db, skip, page_size)
    items = [ServiceResponse.model_validate(s) for s in services]
    return ServiceListResponse(total=total, items=items)


@router.get("/services/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = await service_model.get_service(db, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    return service


@router.put("/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    data: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = await service_model.update_service(db, service_id, data)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )
    return service


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
):
    success = await service_model.delete_service(db, service_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Service not found"
        )


@router.get("/logs", response_model=LogListResponse)
async def list_logs(
    agent_id: str | None = None,
    service_id: str | None = None,
    from_time: str | None = None,
    to_time: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime

    from_dt = None
    to_dt = None

    if from_time:
        from_dt = datetime.fromisoformat(from_time)
    if to_time:
        to_dt = datetime.fromisoformat(to_time)

    logs, total = await log_model.list_logs(
        db, agent_id, service_id, from_dt, to_dt, page, page_size
    )
    items = [log_model.LogResponse.model_validate(l) for l in logs]
    return LogListResponse(total=total, items=items, page=page, page_size=page_size)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    stats = await log_model.get_stats(db)
    return stats


from app.schemas.intent import IntentCreate, IntentResponse, IntentUpdate
from app.schemas.llm_config import LLMConfigCreate, LLMConfigResponse, LLMConfigUpdate


@router.post(
    "/intents", response_model=IntentResponse, status_code=status.HTTP_201_CREATED
)
async def create_intent(
    data: IntentCreate,
    db: AsyncSession = Depends(get_db),
):
    intent = await intent_model.create_intent(db, data)
    return intent


@router.get("/intents")
async def list_intents(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    intents, total = await intent_model.list_intents(db, skip, page_size)
    items = [IntentResponse.model_validate(i) for i in intents]
    return {"total": total, "items": items}


@router.get("/intents/{intent_id}", response_model=IntentResponse)
async def get_intent(
    intent_id: str,
    db: AsyncSession = Depends(get_db),
):
    intent = await intent_model.get_intent(db, intent_id)
    if not intent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Intent not found"
        )
    return intent


@router.put("/intents/{intent_id}", response_model=IntentResponse)
async def update_intent(
    intent_id: str,
    data: IntentUpdate,
    db: AsyncSession = Depends(get_db),
):
    intent = await intent_model.update_intent(db, intent_id, data)
    if not intent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Intent not found"
        )
    return intent


@router.delete("/intents/{intent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_intent(
    intent_id: str,
    db: AsyncSession = Depends(get_db),
):
    success = await intent_model.delete_intent(db, intent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Intent not found"
        )


@router.post(
    "/llm-configs",
    response_model=LLMConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_llm_config(
    data: LLMConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    config = await llm_config_model.create_llm_config(db, data)
    return config


@router.get("/llm-configs")
async def list_llm_configs(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    configs, total = await llm_config_model.list_llm_configs(db, skip, page_size)
    items = [LLMConfigResponse.model_validate(c) for c in configs]
    return {"total": total, "items": items}


@router.get("/llm-configs/{config_id}", response_model=LLMConfigResponse)
async def get_llm_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
):
    config = await llm_config_model.get_llm_config(db, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LLM Config not found"
        )
    return config


@router.put("/llm-configs/{config_id}", response_model=LLMConfigResponse)
async def update_llm_config(
    config_id: str,
    data: LLMConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    config = await llm_config_model.update_llm_config(db, config_id, data)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LLM Config not found"
        )
    return config


@router.delete("/llm-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
):
    success = await llm_config_model.delete_llm_config(db, config_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="LLM Config not found"
        )

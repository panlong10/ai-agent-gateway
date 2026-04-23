import json
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.database import get_db
from app.core import engine as core_engine
from app.models import llm_config as llm_config_model
from app.models import intent as intent_model
from app.models import service as service_model
from app.services import llm as llm_service


router = APIRouter(prefix="/nlp", tags=["自然语言"])


class NLPParseRequest(BaseModel):
    query: str


class NLPAgentRequest(BaseModel):
    query: str
    params: dict = {}


@router.post("/agent")
async def nlp_agent_request(
    req: NLPAgentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    query = req.query
    api_key = getattr(request.state, "agent_api_key", None)
    is_admin = getattr(request.state, "is_admin", False)

    if not is_admin and api_key:
        agent = await core_engine.verify_agent(db, api_key)
        if not agent:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API Key"},
            )
    elif not api_key:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing API Key"},
        )

    llm_config = await llm_config_model.get_enabled_llm_config(db)
    if not llm_config:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "No LLM configured"},
        )

    intents, _ = await intent_model.list_intents(db)
    if not intents:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "No intents registered"},
        )

    available_intents = []
    for intent in intents:
        intent_dict = {
            "name": intent.name,
            "description": intent.description,
            "pattern": intent.pattern,
        }
        if intent.params_mapping:
            try:
                intent_dict["params_mapping"] = json.loads(intent.params_mapping)
            except:
                intent_dict["params_mapping"] = {}
        available_intents.append(intent_dict)

    try:
        llm = await llm_service.create_llm_service(llm_config)
        result = await llm.parse_intent(query, available_intents)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": f"LLM error: {str(e)}"},
        )

    intent_name = result.get("intent_name")
    extracted_params = result.get("params", {})

    if not intent_name:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Could not understand the intent"},
        )

    intent = await intent_model.get_intent_by_name(db, intent_name)
    if not intent:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"Intent '{intent_name}' not found"},
        )

    service = await service_model.get_service(db, intent.service_id)
    if not service or not service.enabled:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Service not found or disabled"},
        )

    try:
        response_text = await core_engine.forward_request(
            db, service.id, request, api_key, extracted_params
        )

        try:
            data = json.loads(response_text)
            return JSONResponse(content=data)
        except json.JSONDecodeError:
            return JSONResponse(content={"result": response_text})

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": f"Failed to forward request: {str(e)}"},
        )


@router.post("/parse")
async def nlp_parse(
    req: NLPParseRequest,
    db: AsyncSession = Depends(get_db),
):
    query = req.query
    llm_config = await llm_config_model.get_enabled_llm_config(db)

    if not llm_config:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "No LLM configured"},
        )

    intents, _ = await intent_model.list_intents(db)
    available_intents = [
        {
            "name": i.name,
            "description": i.description,
            "pattern": i.pattern,
        }
        for i in intents
    ]

    try:
        llm = await llm_service.create_llm_service(llm_config)
        result = await llm.parse_intent(query, available_intents)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": f"LLM error: {str(e)}"},
        )

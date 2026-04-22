from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentBase(BaseModel):
    name: str = Field(..., description="Agent 名称")
    description: Optional[str] = Field(None, description="描述")


class AgentCreate(AgentBase):
    api_key: Optional[str] = Field(None, description="自定义 API Key（留空则自动生成）")


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class AgentResponse(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    api_key: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class AgentListResponse(BaseModel):
    total: int
    items: list[AgentResponse]

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class IntentBase(BaseModel):
    name: str = Field(..., description="意图名称")
    description: Optional[str] = Field(None, description="意图描述")
    pattern: Optional[str] = Field(None, description="匹配模式")
    service_id: str = Field(..., description="关联的服务ID")
    params_mapping: Optional[str] = Field(None, description="参数映射 JSON")


class IntentCreate(IntentBase):
    pass


class IntentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    pattern: Optional[str] = None
    service_id: Optional[str] = None
    params_mapping: Optional[str] = None
    enabled: Optional[bool] = None


class IntentResponse(IntentBase):
    id: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

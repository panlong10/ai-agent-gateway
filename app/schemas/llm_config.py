from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LLMConfigBase(BaseModel):
    name: str = Field(..., description="LLM 配置名称")
    provider: str = Field(..., description="提供商: openai/anthropic")
    api_key: str = Field(..., description="API Key")
    model: str = Field(..., description="模型名称")
    base_url: Optional[str] = Field(None, description="自定义端点")


class LLMConfigCreate(LLMConfigBase):
    pass


class LLMConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    enabled: Optional[bool] = None


class LLMConfigResponse(LLMConfigBase):
    id: str
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

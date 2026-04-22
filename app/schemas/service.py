from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ServiceBase(BaseModel):
    name: str = Field(..., description="服务名称")
    path: str = Field(..., description="API 路径")
    method: str = Field("POST", description="HTTP 方法")
    target_url: str = Field(..., description="目标服务地址")
    timeout: int = Field(30, description="超时时间（秒）")


class ServiceCreate(ServiceBase):
    enabled: bool = True
    config: Optional[str] = Field(None, description="额外配置（JSON 字符串）")


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None
    target_url: Optional[str] = None
    timeout: Optional[int] = None
    enabled: Optional[bool] = None
    config: Optional[str] = None


class ServiceResponse(ServiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    enabled: bool
    config: Optional[str]
    created_at: datetime
    updated_at: datetime


class ServiceListResponse(BaseModel):
    total: int
    items: list[ServiceResponse]

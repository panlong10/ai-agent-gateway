from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class LogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_id: Optional[str]
    service_id: Optional[str]
    path: str
    method: str
    request_body: Optional[str]
    response_body: Optional[str]
    status_code: Optional[int]
    duration_ms: Optional[int]
    ip_address: Optional[str]
    created_at: datetime


class LogListResponse(BaseModel):
    total: int
    items: list[LogResponse]
    page: int
    page_size: int


class StatsResponse(BaseModel):
    total_requests: int
    total_agents: int
    total_services: int
    requests_last_hour: int
    avg_response_time_ms: float

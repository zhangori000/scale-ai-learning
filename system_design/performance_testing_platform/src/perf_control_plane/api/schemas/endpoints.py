from __future__ import annotations

from datetime import datetime

from perf_control_plane.domain.entities.base import BaseModel
from perf_control_plane.domain.entities.endpoints import HttpMethod, RiskClass


class EndpointCreateRequest(BaseModel):
    service_name: str
    method: HttpMethod
    path: str
    base_url: str | None = None
    owner_team: str
    risk_class: RiskClass = RiskClass.MODERATE
    description: str | None = None


class EndpointResponse(BaseModel):
    id: str
    service_name: str
    method: HttpMethod
    path: str
    base_url: str | None = None
    owner_team: str
    risk_class: RiskClass
    description: str | None = None
    created_at: datetime
    updated_at: datetime

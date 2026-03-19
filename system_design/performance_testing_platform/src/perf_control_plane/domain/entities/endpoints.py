from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import Field

from perf_control_plane.domain.entities.base import BaseModel


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class RiskClass(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXPENSIVE = "expensive"


class EndpointEntity(BaseModel):
    id: str
    service_name: str
    method: HttpMethod
    path: str
    base_url: str | None = None
    owner_team: str
    risk_class: RiskClass = RiskClass.MODERATE
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

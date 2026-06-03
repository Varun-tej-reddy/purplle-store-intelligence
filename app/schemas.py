from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

SUPPORTED_EVENTS = {
    "ENTRY",
    "EXIT",
    "ZONE_ENTER",
    "ZONE_EXIT",
    "ZONE_DWELL",
    "BILLING_QUEUE_JOIN",
    "BILLING_QUEUE_ABANDON",
    "REENTRY",
}


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=128)
    store_id: str = Field(min_length=1, max_length=64)
    camera_id: str = Field(min_length=1, max_length=128)
    visitor_id: str = Field(min_length=1, max_length=128)
    event_type: str
    timestamp: datetime
    zone_id: str | None = Field(default=None, max_length=64)
    dwell_ms: int | None = Field(default=None, ge=0)
    is_staff: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_type")
    @classmethod
    def valid_event_type(cls, value: str) -> str:
        if value not in SUPPORTED_EVENTS:
            raise ValueError(f"Unsupported event_type '{value}'")
        return value


class IngestRequest(BaseModel):
    events: list[EventIn] = Field(min_length=1)


class IngestResponse(BaseModel):
    received: int
    inserted: int
    duplicates: int
    duplicate_event_ids: list[str]


class MetricsResponse(BaseModel):
    unique_visitors: int
    conversion_rate: float
    average_dwell: float
    queue_depth: int
    abandonment_rate: float


class FunnelStage(BaseModel):
    stage: str
    count: int
    dropoff_percentage: float


class FunnelResponse(BaseModel):
    stages: list[FunnelStage]


class HeatmapRow(BaseModel):
    zone: str
    visits: int
    average_dwell: float
    normalized_score: float


class HeatmapResponse(BaseModel):
    zones: list[HeatmapRow]


class AnomalyItem(BaseModel):
    anomaly_type: str
    severity: str
    message: str
    suggested_action: str
    detected_at: datetime


class AnomaliesResponse(BaseModel):
    active_anomalies: list[AnomalyItem]


class HealthResponse(BaseModel):
    status: str
    last_event_timestamp: datetime | None
    stale_feed_warning: bool

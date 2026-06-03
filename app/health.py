from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models


def get_health(db: Session) -> dict:
    # Treat frame-derived epoch timestamps as invalid event-time for health display.
    # We keep event generation unchanged and use ingest time fallback for meaningful UI output.
    valid_ts_cutoff = datetime(2000, 1, 1, tzinfo=timezone.utc)
    latest_valid_event_ts = db.execute(
        select(models.Event.timestamp)
        .where(models.Event.timestamp >= valid_ts_cutoff)
        .order_by(desc(models.Event.timestamp))
        .limit(1)
    ).scalar_one_or_none()

    latest_ingested_at = db.execute(
        select(models.Event.created_at)
        .order_by(desc(models.Event.created_at))
        .limit(1)
    ).scalar_one_or_none()

    has_events = latest_ingested_at is not None
    recent_window_start = datetime.now(timezone.utc) - timedelta(minutes=5)
    has_recent_events = (
        db.execute(
            select(models.Event.id)
            .where(models.Event.created_at >= recent_window_start)
            .limit(1)
        ).scalar_one_or_none()
        is not None
    ) if has_events else False

    status = "healthy" if has_events else "degraded"
    stale_warning = has_events and not has_recent_events
    last_event = latest_valid_event_ts or latest_ingested_at

    return {
        "status": status,
        "last_event_timestamp": last_event,
        "stale_feed_warning": stale_warning,
    }

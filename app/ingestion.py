from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app import models
from app.schemas import EventIn
from app.store_utils import ensure_store

logger = logging.getLogger(__name__)


class IngestionResult(dict):
    pass


def _transaction_id(store_id: str, visitor_id: str, ts: datetime) -> str:
    raw = f"{store_id}:{visitor_id}:{ts.isoformat()}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def ingest_events(db: Session, events: list[EventIn]) -> IngestionResult:
    if not events:
        return IngestionResult(received=0, inserted=0, duplicates=0, duplicate_event_ids=[])

    event_ids = [event.event_id for event in events]
    existing_ids = set(
        db.execute(select(models.Event.event_id).where(models.Event.event_id.in_(event_ids))).scalars().all()
    )

    seen_in_batch: set[str] = set()
    duplicate_event_ids: list[str] = []
    inserted = 0

    visitor_bounds: dict[tuple[str, str], list[datetime]] = defaultdict(list)

    for event in events:
        if event.event_id in existing_ids or event.event_id in seen_in_batch:
            duplicate_event_ids.append(event.event_id)
            continue

        seen_in_batch.add(event.event_id)
        ensure_store(db, event.store_id)

        db_event = models.Event(
            event_id=event.event_id,
            store_id=event.store_id,
            camera_id=event.camera_id,
            visitor_id=event.visitor_id,
            event_type=event.event_type,
            timestamp=event.timestamp,
            zone_id=event.zone_id,
            dwell_ms=event.dwell_ms,
            is_staff=event.is_staff,
            confidence=event.confidence,
            metadata_json=event.metadata,
        )
        db.add(db_event)
        inserted += 1

        visitor_bounds[(event.store_id, event.visitor_id)].append(event.timestamp)

        if event.metadata.get("is_purchase"):
            transaction_id = str(event.metadata.get("transaction_id") or _transaction_id(event.store_id, event.visitor_id, event.timestamp))
            if db.get(models.Transaction, transaction_id) is None:
                db.add(
                    models.Transaction(
                        id=transaction_id,
                        store_id=event.store_id,
                        visitor_id=event.visitor_id,
                        amount=float(event.metadata.get("amount", 0.0)),
                        occurred_at=event.timestamp,
                        metadata_json={"source_event_id": event.event_id},
                    )
                )

    db.flush()

    for (store_id, visitor_id), timestamps in visitor_bounds.items():
        min_ts = min(timestamps)
        max_ts = max(timestamps)

        session = db.execute(
            select(models.VisitorSession).where(
                and_(
                    models.VisitorSession.store_id == store_id,
                    models.VisitorSession.visitor_id == visitor_id,
                )
            )
        ).scalar_one_or_none()

        if session is None:
            db.add(
                models.VisitorSession(
                    store_id=store_id,
                    visitor_id=visitor_id,
                    first_seen_at=min_ts,
                    last_seen_at=max_ts,
                    session_count=1,
                )
            )
        else:
            session.first_seen_at = min(session.first_seen_at, min_ts)
            session.last_seen_at = max(session.last_seen_at, max_ts)

    db.commit()

    result = IngestionResult(
        received=len(events),
        inserted=inserted,
        duplicates=len(duplicate_event_ids),
        duplicate_event_ids=duplicate_event_ids,
    )
    logger.info("Ingestion complete: %s", result)
    return result

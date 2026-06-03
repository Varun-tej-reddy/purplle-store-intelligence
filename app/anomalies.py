from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models
from app.metrics import compute_metrics
from app.store_utils import ensure_store

ZONES = ("ENTRY", "FOH", "FRAGRANCE", "MAKEUP", "BILLING")
logger = logging.getLogger(__name__)


def _upsert_anomaly(
    db: Session,
    store_id: str,
    anomaly_type: str,
    should_activate: bool,
    severity: str,
    message: str,
    action: str,
    now: datetime,
) -> None:
    anomaly_id = f"{store_id}:{anomaly_type}"
    anomaly = db.get(models.Anomaly, anomaly_id)
    if should_activate:
        if anomaly is None:
            db.add(
                models.Anomaly(
                    id=anomaly_id,
                    store_id=store_id,
                    anomaly_type=anomaly_type,
                    severity=severity,
                    message=message,
                    suggested_action=action,
                    is_active=True,
                    detected_at=now,
                    resolved_at=None,
                )
            )
        else:
            anomaly.is_active = True
            anomaly.severity = severity
            anomaly.message = message
            anomaly.suggested_action = action
            anomaly.detected_at = now
            anomaly.resolved_at = None
    elif anomaly is not None and anomaly.is_active:
        anomaly.is_active = False
        anomaly.resolved_at = now


def detect_anomalies(db: Session, store_id: str, now: datetime | None = None) -> None:
    now = now or datetime.utcnow()
    ensure_store(db, store_id)
    metrics = compute_metrics(db, store_id)

    queue_threshold = int(os.getenv("QUEUE_SPIKE_THRESHOLD", "5"))
    queue_spike = metrics["queue_depth"] > queue_threshold
    _upsert_anomaly(
        db,
        store_id,
        "Queue Spike",
        queue_spike,
        "high" if metrics["queue_depth"] > queue_threshold * 2 else "medium",
        f"Queue depth is {metrics['queue_depth']} (threshold: {queue_threshold}).",
        "Open additional billing counters and route floor staff to billing.",
        now,
    )

    current_window_start = now - timedelta(hours=1)
    historical_window_start = now - timedelta(days=7)

    current_visitors = db.execute(
        select(func.count(func.distinct(models.Event.visitor_id))).where(
            models.Event.store_id == store_id,
            models.Event.timestamp >= current_window_start,
            models.Event.is_staff.is_(False),
        )
    ).scalar_one()
    current_purchases = db.execute(
        select(func.count(func.distinct(models.Transaction.visitor_id))).where(
            models.Transaction.store_id == store_id,
            models.Transaction.occurred_at >= current_window_start,
        )
    ).scalar_one()

    current_conversion = (current_purchases / current_visitors) if current_visitors else 0.0

    historical_visitors = db.execute(
        select(func.count(func.distinct(models.Event.visitor_id))).where(
            models.Event.store_id == store_id,
            models.Event.timestamp >= historical_window_start,
            models.Event.timestamp < current_window_start,
            models.Event.is_staff.is_(False),
        )
    ).scalar_one()
    historical_purchases = db.execute(
        select(func.count(func.distinct(models.Transaction.visitor_id))).where(
            models.Transaction.store_id == store_id,
            models.Transaction.occurred_at >= historical_window_start,
            models.Transaction.occurred_at < current_window_start,
        )
    ).scalar_one()

    historical_conversion = (historical_purchases / historical_visitors) if historical_visitors else 0.0
    conversion_drop = historical_conversion > 0 and current_conversion < (0.7 * historical_conversion)

    _upsert_anomaly(
        db,
        store_id,
        "Conversion Drop",
        conversion_drop,
        "high",
        (
            f"Conversion dropped to {current_conversion:.2%} from historical {historical_conversion:.2%}."
            if historical_conversion > 0
            else "Conversion has dropped below expected baseline."
        ),
        "Audit stock availability and associate coverage in high-intent zones.",
        now,
    )

    dead_window_start = now - timedelta(minutes=30)
    dead_zones = []
    for zone in ZONES:
        recent_count = db.execute(
            select(func.count())
            .select_from(models.Event)
            .where(
                and_(
                    models.Event.store_id == store_id,
                    models.Event.zone_id == zone,
                    models.Event.event_type == "ZONE_ENTER",
                    models.Event.timestamp >= dead_window_start,
                    models.Event.is_staff.is_(False),
                )
            )
        ).scalar_one()
        if recent_count == 0:
            dead_zones.append(zone)

    dead_zone_active = len(dead_zones) > 0
    dead_zone_message = (
        f"No visitor movement in zones for 30+ minutes: {', '.join(dead_zones)}."
        if dead_zones
        else "All zones are receiving traffic."
    )

    _upsert_anomaly(
        db,
        store_id,
        "Dead Zone",
        dead_zone_active,
        "medium",
        dead_zone_message,
        "Inspect merchandising and signage in inactive zones.",
        now,
    )

    db.commit()


def get_active_anomalies(db: Session, store_id: str) -> dict:
    try:
        detect_anomalies(db, store_id)
        anomalies = db.execute(
            select(models.Anomaly)
            .where(
                models.Anomaly.store_id == store_id,
                models.Anomaly.is_active.is_(True),
            )
            .order_by(models.Anomaly.detected_at.desc())
        ).scalars().all()
    except SQLAlchemyError:
        logger.exception("Anomaly generation failed for store_id=%s", store_id)
        db.rollback()
        return {"active_anomalies": []}

    return {
        "active_anomalies": [
            {
                "anomaly_type": a.anomaly_type,
                "severity": a.severity,
                "message": a.message,
                "suggested_action": a.suggested_action,
                "detected_at": a.detected_at,
            }
            for a in anomalies
        ]
    }

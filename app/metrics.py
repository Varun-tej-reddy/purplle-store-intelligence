from __future__ import annotations

from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models


def compute_metrics(db: Session, store_id: str) -> dict:
    unique_visitors = db.execute(
        select(func.count(func.distinct(models.Event.visitor_id))).where(
            models.Event.store_id == store_id,
            models.Event.is_staff.is_(False),
        )
    ).scalar_one()

    purchasing_visitors = db.execute(
        select(func.count(func.distinct(models.Transaction.visitor_id))).where(
            models.Transaction.store_id == store_id,
        )
    ).scalar_one()

    average_dwell = (
        db.execute(
            select(func.avg(models.Event.dwell_ms)).where(
                models.Event.store_id == store_id,
                models.Event.event_type == "ZONE_DWELL",
                models.Event.dwell_ms.is_not(None),
            )
        ).scalar_one()
        or 0.0
    )

    queue_joins = db.execute(
        select(func.count()).where(
            models.Event.store_id == store_id,
            models.Event.event_type == "BILLING_QUEUE_JOIN",
        ).select_from(models.Event)
    ).scalar_one()
    queue_abandons = db.execute(
        select(func.count()).where(
            models.Event.store_id == store_id,
            models.Event.event_type == "BILLING_QUEUE_ABANDON",
        ).select_from(models.Event)
    ).scalar_one()

    queue_depth = max(queue_joins - queue_abandons - purchasing_visitors, 0)
    abandonment_rate = (queue_abandons / queue_joins) if queue_joins else 0.0
    conversion_rate = (purchasing_visitors / unique_visitors) if unique_visitors else 0.0

    return {
        "unique_visitors": int(unique_visitors),
        "conversion_rate": round(float(conversion_rate), 4),
        "average_dwell": round(float(average_dwell), 2),
        "queue_depth": int(queue_depth),
        "abandonment_rate": round(float(abandonment_rate), 4),
    }


def compute_heatmap(db: Session, store_id: str) -> dict:
    visits_by_zone = defaultdict(int)
    dwell_by_zone = defaultdict(float)

    zone_visits = db.execute(
        select(models.Event.zone_id, func.count())
        .where(
            models.Event.store_id == store_id,
            models.Event.event_type == "ZONE_ENTER",
            models.Event.zone_id.is_not(None),
        )
        .group_by(models.Event.zone_id)
    ).all()

    zone_dwell = db.execute(
        select(models.Event.zone_id, func.avg(models.Event.dwell_ms))
        .where(
            models.Event.store_id == store_id,
            models.Event.event_type == "ZONE_DWELL",
            models.Event.zone_id.is_not(None),
        )
        .group_by(models.Event.zone_id)
    ).all()

    for zone, count in zone_visits:
        if zone:
            visits_by_zone[zone] = int(count)

    for zone, avg_dwell in zone_dwell:
        if zone:
            dwell_by_zone[zone] = float(avg_dwell or 0.0)

    zones = sorted(set(visits_by_zone.keys()) | set(dwell_by_zone.keys()))
    raw_scores = {zone: (visits_by_zone[zone] * max(dwell_by_zone[zone], 1.0)) for zone in zones}

    if raw_scores:
        min_score = min(raw_scores.values())
        max_score = max(raw_scores.values())
    else:
        min_score = 0.0
        max_score = 0.0

    rows = []
    for zone in zones:
        score = raw_scores[zone]
        normalized = 1.0 if max_score == min_score and max_score > 0 else (
            0.0 if max_score == min_score else (score - min_score) / (max_score - min_score)
        )
        rows.append(
            {
                "zone": zone,
                "visits": visits_by_zone[zone],
                "average_dwell": round(dwell_by_zone[zone], 2),
                "normalized_score": round(normalized, 4),
            }
        )

    return {"zones": rows}

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models


def compute_funnel(db: Session, store_id: str) -> dict:
    entry = db.execute(
        select(func.count(func.distinct(models.Event.visitor_id))).where(
            models.Event.store_id == store_id,
            models.Event.event_type == "ENTRY",
            models.Event.is_staff.is_(False),
        )
    ).scalar_one()

    zone_visit = db.execute(
        select(func.count(func.distinct(models.Event.visitor_id))).where(
            models.Event.store_id == store_id,
            models.Event.event_type == "ZONE_ENTER",
            models.Event.is_staff.is_(False),
        )
    ).scalar_one()

    billing_queue = db.execute(
        select(func.count(func.distinct(models.Event.visitor_id))).where(
            models.Event.store_id == store_id,
            models.Event.event_type == "BILLING_QUEUE_JOIN",
            models.Event.is_staff.is_(False),
        )
    ).scalar_one()

    purchase = db.execute(
        select(func.count(func.distinct(models.Transaction.visitor_id))).where(
            models.Transaction.store_id == store_id,
        )
    ).scalar_one()

    counts = [int(entry), int(zone_visit), int(billing_queue), int(purchase)]
    stages = ["Entry", "Zone Visit", "Billing Queue", "Purchase"]

    response = []
    prev = counts[0]
    for idx, stage in enumerate(stages):
        count = counts[idx]
        if idx == 0 or prev == 0:
            dropoff = 0.0
        else:
            dropoff = max((prev - count) / prev, 0.0)
        response.append(
            {
                "stage": stage,
                "count": count,
                "dropoff_percentage": round(float(dropoff * 100), 2),
            }
        )
        prev = count

    return {"stages": response}

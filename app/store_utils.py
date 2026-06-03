from __future__ import annotations

from sqlalchemy.orm import Session

from app import models


def ensure_store(db: Session, store_id: str, *, name: str | None = None) -> models.Store:
    """
    Ensure a store row exists for the provided store_id in the current transaction.
    """
    store = db.get(models.Store, store_id)
    if store is None:
        store = models.Store(id=store_id, name=name or f"Store {store_id}")
        db.add(store)
    return store

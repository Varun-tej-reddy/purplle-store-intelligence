from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.anomalies import get_active_anomalies
from app.database import Base, SessionLocal, engine, get_db
from app.funnel import compute_funnel
from app.health import get_health
from app.ingestion import ingest_events
from app.metrics import compute_heatmap, compute_metrics
from app.schemas import (
    AnomaliesResponse,
    FunnelResponse,
    HealthResponse,
    HeatmapResponse,
    IngestRequest,
    IngestResponse,
    MetricsResponse,
)
from app.store_utils import ensure_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
DEMO_STORE_ID = "store_1"

app = FastAPI(title="Purplle Store Intelligence", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        try:
            ensure_store(db, DEMO_STORE_ID, name="Purplle Demo Store 1")
            db.commit()
        except SQLAlchemyError:
            logger.exception("Failed to seed demo store '%s'", DEMO_STORE_ID)
            db.rollback()
    logger.info("Database schema verified and demo seed checked")


@app.post("/events/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, db: Session = Depends(get_db)) -> IngestResponse:
    try:
        result = ingest_events(db, payload.events)
        return IngestResponse(**result)
    except Exception as exc:  # pragma: no cover - defensive path
        logger.exception("Failed to ingest events")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ingestion failed") from exc


@app.get("/stores/{store_id}/metrics", response_model=MetricsResponse)
def metrics(store_id: str, db: Session = Depends(get_db)) -> MetricsResponse:
    return MetricsResponse(**compute_metrics(db, store_id))


@app.get("/stores/{store_id}/funnel", response_model=FunnelResponse)
def funnel(store_id: str, db: Session = Depends(get_db)) -> FunnelResponse:
    return FunnelResponse(**compute_funnel(db, store_id))


@app.get("/stores/{store_id}/heatmap", response_model=HeatmapResponse)
def heatmap(store_id: str, db: Session = Depends(get_db)) -> HeatmapResponse:
    return HeatmapResponse(**compute_heatmap(db, store_id))


@app.get("/stores/{store_id}/anomalies", response_model=AnomaliesResponse)
def anomalies(store_id: str, db: Session = Depends(get_db)) -> AnomaliesResponse:
    return AnomaliesResponse(**get_active_anomalies(db, store_id))


@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    return HealthResponse(**get_health(db))

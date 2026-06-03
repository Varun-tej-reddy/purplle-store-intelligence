# Technology Choices

## 1. Why YOLOv8

- Strong real-time detector quality/latency tradeoff.
- Mature Python API for fast integration.
- Supports class filtering (`person`) and confidence controls out-of-the-box.

## 2. Why ByteTrack

- Robust identity tracking for crowded scenes.
- Better ID continuity than simple centroid tracking.
- Natural fit for deriving zone transition events and dwell times.

## 3. Why PostgreSQL

- Reliable transactional consistency for event ingestion and deduplication.
- Rich indexing and aggregation support for analytics workloads.
- Good operational ergonomics with Docker Compose.

## 4. Why FastAPI

- High performance async-ready Python web framework.
- Automatic OpenAPI docs.
- Excellent Pydantic validation for strict event schema enforcement.

## 5. Event Schema Design Decisions

- Event payload captures immutable facts with traceable IDs (`event_id`, `visitor_id`, `camera_id`).
- Optional fields (`zone_id`, `dwell_ms`) support event-type-specific semantics.
- `metadata` provides extensibility for purchases and future integrations.
- `confidence` preserved for CV-origin observability and downstream filtering.

# Design Document

## 1. High-Level Architecture

```
+------------------+       +------------------+      +-----------------+
| CCTV Video Files | ----> | CV Pipeline      | ---> | JSONL Events    |
| (data/videos/*)  |       | (YOLOv8+Tracker) |      |                 |
+------------------+       +------------------+      +-----------------+
                                                            |
                                                            v
                                                    +-----------------+
                                                    | FastAPI Ingest  |
                                                    | /events/ingest  |
                                                    +-----------------+
                                                            |
                                                            v
                                                    +-----------------+
                                                    | PostgreSQL      |
                                                    | stores/events/* |
                                                    +-----------------+
                                                            |
                                                            v
                                                    +-----------------+
                                                    | Analytics APIs  |
                                                    | + Anomalies     |
                                                    +-----------------+
                                                            |
                                                            v
                                                    +-----------------+
                                                    | React Dashboard |
                                                    +-----------------+
```

## 2. Event Flow

1. YOLOv8 detects person-class bounding boxes.
2. Tracker assigns a stable `visitor_id`.
3. Zone assigner maps coordinates to store zones.
4. Event emitter derives transitions:
   - `ENTRY`, `EXIT`
   - `ZONE_ENTER`, `ZONE_EXIT`, `ZONE_DWELL`
   - `BILLING_QUEUE_JOIN`, `BILLING_QUEUE_ABANDON`
   - `REENTRY` (supported by schema for future extension)
5. JSONL records are ingested through `/events/ingest`.
6. Backend persists and updates `visitor_sessions` and `transactions`.

## 3. Database Design

Tables:

- `stores`: store metadata
- `events`: immutable event stream, unique `event_id`
- `visitor_sessions`: per `(store_id, visitor_id)` summary bounds
- `transactions`: purchase records tied to visitor identity
- `anomalies`: active/resolved anomaly state

Indexes are applied on `events(store_id,timestamp)` and event identifiers for query performance.

## 4. AI-Assisted Decisions

- Used model-assisted generation for project bootstrap and module structuring.
- Final architecture and code-level integration decisions were manually curated to ensure deterministic API behavior and testability.
- Tracking implementation is intentionally abstracted behind `ByteTrackAdapter` so it can be swapped with native Ultralytics ByteTrack config without breaking event interfaces.

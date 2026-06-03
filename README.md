# Purplle Store Intelligence System

Production-style AI analytics platform for converting CCTV footage into business KPIs.

## Architecture

Data flow:

`CCTV Video -> YOLOv8 Detection -> ByteTrack Tracking -> Zone Assignment -> Event Emission -> PostgreSQL -> FastAPI Analytics -> React Dashboard`

Core components:

- `pipeline/`: computer-vision event generation pipeline (YOLOv8 + tracker abstraction)
- `app/`: FastAPI backend with ingestion, metrics, funnel, heatmap, anomalies, health
- `frontend/`: React + Vite dashboard with Chart.js visualizations
- `tests/`: Pytest suite for ingestion/metrics/funnel/anomalies

## Quick Start

### Prerequisites

- Docker
- Docker Compose

### Run

```bash
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`
- PostgreSQL: `localhost:5432`

## API Endpoints

- `POST /events/ingest`
- `GET /stores/{id}/metrics`
- `GET /stores/{id}/funnel`
- `GET /stores/{id}/heatmap`
- `GET /stores/{id}/anomalies`
- `GET /health`

## Example Ingestion Payload

```json
{
  "events": [
    {
      "event_id": "evt_101",
      "store_id": "store_1",
      "camera_id": "cam_1",
      "visitor_id": "visitor_42",
      "event_type": "ENTRY",
      "timestamp": "2026-01-01T10:00:00Z",
      "zone_id": "ENTRY",
      "dwell_ms": null,
      "is_staff": false,
      "confidence": 0.97,
      "metadata": {}
    }
  ]
}
```

## Running Tests

```bash
pytest -q
```

## CV Pipeline Usage

```bash
bash pipeline/run.sh data/videos/sample.mp4 data/output/events.jsonl
```

or

```bash
python -m pipeline.process_video --video data/videos/sample.mp4 --output data/output/events.jsonl
```

## Notes

- Ingestion deduplicates by `event_id`
- Conversion is computed as unique purchasers / unique visitors
- Active anomalies are recalculated on anomaly endpoint calls

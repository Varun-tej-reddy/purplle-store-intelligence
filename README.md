# Purplle Store Intelligence

AI-powered retail analytics platform that transforms CCTV footage into actionable business insights.

Built for the Purplle Tech Challenge 2026.

---

## Overview

Retail stores generate massive amounts of CCTV footage, but extracting useful business insights manually is difficult and time-consuming.

Purplle Store Intelligence uses Computer Vision, Multi-Object Tracking, and Event Analytics to convert raw surveillance video into structured retail intelligence.

The system automatically detects customers, tracks their movement across store zones, measures dwell times, identifies queue behavior, and generates analytics dashboards for business decision-making.

---

## Features

### Customer Footfall Analytics
- Detects customer entries and exits
- Counts visitors per camera
- Tracks unique visitors

### Zone Analytics
- Zone entry detection
- Zone exit detection
- Zone dwell-time tracking
- Customer movement analysis

### Queue Monitoring
- Billing queue join detection
- Queue behavior analysis
- Customer congestion monitoring

### Event Pipeline
- Real-time event generation
- Structured JSON event stream
- Event ingestion API
- PostgreSQL event storage

### Analytics Dashboard
- Live event feed
- Store health monitoring
- Footfall metrics
- Funnel analytics
- Zone performance insights
- Anomaly detection

---

## Architecture

```text
CCTV Videos
      │
      ▼
YOLOv8 Person Detection
      │
      ▼
ByteTrack Multi-Object Tracking
      │
      ▼
Zone Assignment Engine
      │
      ▼
Event Generation Pipeline
      │
      ▼
FastAPI Backend
      │
      ▼
PostgreSQL Database
      │
      ▼
React Dashboard
```

---

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic

### Computer Vision
- YOLOv8
- OpenCV
- ByteTrack
- NumPy

### Frontend
- React
- Vite
- JavaScript
- CSS

### DevOps
- Docker
- Docker Compose

### Testing
- Pytest

---

## Project Structure

```text
purplle-store-intelligence/
│
├── app/
│   ├── main.py
│   ├── ingestion.py
│   ├── metrics.py
│   ├── funnel.py
│   ├── anomalies.py
│   └── health.py
│
├── pipeline/
│   ├── detect.py
│   ├── tracker.py
│   ├── zones.py
│   ├── emit.py
│   └── process_video.py
│
├── frontend/
│   ├── src/
│   └── package.json
│
├── docs/
│   ├── DESIGN.md
│   └── CHOICES.md
│
├── tests/
│
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Event Types

The system generates the following retail events:

- ENTRY
- EXIT
- ZONE_ENTER
- ZONE_EXIT
- ZONE_DWELL
- BILLING_QUEUE_JOIN

Example Event:

```json
{
  "event_id": "evt_001",
  "store_id": "store_1",
  "camera_id": "cam_1",
  "visitor_id": "visitor_12",
  "event_type": "ZONE_ENTER",
  "timestamp": "2026-05-31T10:15:30Z"
}
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/Varun-tej-reddy/purplle-store-intelligence.git

cd purplle-store-intelligence
```

---

## Run With Docker

### Build

```bash
docker compose build
```

### Start Services

```bash
docker compose up -d
```

### Services

Live Demo:
https://purplle-store-intelligence-one.vercel.app/

Repository:
https://github.com/Varun-tej-reddy/purplle-store-intelligence

---

## Processing Videos

Example:

```bash
python -m pipeline.process_video \
--video "CAM 1.mp4" \
--camera-id cam_1 \
--output output/events_cam1.jsonl
```

Generated events can then be ingested into the backend.

---

## API Endpoints

### Health

```http
GET /health
```

### Event Ingestion

```http
POST /events/ingest
```

### Metrics

```http
GET /metrics
```

### Funnel Analytics

```http
GET /funnel
```

### Anomalies

```http
GET /anomalies
```

---

## Sample Results

Example processed dataset:

| Camera | Entries | Exits |
|----------|----------|----------|
| cam_1 | 12 | 12 |
| cam_2 | 13 | 12 |
| cam_5 | 2 | 2 |

Total Events Processed:

```text
160+
```

---

## Testing

Run tests:

```bash
pytest
```

---

## Design Decisions

Key design decisions are documented in:

```text
docs/DESIGN.md
docs/CHOICES.md
```

---

## Future Improvements

- Real-time RTSP camera support
- Multi-camera identity association
- Advanced queue analytics
- Heatmap visualization
- Customer journey prediction
- Cloud deployment
- Real-time alerting

---

## Team

### Varun Tej Reddy

Purplle Tech Challenge 2026 Submission

---

## License

This project was developed as part of the Purplle Tech Challenge 2026 hackathon and is intended for educational and demonstration purposes.

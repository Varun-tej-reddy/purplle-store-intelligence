from __future__ import annotations


def test_ingest_deduplicates_events(client):
    payload = {
        "events": [
            {
                "event_id": "evt_1",
                "store_id": "store_1",
                "camera_id": "cam_1",
                "visitor_id": "v_1",
                "event_type": "ENTRY",
                "timestamp": "2026-01-01T00:00:00Z",
                "zone_id": "ENTRY",
                "dwell_ms": None,
                "is_staff": False,
                "confidence": 0.9,
                "metadata": {},
            },
            {
                "event_id": "evt_1",
                "store_id": "store_1",
                "camera_id": "cam_1",
                "visitor_id": "v_1",
                "event_type": "ENTRY",
                "timestamp": "2026-01-01T00:00:01Z",
                "zone_id": "ENTRY",
                "dwell_ms": None,
                "is_staff": False,
                "confidence": 0.9,
                "metadata": {},
            },
        ]
    }

    response = client.post("/events/ingest", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["received"] == 2
    assert body["inserted"] == 1
    assert body["duplicates"] == 1
    assert body["duplicate_event_ids"] == ["evt_1"]

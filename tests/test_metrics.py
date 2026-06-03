from __future__ import annotations


def test_metrics_and_heatmap_endpoints(client):
    events = {
        "events": [
            {
                "event_id": "evt_m1",
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
                "event_id": "evt_m2",
                "store_id": "store_1",
                "camera_id": "cam_1",
                "visitor_id": "v_1",
                "event_type": "ZONE_ENTER",
                "timestamp": "2026-01-01T00:00:05Z",
                "zone_id": "FOH",
                "dwell_ms": None,
                "is_staff": False,
                "confidence": 0.9,
                "metadata": {},
            },
            {
                "event_id": "evt_m3",
                "store_id": "store_1",
                "camera_id": "cam_1",
                "visitor_id": "v_1",
                "event_type": "ZONE_DWELL",
                "timestamp": "2026-01-01T00:00:06Z",
                "zone_id": "FOH",
                "dwell_ms": 3200,
                "is_staff": False,
                "confidence": 0.9,
                "metadata": {"is_purchase": True, "amount": 500.0, "transaction_id": "txn_1"},
            },
        ]
    }

    ingest_response = client.post("/events/ingest", json=events)
    assert ingest_response.status_code == 200

    metrics_response = client.get("/stores/store_1/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert metrics["unique_visitors"] == 1
    assert metrics["conversion_rate"] == 1.0
    assert metrics["average_dwell"] == 3200.0

    heatmap_response = client.get("/stores/store_1/heatmap")
    assert heatmap_response.status_code == 200
    heatmap = heatmap_response.json()
    assert len(heatmap["zones"]) == 1
    assert heatmap["zones"][0]["zone"] == "FOH"

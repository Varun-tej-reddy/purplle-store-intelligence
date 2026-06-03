from __future__ import annotations


def test_funnel_endpoint(client):
    payload = {
        "events": [
            {
                "event_id": "evt_f1",
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
                "event_id": "evt_f2",
                "store_id": "store_1",
                "camera_id": "cam_1",
                "visitor_id": "v_1",
                "event_type": "ZONE_ENTER",
                "timestamp": "2026-01-01T00:00:01Z",
                "zone_id": "FOH",
                "dwell_ms": None,
                "is_staff": False,
                "confidence": 0.9,
                "metadata": {},
            },
            {
                "event_id": "evt_f3",
                "store_id": "store_1",
                "camera_id": "cam_1",
                "visitor_id": "v_1",
                "event_type": "BILLING_QUEUE_JOIN",
                "timestamp": "2026-01-01T00:00:03Z",
                "zone_id": "BILLING",
                "dwell_ms": None,
                "is_staff": False,
                "confidence": 0.9,
                "metadata": {"is_purchase": True, "transaction_id": "txn_f1"},
            },
        ]
    }
    ingest_response = client.post("/events/ingest", json=payload)
    assert ingest_response.status_code == 200

    funnel_response = client.get("/stores/store_1/funnel")
    assert funnel_response.status_code == 200
    stages = funnel_response.json()["stages"]
    assert [s["stage"] for s in stages] == ["Entry", "Zone Visit", "Billing Queue", "Purchase"]
    assert [s["count"] for s in stages] == [1, 1, 1, 1]

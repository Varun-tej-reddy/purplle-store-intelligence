from __future__ import annotations


def test_anomalies_endpoint_without_preexisting_store_does_not_500(client):
    anomalies_response = client.get("/stores/store_1/anomalies")
    assert anomalies_response.status_code == 200
    body = anomalies_response.json()
    assert "active_anomalies" in body
    assert isinstance(body["active_anomalies"], list)


def test_dead_zone_anomaly_is_reported(client):
    payload = {
        "events": [
            {
                "event_id": "evt_a1",
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
            }
        ]
    }
    ingest_response = client.post("/events/ingest", json=payload)
    assert ingest_response.status_code == 200

    anomalies_response = client.get("/stores/store_1/anomalies")
    assert anomalies_response.status_code == 200
    anomalies = anomalies_response.json()["active_anomalies"]
    types = {item["anomaly_type"] for item in anomalies}
    assert "Dead Zone" in types

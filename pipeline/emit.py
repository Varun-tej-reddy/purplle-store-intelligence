from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from pipeline.tracker import TrackedObject


@dataclass(slots=True)
class TrackState:
    zone_id: str | None
    first_seen_frame: int
    is_confirmed: bool
    first_seen_ms: int
    last_seen_ms: int


class EventEmitter:
    _ENTRY_CONFIRMATION_FRAMES = 150

    def __init__(self, store_id: str, camera_id: str, fps: float) -> None:
        self._store_id = store_id
        self._camera_id = camera_id
        self._fps = fps
        self._states: dict[int, TrackState] = {}

    @staticmethod
    def _ts(frame_idx: int, fps: float) -> datetime:
        seconds = frame_idx / max(fps, 1.0)
        return datetime.fromtimestamp(seconds, tz=timezone.utc)

    def _base_event(
        self,
        visitor_id: str,
        event_type: str,
        timestamp: datetime,
        zone_id: str | None,
        confidence: float,
        dwell_ms: int | None = None,
        metadata: dict | None = None,
    ) -> dict:
        return {
            "event_id": str(uuid4()),
            "store_id": self._store_id,
            "camera_id": self._camera_id,
            "visitor_id": visitor_id,
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "zone_id": zone_id,
            "dwell_ms": dwell_ms,
            "is_staff": False,
            "confidence": round(confidence, 4),
            "metadata": metadata or {},
        }

    def emit_frame(
        self,
        tracked_objects: list[TrackedObject],
        frame_idx: int,
        zone_lookup: dict[int, str | None],
    ) -> list[dict]:
        events: list[dict] = []
        now_ms = int((frame_idx / max(self._fps, 1.0)) * 1000)
        timestamp = self._ts(frame_idx, self._fps)

        active_track_ids = {obj.track_id for obj in tracked_objects}

        for obj in tracked_objects:
            visitor_id = f"{self._camera_id}_visitor_{obj.track_id}"
            zone_id = zone_lookup.get(obj.track_id)
            confidence = obj.detection.confidence
            state = self._states.get(obj.track_id)

            if state is None:
                self._states[obj.track_id] = TrackState(
                    zone_id=zone_id,
                    first_seen_frame=frame_idx,
                    is_confirmed=False,
                    first_seen_ms=now_ms,
                    last_seen_ms=now_ms,
                )
                continue

            if not state.is_confirmed:
                frames_seen = frame_idx - state.first_seen_frame + 1
                state.zone_id = zone_id
                state.last_seen_ms = now_ms
                if frames_seen >= self._ENTRY_CONFIRMATION_FRAMES:
                    state.is_confirmed = True
                    events.append(self._base_event(visitor_id, "ENTRY", timestamp, zone_id, confidence))
                    if zone_id is not None:
                        events.append(self._base_event(visitor_id, "ZONE_ENTER", timestamp, zone_id, confidence))
                        if zone_id == "BILLING":
                            events.append(
                                self._base_event(visitor_id, "BILLING_QUEUE_JOIN", timestamp, zone_id, confidence)
                            )
                continue

            if state.zone_id != zone_id:
                if state.zone_id is not None:
                    dwell_ms = max(now_ms - state.last_seen_ms, 0)
                    events.append(self._base_event(visitor_id, "ZONE_EXIT", timestamp, state.zone_id, confidence))
                    events.append(
                        self._base_event(
                            visitor_id,
                            "ZONE_DWELL",
                            timestamp,
                            state.zone_id,
                            confidence,
                            dwell_ms=dwell_ms,
                        )
                    )
                    if state.zone_id == "BILLING":
                        events.append(
                            self._base_event(visitor_id, "BILLING_QUEUE_ABANDON", timestamp, state.zone_id, confidence)
                        )

                if zone_id is not None:
                    events.append(self._base_event(visitor_id, "ZONE_ENTER", timestamp, zone_id, confidence))
                    if zone_id == "BILLING":
                        events.append(self._base_event(visitor_id, "BILLING_QUEUE_JOIN", timestamp, zone_id, confidence))

                state.zone_id = zone_id

            state.last_seen_ms = now_ms

        for track_id, state in list(self._states.items()):
            if track_id in active_track_ids:
                continue
            if not state.is_confirmed:
                self._states.pop(track_id, None)
                continue

            visitor_id = f"{self._camera_id}_visitor_{track_id}"
            if state.zone_id is not None:
                dwell_ms = max(now_ms - state.last_seen_ms, 0)
                events.append(self._base_event(visitor_id, "ZONE_EXIT", timestamp, state.zone_id, 0.5))
                events.append(self._base_event(visitor_id, "ZONE_DWELL", timestamp, state.zone_id, 0.5, dwell_ms=dwell_ms))
            events.append(self._base_event(visitor_id, "EXIT", timestamp, state.zone_id, 0.5))
            self._states.pop(track_id, None)

        return events

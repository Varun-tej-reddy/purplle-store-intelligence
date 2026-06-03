from __future__ import annotations

from dataclasses import dataclass

from pipeline.detect import Detection


@dataclass(slots=True)
class TrackedObject:
    track_id: int
    detection: Detection


class ByteTrackAdapter:
    """
    Lightweight tracking adapter.

    In production this can be swapped with Ultralytics + native ByteTrack config.
    The current implementation keeps an internal IoU-based association so the rest
    of the event pipeline remains stable and testable.
    """

    def __init__(self, iou_threshold: float = 0.7) -> None:
        self._iou_threshold = iou_threshold
        self._next_id = 1
        self._tracks: dict[int, Detection] = {}

    @staticmethod
    def _iou(a: Detection, b: Detection) -> float:
        x_left = max(a.x1, b.x1)
        y_top = max(a.y1, b.y1)
        x_right = min(a.x2, b.x2)
        y_bottom = min(a.y2, b.y2)
        if x_right <= x_left or y_bottom <= y_top:
            return 0.0
        inter = (x_right - x_left) * (y_bottom - y_top)
        area_a = (a.x2 - a.x1) * (a.y2 - a.y1)
        area_b = (b.x2 - b.x1) * (b.y2 - b.y1)
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    def update(self, detections: list[Detection]) -> list[TrackedObject]:
        assigned_tracks: set[int] = set()
        tracked: list[TrackedObject] = []

        for det in detections:
            best_track = None
            best_iou = 0.0
            for track_id, prev in self._tracks.items():
                if track_id in assigned_tracks:
                    continue
                score = self._iou(det, prev)
                if score > best_iou:
                    best_iou = score
                    best_track = track_id

            if best_track is not None and best_iou >= self._iou_threshold:
                self._tracks[best_track] = det
                assigned_tracks.add(best_track)
                tracked.append(TrackedObject(track_id=best_track, detection=det))
            else:
                track_id = self._next_id
                self._next_id += 1
                self._tracks[track_id] = det
                assigned_tracks.add(track_id)
                tracked.append(TrackedObject(track_id=track_id, detection=det))

        active_ids = {obj.track_id for obj in tracked}
        self._tracks = {k: v for k, v in self._tracks.items() if k in active_ids}
        return tracked

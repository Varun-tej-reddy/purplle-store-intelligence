from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Detection:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_id: int


class YoloV8PersonDetector:
    """YOLOv8 detector constrained to person class (COCO class 0)."""

    def __init__(self, model_path: str = "yolov8n.pt", conf_threshold: float = 0.60) -> None:
        from ultralytics import YOLO

        self._model = YOLO(model_path)
        self._conf_threshold = conf_threshold

    def detect(self, frame) -> list[Detection]:
        results = self._model.predict(frame, conf=self._conf_threshold, classes=[0], verbose=False)
        detections: list[Detection] = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                width = x2 - x1
                height = y2 - y1

                if width < 30 or height < 60:
                    continue

                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                detections.append(
                    Detection(
                        x1,
                        y1,
                        x2,
                        y2,
                        confidence,
                        class_id,
                    )
                )
        return detections

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import cv2

from pipeline.detect import YoloV8PersonDetector
from pipeline.emit import EventEmitter
from pipeline.tracker import ByteTrackAdapter
from pipeline.zones import ZoneAssigner, default_zones

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_video(
    video_path: Path,
    output_path: Path,
    store_id: str,
    camera_id: str,
    model_path: str,
) -> int:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    detector = YoloV8PersonDetector(model_path=model_path)
    tracker = ByteTrackAdapter()
    zone_assigner = ZoneAssigner(default_zones(width, height))
    emitter = EventEmitter(store_id=store_id, camera_id=camera_id, fps=fps)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    frame_idx = 0
    processed_frames = 0
    written = 0
    total_detections = 0
    total_tracks = 0

    with output_path.open("w", encoding="utf-8") as out_f:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % 5 != 0:
                frame_idx += 1
                continue

            detections = detector.detect(frame)

            filtered = []

            for d in detections:
                width = d.x2 - d.x1
                height = d.y2 - d.y1

                if width < 50:
                    continue

                if height < 100:
                    continue

                filtered.append(d)

            detections = filtered

            tracked = tracker.update(detections)
            tracked = [obj for obj in tracked if obj.detection.confidence >= 0.70]
            
            processed_frames += 1

            total_detections += len(detections)
            total_tracks += len(tracked)

            zone_map: dict[int, str | None] = {}
            for obj in tracked:
                d = obj.detection
                center_x = (d.x1 + d.x2) / 2
                foot_y = d.y2
                zone_map[obj.track_id] = zone_assigner.assign(center_x, foot_y)

            frame_events = emitter.emit_frame(tracked, frame_idx, zone_map)
            for event in frame_events:
                out_f.write(json.dumps(event) + "\n")
                written += 1

            frame_idx += 1

    cap.release()
    logger.info(
        "Processed %s frames | processed_frames=%s | detections=%s | tracks=%s | events=%s",
        frame_idx,
        processed_frames,
        total_detections,
        total_tracks,
        written,
    )
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Purplle store intelligence on a CCTV video")
    parser.add_argument("--video", required=True, type=Path, help="Path to input video")
    parser.add_argument("--output", required=True, type=Path, help="Output JSONL path")
    parser.add_argument("--store-id", default="store_1")
    parser.add_argument("--camera-id", default="cam_1")
    parser.add_argument("--model-path", default="yolov8n.pt")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    process_video(args.video, args.output, args.store_id, args.camera_id, args.model_path)


if __name__ == "__main__":
    main()

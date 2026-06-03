#!/usr/bin/env bash
set -euo pipefail

VIDEO_PATH=${1:-"data/videos/sample.mp4"}
OUTPUT_PATH=${2:-"data/output/events.jsonl"}

python -m pipeline.process_video --video "$VIDEO_PATH" --output "$OUTPUT_PATH"

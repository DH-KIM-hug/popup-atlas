#!/bin/sh
# turnip full recording at 1200x900 (absolute --write-movie path, --import first): tools/story/tn_rec.sh <tag> [extra args]
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
G=/Applications/Godot.app/Contents/MacOS/Godot
TAG="$1"; shift
OUT="$ROOT/artifacts/turnip/rec"
mkdir -p "$OUT"
"$G" --headless --path "$ROOT/game" --import > "$OUT/import_$TAG.log" 2>&1 || true
"$G" --path "$ROOT/game" --resolution 1200x900 --fixed-fps 30 --write-movie "$OUT/full_$TAG.avi" -- \
  --tale=turnip --autoplay --quit-on-done --log-sound "$@" > "$OUT/run_$TAG.log" 2>&1 || true
ffmpeg -y -loglevel error -i "$OUT/full_$TAG.avi" -c:v libx264 -crf 28 -preset veryfast -pix_fmt yuv420p -c:a aac -b:a 96k "$OUT/full_$TAG.mp4"
mv "$OUT/full_$TAG.avi" "$HOME/.Trash/tn_full_$TAG.avi"
grep -E "STORY_DONE|VOICE_DUP|CAM_JUMP|OVERLAP_COUNT|SCRIPT ERROR" "$OUT/run_$TAG.log" | head

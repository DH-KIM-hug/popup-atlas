#!/bin/sh
# wolf_goats full recording at 1200x900 (absolute --write-movie path, --import first): tools/story/wg_rec.sh <tag> [extra args]
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
G=/Applications/Godot.app/Contents/MacOS/Godot
TAG="$1"; shift
OUT="$ROOT/artifacts/wolf_goats/rec"
mkdir -p "$OUT"
"$ROOT/tools/story/need_disk.sh" 10 || exit 3
"$G" --headless --path "$ROOT/game" --import > "$OUT/import_$TAG.log" 2>&1 || true
"$G" --path "$ROOT/game" --resolution 1200x900 --fixed-fps 30 --write-movie "$OUT/full_$TAG.avi" -- \
  --tale=wolf_goats --autoplay --quit-on-done --log-sound "$@" > "$OUT/run_$TAG.log" 2>&1 || true
ffmpeg -y -loglevel error -i "$OUT/full_$TAG.avi" -c:v libx264 -crf 24 -preset veryfast -pix_fmt yuv420p -c:a aac -b:a 128k "$OUT/full_$TAG.mp4"
"$ROOT/tools/story/drop_avi.sh" "$OUT/full_$TAG.avi" "$OUT/full_$TAG.mp4"
grep -E "STORY_DONE|VOICE_DUP|CAM_JUMP|OVERLAP_COUNT|SCRIPT ERROR" "$OUT/run_$TAG.log" | head

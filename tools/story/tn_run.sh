#!/bin/sh
# turnip: import, then a full autoplay run WITHOUT the movie maker (quick checks): tools/story/tn_run.sh <tag> [args]
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
G=/Applications/Godot.app/Contents/MacOS/Godot
TAG="$1"; shift
OUT="$ROOT/artifacts/turnip/rec"
mkdir -p "$OUT"
"$G" --headless --path "$ROOT/game" --import > "$OUT/import_$TAG.log" 2>&1 || true
"$G" --path "$ROOT/game" --resolution 1200x900 --fixed-fps 30 -- --tale=turnip --autoplay --quit-on-done --log-sound "$@" \
  > "$OUT/run_$TAG.log" 2>&1 || true
grep -E "STORY_DONE|VOICE_DUP|CAM_JUMP|OVERLAP_COUNT|SCRIPT ERROR|SPEAKER_OFF=" "$OUT/run_$TAG.log" | head

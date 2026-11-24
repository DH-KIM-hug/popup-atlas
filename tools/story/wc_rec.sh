#!/bin/sh
# witch_candy full recording (gate): 1200x900, absolute --write-movie path, --import first, --log-sound --log-track,
# --quit-on-done + a frame cap. Run through with_godot.sh:  tools/story/with_godot.sh tools/story/wc_rec.sh <tag> [extra]
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
G=/Applications/Godot.app/Contents/MacOS/Godot
TAG="$1"; shift
OUT="$ROOT/artifacts/witch_candy/rec"
mkdir -p "$OUT"
"$ROOT/tools/story/need_disk.sh" 10 || exit 3
"$G" --headless --path "$ROOT/game" --import > "$OUT/import_$TAG.log" 2>&1 || true
"$G" --path "$ROOT/game" --resolution 1200x900 --fixed-fps 30 --write-movie "$OUT/full_$TAG.avi" --quit-after 18000 -- \
  --tale=witch_candy --autoplay --quit-on-done --log-sound --log-track "$@" > "$OUT/$TAG.log" 2>&1 || true
ffmpeg -y -loglevel error -i "$OUT/full_$TAG.avi" -c:v libx264 -crf 24 -preset veryfast -pix_fmt yuv420p -c:a aac -b:a 128k "$OUT/full_$TAG.mp4"
"$ROOT/tools/story/drop_avi.sh" "$OUT/full_$TAG.avi" "$OUT/full_$TAG.mp4"
grep -E "STORY_DONE|VOICE_DUP|CAM_JUMP|OVERLAP_COUNT|SCRIPT ERROR|Failed loading" "$OUT/$TAG.log" | head

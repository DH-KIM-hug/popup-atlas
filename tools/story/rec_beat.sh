#!/bin/sh
# Record one beat with the movie maker: tools/story/rec_beat.sh TALE BEAT SECONDS OUT.mp4 [crf]
# (30 fps fixed, autoplay; the AVI is deleted after encoding). One Godot process per project at a time.
set -e
TALE="$1"; BEAT="$2"; SEC="$3"; OUT="$4"; CRF="${5:-24}"
G=/Applications/Godot.app/Contents/MacOS/Godot
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AVI="${OUT%.mp4}.avi"
FR=$(python3 -c "print(int(float('$SEC')*30))")
"$G" --path "$ROOT/game" --resolution 1366x1024 --fixed-fps 30 --write-movie "$AVI" --quit-after "$FR" -- \
  --tale="$TALE" --beat="$BEAT" --autoplay > "${OUT%.mp4}.log" 2>&1 || true
ffmpeg -y -loglevel error -i "$AVI" -c:v libx264 -crf "$CRF" -preset veryfast -pix_fmt yuv420p -c:a aac "$OUT"
rm -f "$AVI"
grep -E "SCRIPT ERROR|^ERROR" "${OUT%.mp4}.log" | head -5 || true
echo "$OUT"

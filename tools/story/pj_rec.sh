#!/bin/sh
# patjuk: record a beat (or the full tale) with the movie maker at 1200x900 (absolute paths; run via with_godot.sh).
#   tools/story/with_godot.sh tools/story/pj_rec.sh <beat|full> <seconds> </abs/out.mp4> [extra godot user args]
set -e
BEAT="$1"; SEC="$2"; OUT="$3"; shift 3
G=/Applications/Godot.app/Contents/MacOS/Godot
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AVI="${OUT%.mp4}.avi"
FR=$(python3 -c "print(int(float('$SEC')*30))")
"$G" --headless --path "$ROOT/game" --import > "${OUT%.mp4}_import.log" 2>&1 || true
if [ "$BEAT" = "full" ]; then B=""; Q="--quit-on-done"; else B="--beat=$BEAT"; Q=""; fi
"$G" --path "$ROOT/game" --resolution 1200x900 --fixed-fps 30 --write-movie "$AVI" --quit-after "$FR" -- \
  --tale=patjuk $B --autoplay $Q --log-sound "$@" > "${OUT%.mp4}.log" 2>&1 || true
ffmpeg -y -loglevel error -i "$AVI" -c:v libx264 -crf 31 -preset slow -pix_fmt yuv420p -c:a aac -b:a 96k "$OUT"
mv "$AVI" "$HOME/.Trash/pj_$(basename "$AVI" .avi)_$(date +%s).avi"
grep -E "SCRIPT ERROR|^ERROR" "${OUT%.mp4}.log" | head -8 || true
echo "$OUT"

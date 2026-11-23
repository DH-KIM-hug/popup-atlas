#!/bin/sh
# Record one beat for a gate-style check (wave 1): 1200x900, 30 fps fixed, autoplay, --log-track --log-sound.
#   tools/story/with_godot.sh tools/story/w1_beat.sh TALE BEAT SECONDS /ABS/OUT.mp4 [extra user args...]
# Writes OUT.mp4 + OUT.log; the AVI goes to ~/.Trash after encoding.
set -e
TALE="$1"; BEAT="$2"; SEC="$3"; OUT="$4"; shift 4
G=/Applications/Godot.app/Contents/MacOS/Godot
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AVI="${OUT%.mp4}.avi"
FR=$(python3 -c "print(int(float('$SEC')*30))")
"$G" --path "$ROOT/game" --resolution 1200x900 --fixed-fps 30 --write-movie "$AVI" --quit-after "$FR" -- \
  --tale="$TALE" --beat="$BEAT" --autoplay --log-track --log-sound "$@" > "${OUT%.mp4}.log" 2>&1 || true
ffmpeg -y -loglevel error -i "$AVI" -vf "scale=1200:900" -c:v libx264 -crf 24 -preset veryfast -pix_fmt yuv420p -c:a aac "$OUT"
mv "$AVI" "$HOME/.Trash/$(basename "$AVI" .avi)_$(date +%s).avi"
grep -E "SCRIPT ERROR|Parse Error|^ERROR" "${OUT%.mp4}.log" | head -5 || true
echo "$OUT"

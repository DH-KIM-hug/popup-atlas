#!/bin/sh
# Full gate recording of one tale: --import first, 1200x900, 30 fps fixed, absolute movie path, autoplay to the end
# with a frame cap (the shared Godot slot is never held forever), --log-sound --log-track.
#   tools/story/with_godot.sh tools/story/full_rec.sh TALE /ABS/OUT.mp4 MAX_SECONDS [extra user args...]
# Writes OUT.mp4 (crf 28; re-encode smaller if > 30 MB) + OUT.log; the AVI goes to ~/.Trash after encoding.
set -e
TALE="$1"; OUT="$2"; SEC="$3"; shift 3
case "$OUT" in /*) ;; *) echo "OUT must be absolute"; exit 2;; esac
G=/Applications/Godot.app/Contents/MacOS/Godot
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
AVI="${OUT%.mp4}.avi"
LOG="${OUT%.mp4}.log"
FR=$(python3 -c "print(int(float('$SEC')*30))")
"$G" --headless --path "$ROOT/game" --import > "${OUT%.mp4}_import.log" 2>&1 || true
"$G" --path "$ROOT/game" --resolution 1200x900 --fixed-fps 30 --write-movie "$AVI" --quit-after "$FR" -- \
  --tale="$TALE" --autoplay --quit-on-done --log-sound --log-track "$@" > "$LOG" 2>&1 || true
ffmpeg -y -loglevel error -i "$AVI" -vf "scale=1200:900" -c:v libx264 -crf 28 -preset veryfast -pix_fmt yuv420p \
  -c:a aac -b:a 96k "$OUT"
mv "$AVI" "$HOME/.Trash/$(basename "$AVI" .avi)_$(date +%s).avi"
grep -E "STORY_DONE|SCRIPT ERROR|Failed loading" "$LOG" | head -5 || true
ls -la "$OUT"

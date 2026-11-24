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
# frozen video (the movie maker sometimes repeats frames for seconds while the log runs on: turnip t2 2026-11-24, 36
# freezes, an 11 MB file instead of 19 MB); 0 expected, re-record otherwise
echo "FROZEN_VIDEO $(ffmpeg -i "$OUT" -vf "scale=300:225,freezedetect=n=0.0005:d=2.5" -map 0:v -f null - 2>&1 | grep -c freeze_start)"
ls -la "$OUT"

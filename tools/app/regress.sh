#!/bin/sh
# Autoplay regression after shared-engine edits: tools/story/with_godot.sh tools/app/regress.sh <out_dir> [tale ...]
# (default witch_candy sun_wind; real time, windowed 1200x900, no movie) -> STORY_DONE / VOICE_DUP / check_lines.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:?out dir}"; shift
[ $# -eq 0 ] && set -- witch_candy sun_wind
mkdir -p "$OUT"
G=/Applications/Godot.app/Contents/MacOS/Godot
"$G" --headless --path "$ROOT/game" --import > "$OUT/import.log" 2>&1 || true
for t in "$@"; do
  "$G" --path "$ROOT/game" --resolution 1200x900 -- --tale="$t" --autoplay --quit-on-done > "$OUT/run_$t.log" 2>&1 &
  p=$!; ( sleep 900; kill $p 2>/dev/null ) & w=$!; wait $p; kill $w 2>/dev/null
  echo "== $t"; grep -E "STORY_DONE|VOICE_DUP=|SCRIPT ERROR|Parse Error" "$OUT/run_$t.log" | head -5
  python3 "$ROOT/tools/story/check_lines.py" "$t" "$OUT/run_$t.log" | tail -2
done

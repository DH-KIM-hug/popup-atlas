#!/bin/sh
# wolf_goats phase 1: no-movie autoplay regression of the other tales after shared engine edits (one Godot at a time)
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
G=/Applications/Godot.app/Contents/MacOS/Godot
OUT="$ROOT/artifacts/wolf_goats/regress"
mkdir -p "$OUT"
for t in sun_wind three_pigs witch_candy sunmoon; do
  "$G" --path "$ROOT/game" --resolution 1200x900 --fixed-fps 30 -- --tale=$t --autoplay --quit-on-done > "$OUT/$t.log" 2>&1
  echo "$t: $(grep -E 'STORY_DONE' "$OUT/$t.log" | cut -c1-90) $(grep -c 'SCRIPT ERROR' "$OUT/$t.log") script errors"
  python3 "$ROOT/tools/story/check_lines.py" $t "$OUT/$t.log" | tail -1
done

#!/bin/sh
# House bodies (2026-11-23): no-movie autoplay of every tale, one Godot at a time (holds the slot per tale):
#   tools/story/house_regress.sh OUT_DIR [tales]
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
G=/Applications/Godot.app/Contents/MacOS/Godot
OUT="$1"; shift
TALES="${*:-sun_wind three_pigs witch_candy sunmoon wolf_goats patjuk turnip}"
mkdir -p "$OUT"
for t in $TALES; do
  "$ROOT/tools/story/with_godot.sh" "$G" --path "$ROOT/game" --resolution 1200x900 --fixed-fps 30 -- --tale=$t --autoplay \
    --quit-on-done --log-sound > "$OUT/$t.log" 2>&1
  echo "== $t: $(grep -E 'STORY_DONE' "$OUT/$t.log" | cut -c1-140)"
  grep -E "VOICE_DUP|CAM_JUMP|CAM_JERK|SPEAKER_OFF=|OVERLAP_COUNT|OCCLUDE_COUNT" "$OUT/$t.log" | tail -4
  echo "   script errors: $(grep -c 'SCRIPT ERROR' "$OUT/$t.log")  SET_CHECK nonzero: $(grep 'SET_CHECK' "$OUT/$t.log" | grep -vc 'road=0 water=0')"
  python3 "$ROOT/tools/story/check_lines.py" $t "$OUT/$t.log" | tail -1
done

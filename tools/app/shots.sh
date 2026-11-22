#!/bin/sh
# App-shell screenshots, iPad landscape (1200x900) + portrait (675x900: 3:4, a 900x1200 window does not fit this
# Mac screen; 675 pt is narrower than any iPad portrait, so it is the strict case), every screen.
#   tools/story/with_godot.sh tools/app/shots.sh <out_dir>
# then: python3 tools/app/shots_sheet.py <out_dir>
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:?out dir}"
mkdir -p "$OUT"
G=/Applications/Godot.app/Contents/MacOS/Godot
ST="$OUT/state_named.json"
printf '{"names": {"witch_candy": {"A": "지우", "on": true, "done": false, "got": {}}}}' > "$ST"
run() {  # name size secs args...
  n=$1; sz=$2; at=$3; shift 3
  "$G" --path "$ROOT/game" --resolution "$sz" -- --app-shot --app-capture="$OUT/$n.png" --app-capture-at="$at" "$@" > "$OUT/$n.log" 2>&1 &
  p=$!; ( sleep 90; kill $p 2>/dev/null ) & w=$!; wait $p; kill $w 2>/dev/null
  grep -E "SCRIPT ERROR|Parse Error|APP_CAPTURE" "$OUT/$n.log" | head -3
}
for o in ${SHOTS_ORIENT:-land:1200x900 port:675x900}; do
  k=${o%%:*}; sz=${o#*:}
  run ${k}_01_shelf "$sz" 5 --app-fresh
  run ${k}_02_shelf_locked "$sz" 5 --app-fresh --app-locked
  run ${k}_03_locked_card "$sz" 5 --app-fresh --app-locked --app-screen=locked
  run ${k}_04_gate "$sz" 5 --app-fresh --app-screen=gate
  run ${k}_05_menu "$sz" 5 --app-fresh --app-locked --app-screen=menu
  run ${k}_06_store "$sz" 5 --app-fresh --app-screen=store
  run ${k}_07_store_locked "$sz" 5 --app-fresh --app-locked --app-screen=store
  run ${k}_08_sheet "$sz" 5 --app-fresh --app-locked --app-screen=sheet
  run ${k}_09_names "$sz" 5 --app-state="$ST" --app-screen=names
  run ${k}_10_names_locked "$sz" 5 --app-fresh --app-locked --app-screen=names
  run ${k}_11_settings "$sz" 5 --app-fresh --app-screen=settings
  run ${k}_12_info "$sz" 5 --app-fresh --app-screen=info
  run ${k}_13_in_story "$sz" 16 --app-fresh --shelf-pick=witch_candy
done

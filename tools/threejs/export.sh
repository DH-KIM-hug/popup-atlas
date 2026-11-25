#!/bin/sh
# Export one tale for the three.js player (docs/THREEJS.md): the real runner in Godot, autoplay to the end.
#   tools/story/with_godot.sh tools/threejs/export.sh TALE [MAX_SECONDS]
# -> build/threejs_dump/TALE/{scene.json,geo.bin,tex/} + export.log; Godot reference frames every 3 s in
#    artifacts/threejs/TALE/godot_ref/. Then: python3 tools/threejs/pack_tale.py TALE
set -e
TALE="$1"; SEC="${2:-600}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
G=/Applications/Godot.app/Contents/MacOS/Godot
OUT="$ROOT/build/threejs_dump/$TALE"
REF="$ROOT/artifacts/threejs/$TALE/godot_ref"
"$ROOT/tools/story/need_disk.sh" 8 || exit 3
mkdir -p "$OUT" "$REF"
FR=$(python3 -c "print(int(float('$SEC')*30) + 300)")
"$G" --path "$ROOT/game" --resolution 1366x1024 --fixed-fps 30 --quit-after "$FR" \
  --script res://../tools/threejs/export_tale.gd -- \
  --tale="$TALE" --autoplay --log-sound --x-out="$OUT" --x-ref="$REF" --x-ref-every=90 --x-max="$SEC" \
  > "$OUT/export.log" 2>&1 || true
grep -E "TALE_EXPORT|STORY_DONE|SCRIPT ERROR|Parse Error" "$OUT/export.log" | head -5

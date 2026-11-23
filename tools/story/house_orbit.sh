#!/bin/sh
# House orbit audit for one tale beat (2026-11-23): tools/story/house_orbit.sh TALE BEAT OUT_DIR [houses,comma] [tmpl N] [kit presets,comma]
# Copies tools/story/house_orbit.gd into game/.agent_out and runs it (windowed 1200x900) holding the Godot slot.
# Then: python3 tools/story/house_audit.py OUT_DIR TALE -> OUT_DIR/<tale>_audit.jpg + seam counts.
set -e
TALE="$1"; BEAT="$2"; OUT="$3"; HOUSES="${4:-}"; TMPL="${5:-3}"; KITS="${6:-}"
G=/Applications/Godot.app/Contents/MacOS/Godot
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
mkdir -p "$ROOT/game/.agent_out" "$OUT"
cp "$ROOT/tools/story/house_orbit.gd" "$ROOT/game/.agent_out/house_orbit.gd"
"$ROOT/tools/story/with_godot.sh" "$G" --path "$ROOT/game" --resolution 1200x900 --script res://.agent_out/house_orbit.gd -- \
  --tale="$TALE" --beat="$BEAT" --fixed --mute --nosubs --orbit-out="$OUT" --houses="$HOUSES" --tmpl="$TMPL" --kit="$KITS" \
  > "$OUT/${TALE}_orbit.log" 2>&1 || true
grep -E "ORBIT|SCRIPT ERROR|^ERROR" "$OUT/${TALE}_orbit.log" | cut -c1-300 | head -40

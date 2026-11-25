#!/bin/sh
# Side-by-side sheet: the Godot gate video vs the three.js player at the same story times.
#   tools/threejs/compare_gate.sh <gate.mp4> <player url (…/?tale=X)> <out.jpg> t1,t2,...
# Godot frames come from the gate video (ffmpeg -ss), three.js frames from tools/threejs/shot.mjs (seek + hold) at
# 1366x1024 (4:3 like the gate). Both recordings run the same autoplay at 30 fps fixed, so story times line up
# (the export's BEAT times match the gate log within 0.1 s).
set -e
MP4="$1"; URL="$2"; OUT="$3"; TS="$4"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TMP="$(dirname "$OUT")/frames_$(basename "$OUT" .jpg)"
mkdir -p "$TMP"
node "$ROOT/tools/threejs/shot.mjs" "$URL" "$TMP" "$TS" chromium 1366x1024 > "$TMP/shot.log" 2>&1
ARGS=""
for t in $(echo "$TS" | tr ',' ' '); do
  g="$TMP/godot_t$(printf '%05.1f' "$t").jpg"
  ffmpeg -loglevel error -y -ss "$t" -i "$MP4" -frames:v 1 -q:v 3 "$g"
  ARGS="$ARGS t=${t}s|$g|$TMP/three_t$(printf '%05.1f' "$t").png"
done
# shellcheck disable=SC2086
python3 "$ROOT/tools/threejs/compare.py" "$OUT" $ARGS

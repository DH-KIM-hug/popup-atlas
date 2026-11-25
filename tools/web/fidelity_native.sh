#!/bin/sh
# Native side of the web-vs-native comparison (docs/WEB_BUILD.md, "Fidelity check").
#   tools/web/fidelity_native.sh <outdir> [tale filter, comma list]
# For every moment in tools/web/fidelity_moments.json: one movie-maker run (1366x1024, 30 fps, autoplay, muted,
# frame cap = last t + 1 s), each holding the Godot slot on its own (tools/story/with_godot.sh), then frames at each t
# go to <outdir>/<tale>_<beat>_<t>.png. The AVI is deleted once its frames are out.
# Env: GFLAGS = extra Godot flags (e.g. "--rendering-method gl_compatibility" to see the web renderer on the desktop),
#      UARGS = extra user args after -- (e.g. "--web-look": the web-only look overrides of LookRig).
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$(mkdir -p "$1" && cd "$1" && pwd)"; ONLY="$2"
G=/Applications/Godot.app/Contents/MacOS/Godot
mkdir -p "$OUT"
python3 - "$ROOT/tools/web/fidelity_moments.json" "$ONLY" > "$OUT/.moments" <<'EOF'
import json, sys
only = [x for x in sys.argv[2].split(",") if x]
for m in json.load(open(sys.argv[1]))["moments"]:
    if not only or m["tale"] in only:
        print(m["tale"], m["beat"], ",".join(str(t) for t in m["t"]))
EOF
while read -r TALE BEAT TS; do
  LAST=$(echo "$TS" | tr ',' '\n' | sort -n | tail -1)
  FR=$(( (LAST + 8) * 30 ))  # + room for the build before the first line
  AVI="$OUT/${TALE}_${BEAT}.avi"
  # shellcheck disable=SC2086
  "$ROOT/tools/story/slot_wait.sh" "$G" --path "$ROOT/game" --resolution 1366x1024 --fixed-fps 30 $GFLAGS \
    --write-movie "$AVI" --quit-after "$FR" -- --tale="$TALE" --beat="$BEAT" --autoplay --mute $UARGS \
    < /dev/null > "$OUT/${TALE}_${BEAT}_native.log" 2>&1 || true
  # anchor: the beat's first spoken LINE (its clock = movie seconds: fixed 30 fps from the first frame)
  B0=$(awk -v b="BEAT $BEAT " 'index($0, b) == 1 {on = 1} on && /^LINE / {sub(/.* t=/, ""); print $1; exit}' "$OUT/${TALE}_${BEAT}_native.log")
  B0=${B0:-0}
  for T in $(echo "$TS" | tr ',' ' '); do
    ffmpeg -nostdin -v error -y -ss "$(python3 -c "print($T + $B0)")" -i "$AVI" -frames:v 1 "$OUT/${TALE}_${BEAT}_${T}.png"
  done
  rm -f -- "$AVI"  # frames are out; delete for good (no Trash: it stays on the disk)
  echo "$TALE/$BEAT: $TS (beat clock $B0)"
done < "$OUT/.moments"

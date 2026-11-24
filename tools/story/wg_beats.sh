#!/bin/sh
# wolf_goats: record several beats in one Godot-slot hold (each like w1_beat.sh: 1200x900, --log-track --log-sound).
#   tools/story/with_godot.sh tools/story/wg_beats.sh /ABS/OUTDIR TAG beat:sec [beat:sec ...]
D="$1"; TAG="$2"; shift 2
mkdir -p "$D"
for bs in "$@"; do
  b="${bs%%:*}"; s="${bs##*:}"
  sh "$(dirname "$0")/w1_beat.sh" wolf_goats "$b" "$s" "$D/${TAG}_$b.mp4"
done

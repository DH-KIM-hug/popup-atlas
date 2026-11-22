#!/bin/sh
# Run one command holding the project's Godot slot (one Godot process per project at a time).
#   tools/story/with_godot.sh <command ...>      e.g. tools/story/with_godot.sh tools/story/rec_beat.sh sunmoon road 20 out.mp4
# The lock is a directory (atomic mkdir); it waits while another agent holds it and frees it on exit / Ctrl-C.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOCK="$ROOT/.godot_slot.lock"
while ! mkdir "$LOCK" 2>/dev/null; do
  # stale lock: holder pid gone
  if [ -f "$LOCK/pid" ] && ! kill -0 "$(cat "$LOCK/pid")" 2>/dev/null; then rm -f "$LOCK/pid"; rmdir "$LOCK" 2>/dev/null; continue; fi
  sleep 3
done
echo $$ > "$LOCK/pid"
trap 'rm -f "$LOCK/pid"; rmdir "$LOCK" 2>/dev/null' EXIT INT TERM
"$@"

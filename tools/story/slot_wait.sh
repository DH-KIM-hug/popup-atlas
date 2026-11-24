#!/bin/sh
# Wait for the shared Godot slot with a fast poll (0.2 s; with_godot.sh's 3 s poll loses the race), then take it
# through with_godot.sh:   tools/story/slot_wait.sh <command ...>
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOCK="$ROOT/.godot_slot.lock"
while [ -d "$LOCK" ]; do
  if [ -f "$LOCK/pid" ] && ! kill -0 "$(cat "$LOCK/pid")" 2>/dev/null; then break; fi
  sleep 0.2
done
exec "$ROOT/tools/story/with_godot.sh" "$@"

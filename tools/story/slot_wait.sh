#!/bin/sh
# Take the shared Godot slot (same lock dir as tools/story/with_godot.sh) with a 0.2 s mkdir poll and run one command
# holding it:   tools/story/slot_wait.sh <command ...>
# with_godot.sh polls every 3 s and loses every race against agents polling faster (tooling.md "One Godot per
# project"); this one tries the mkdir itself on every poll and sets the trap only once the lock is its own.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOCK="$ROOT/.godot_slot.lock"
while ! mkdir "$LOCK" 2>/dev/null; do
  if [ -f "$LOCK/pid" ] && ! kill -0 "$(cat "$LOCK/pid" 2>/dev/null)" 2>/dev/null; then rm -f "$LOCK/pid"; rmdir "$LOCK" 2>/dev/null; continue; fi
  sleep 0.2
done
echo $$ > "$LOCK/pid"
trap 'rm -f "$LOCK/pid"; rmdir "$LOCK" 2>/dev/null' EXIT INT TERM
cd "$ROOT" && "$@"

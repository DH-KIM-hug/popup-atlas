#!/bin/sh
# wolf_goats: reseed script.json via a temp file, show the diff size, then copy (seed_script.py --out does not overwrite
# an existing file without --force, so a stale temp silently survives: always --force into the temp).
cd "$(dirname "$0")/../.." || exit 1
T=$(mktemp -t wgseed).json
python3 tools/story/seed_script.py --tale wolf_goats --out "$T" --no-audio --force >/dev/null || exit 1
echo "diff lines: $(diff <(python3 -m json.tool game/stories/wolf_goats/script.json) <(python3 -m json.tool "$T") | grep -c '^[<>]')"
cp "$T" game/stories/wolf_goats/script.json
rm -f "$T"

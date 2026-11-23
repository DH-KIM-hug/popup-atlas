#!/bin/sh
# rapunzel: reseed script.json via a temp file, show the diff size, then copy (seed_script.py --out does not overwrite
# an existing file without --force, so a stale temp silently survives: always --force into the temp).
cd "$(dirname "$0")/../.." || exit 1
T=$(mktemp -t rpseed).json
python3 tools/story/seed_script.py --tale rapunzel --out "$T" --no-audio --force >/dev/null || exit 1
echo "diff lines: $(diff <(python3 -m json.tool game/stories/rapunzel/script.json) <(python3 -m json.tool "$T") | grep -c '^[<>]')"
cp "$T" game/stories/rapunzel/script.json
rm -f "$T"

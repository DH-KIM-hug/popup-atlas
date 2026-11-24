#!/bin/sh
# witch_candy: reseed from tools/story/tales/witch_candy.py into a temp (--force), then copy every top-level key
# EXCEPT "lines" into script.json (a full reseed re-reads 톡톡 and swaps the hand-fixed name-piece / trimmed clips).
cd "$(dirname "$0")/../.." || exit 1
T=$(mktemp -t wcseed).json
python3 tools/story/seed_script.py --tale witch_candy --out "$T" --no-audio --force >/dev/null || exit 1
python3 - "$T" <<'PY'
import json, sys
p = "game/stories/witch_candy/script.json"
a = json.load(open(p, encoding="utf-8")); b = json.load(open(sys.argv[1], encoding="utf-8"))
ch = [k for k in b if k != "lines" and a.get(k) != b[k]]
for k in b:
    if k != "lines":
        a[k] = b[k]
open(p, "w", encoding="utf-8").write(json.dumps(a, ensure_ascii=False, indent=1) + "\n")
print("changed keys:", ch)
PY
rm -f "$T"

#!/usr/bin/env python3
"""Add (or refresh) ONE atlas sheet in the shared library without rebuilding the whole catalog (2026-11-19, witch_candy).

  python3 tools/atlas/add_sheet.py <sheet> [--join N]

1. slices art_src/atlas/raw/<sheet>.png into game/art/atlas/<sheet>/ (tools/atlas/slice_atlas.py),
2. restores pixels the magenta keyer cleared inside sprites (tools/atlas/fill_holes.py: purple candies, ribbons),
3. optional "merge" groups from the labels file: pieces composited back into one card (a spiral the slicer split),
4. replaces this sheet's entries in game/art/atlas/catalog.json from tools/atlas/labels/<sheet>.json (same format as
   tools/atlas/build_catalog.py; unlabelled / "drop" pieces are deleted from the sheet folder, raw stays).
build_catalog.py rebuilds everything and moves unlabelled pieces of every sheet to rejects; this touches one sheet only.
Use story_* categories for story set pieces so the meadow template's category queries (sun_wind layout) don't change.
"""
import json, os, subprocess, sys
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
sheet = sys.argv[1]
join = sys.argv[sys.argv.index("--join") + 1] if "--join" in sys.argv else "5"
out = f"game/art/atlas/{sheet}"
subprocess.run([sys.executable, "tools/atlas/slice_atlas.py", f"art_src/atlas/raw/{sheet}.png", "--out", "game/art/atlas",
                "--join", join], check=True)
subprocess.run([sys.executable, "tools/atlas/fill_holes.py", f"art_src/atlas/raw/{sheet}.png", out], check=True)
L = json.load(open(f"tools/atlas/labels/{sheet}.json"))
meta = json.load(open(f"{out}/_slices.json"))
sl = meta["sprites"]
for grp in L.get("merge", []):  # ["10", "11"]: composite the later pieces into the first (raw-sheet positions)
    ms = [sl[int(k)] for k in grp]
    x0 = min(m["bbox"][0] for m in ms) - 4
    y0 = min(m["bbox"][1] for m in ms) - 4
    x1 = max(m["bbox"][2] for m in ms) + 4
    y1 = max(m["bbox"][3] for m in ms) + 4
    c = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    for m in ms:
        im = Image.open(f"{out}/{m['id']}.webp").convert("RGBA")
        c.alpha_composite(im, (m["bbox"][0] - 4 - x0, m["bbox"][1] - 4 - y0))
    c.save(f"{out}/{ms[0]['id']}.webp", "WEBP", lossless=True, quality=100, method=6)
    ms[0]["bbox"] = [x0 + 4, y0 + 4, x1 - 4, y1 - 4]
    ms[0]["size"] = [x1 - x0, y1 - y0]
    for m in ms[1:]:
        L["items"][sl.index(m).__format__("02d")] = "drop"
json.dump(meta, open(f"{out}/_slices.json", "w"), indent=1)
cat = [e for e in json.load(open("game/art/atlas/catalog.json")) if e.get("sheet") != sheet]
n = 0
for k, m in enumerate(sl):
    it = L["items"].get(f"{k:02d}", "drop")
    src = f"{out}/{m['id']}.webp"
    if it == "drop":
        for p in (src, src + ".import"):
            if os.path.exists(p):
                os.remove(p)
        continue
    label, category, h, cross = it[:4]
    ov = it[4] if len(it) > 4 else {}
    cat.append({"id": m["id"], "path": f"art/atlas/{sheet}/{m['id']}.webp", "sheet": sheet, "category": category,
                "label": label, "height_units": h, "cross_slot": bool(cross), "biome": ov.get("biome", L["biome"]),
                "season": ov.get("season", L.get("season", "any")),
                "tags": sorted(set(L.get("tags", []) + ov.get("tags", []))), "px": m["size"]})
    n += 1
json.dump(cat, open("game/art/atlas/catalog.json", "w"), indent=1, ensure_ascii=False)
print(sheet, n, "cards;", len(cat), "in catalog")

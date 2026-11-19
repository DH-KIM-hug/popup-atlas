#!/usr/bin/env python3
"""Slice a drawn cycle sheet (art_src/cast/raw/<sheet>.png) into catalogued flipbook frames of a cast skin.

  python3 tools/cast/add_cycles.py <sheet> <skin> <cycle>:<n>:<view> [<cycle>:<n>:<view> ...] [--h 0.97]

Pieces are taken left to right; every frame of one sheet is padded to one canvas (bottom-centre aligned, so the
flipbook never jumps); each becomes game/art/cast/cast_<skin>_<cycle>_<i>.webp with catalog fields cycle / frame /
view, height_units = the skin's calm figure × --h. CastPuppet plays a cycle as a flipbook advanced by ground distance.
"""
import json, os, subprocess, sys
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
args = [a for a in sys.argv[1:] if not a.startswith("--")]
hk = float(sys.argv[sys.argv.index("--h") + 1]) if "--h" in sys.argv else 0.97
if "--h" in sys.argv:
    args.remove(sys.argv[sys.argv.index("--h") + 1])
sheet, skin, plan = args[0], args[1], [p.split(":") for p in args[2:]]
subprocess.run([sys.executable, "tools/atlas/slice_atlas.py", f"art_src/cast/raw/{sheet}.png", "--out", "art_src/cast/slices"], check=True)
sl = sorted(json.load(open(f"art_src/cast/slices/{sheet}/_slices.json"))["sprites"], key=lambda m: m["bbox"][0])
frames = [(c, i, v) for c, n, v in plan for i in range(int(n))]
assert len(sl) == len(frames), f"{sheet}: {len(sl)} pieces, plan wants {len(frames)}"
ims = [Image.open(f"art_src/cast/slices/{sheet}/{m['id']}.webp").convert("RGBA") for m in sl]
W, H = max(i.width for i in ims), max(i.height for i in ims)
cat = json.load(open("game/art/cast/catalog.json"))
calm = next(e for e in cat if e["id"] == f"cast_{skin}_calm")
for im, (cyc, fr, view) in zip(ims, frames):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    c.alpha_composite(im, ((W - im.width) // 2, H - im.height))
    cid = f"cast_{skin}_{cyc}_{fr}"
    c.save(f"game/art/cast/{cid}.webp", "WEBP", lossless=True, quality=100, method=6)
    e = {"id": cid, "path": f"art/cast/{cid}.webp", "sheet": sheet, "category": "cast", "role": skin,
         "variant": f"{cyc}_{fr}", "pose": f"{cyc}_{fr}", "view": view, "facing": {"side": "right"}.get(view, view),
         "label": f"{cyc} frame {fr} (drawn cycle)", "height_units": round(calm["height_units"] * hk, 3),
         "cross_slot": False, "biome": "any", "season": "any", "tags": [skin, "three_pigs", "cycle"], "px": [W, H],
         "hanging": False, "skin": skin, "parts": {}, "cycle": cyc, "frame": fr}
    cat = [q for q in cat if q["id"] != cid] + [e]
json.dump(cat, open("game/art/cast/catalog.json", "w"), ensure_ascii=False, indent=1)
print(sheet, "->", len(frames), "frames")

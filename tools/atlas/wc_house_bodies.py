#!/usr/bin/env python3
"""witch_candy v3 (2026-11-20, user: "사선으로 돼 있으니까 집도 집처럼 보여줘야"): bodies for the village houses, which stand
turned toward the road, so from the street camera a flat front read as a cut-out.

  python3 tools/atlas/wc_house_bodies.py [--sheet artifacts/witch_candy/house_bodies.png]

Per house (story_wc_houses_a/b_*):
- the wall / roof split row (automatic: the first row above the wall where the silhouette widens to the eaves; OVERRIDE
  for irregular fronts), written as two fold bands in <sheet>/stages/stages.json (the SetPiece `box` needs bands),
- `side_file`: the house's own wall cropped (a window-wide strip of its left wall, the door excluded) for its side
  walls and back,
- `roof_file`: a strip of its own roof print for the roof slopes,
- `gable`: eave left / right and ridge points (facade px) so SetPiece builds two roof slopes running back over the box.
Contact sheet: each front with the roof line, eaves, ridge and the side / roof crops.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ATLAS = os.path.join(ROOT, "game", "art", "atlas")
# roof line (facade px row) where the automatic split misreads the front (towers, a pumpkin house, a porch)
OVERRIDE = {"story_wc_houses_a_02": 268, "story_wc_houses_b_05": 245}


def opaque(im):
    return np.asarray(im)[..., 3] > 128


def roof_row(op):
    ys = np.where(op.any(1))[0]
    top, base = int(ys[0]), int(ys[-1]) + 1
    w = op.sum(1).astype(float)
    xs = [np.where(op[y])[0] for y in range(op.shape[0])]
    span = np.array([(x[-1] - x[0] + 1) if len(x) else 0 for x in xs], float)
    lo = base - int((base - top) * 0.45)
    wall = float(np.median(span[lo:base - 4]))
    y = lo
    while y > top + 4:
        if span[y] > wall * 1.06 or span[y] < wall * 0.8:
            break
        y -= 1
    return y + 1, wall, top, base, span


def build(cid, e):
    path = os.path.join(ROOT, "game", e["path"])
    im = Image.open(path).convert("RGBA")
    op = opaque(im)
    ry, wall_w, top, base, span = roof_row(op)
    ry = OVERRIDE.get(cid, ry)
    h, w = op.shape
    # wall extents at the lower wall
    row = op[min(base - 6, ry + (base - ry) * 2 // 3)]
    xs = np.where(row)[0]
    wx0, wx1 = int(xs[0]), int(xs[-1])
    # eaves: the widest row in the first 12 % of the roof above ry; ridge: the topmost row at least 18 % of the eaves
    band = range(max(top, ry - max(6, (ry - top) // 6)), ry + 1)
    er = max(band, key=lambda y: span[y])
    exs = np.where(op[er])[0]
    ex0, ex1 = int(exs[0]), int(exs[-1])
    rid = top
    for y in range(top, ry):
        if span[y] >= 0.18 * (ex1 - ex0):
            rid = y
            break
    rxs = np.where(op[rid])[0]
    ridge_x = float((rxs[0] + rxs[-1]) / 2.0)
    out_dir = os.path.join(ATLAS, e["sheet"], "stages")
    os.makedirs(out_dir, exist_ok=True)
    arr = np.asarray(im)
    files = []
    for k, (y0, y1) in enumerate([(ry, base), (top, ry)]):
        b = np.zeros_like(arr)
        b[y0:y1] = arr[y0:y1]
        fn = f"{cid}_b{k}.webp"
        Image.fromarray(b[y0:y1]).save(os.path.join(out_dir, fn), "WEBP", lossless=True, quality=100, method=6)
        files.append((fn, y0, y1))
    # side wall: a window-wide strip of the left wall (between the wall edge and the door), full wall height
    sw = max(24, int((wx1 - wx0) * 0.38))
    side = im.crop((wx0 + 2, ry + 2, wx0 + 2 + sw, base - 2))
    side_a = np.asarray(side).copy()
    side_a[..., 3] = 255  # a solid wall (decorations at the edge would leave holes)
    sf = f"{cid}_side.webp"
    Image.fromarray(side_a).save(os.path.join(out_dir, sf), "WEBP", lossless=True, quality=100, method=6)
    # roof print: a strip just above the eaves, away from the ridge / chimney, full roof width
    ry0 = max(top, ry - max(10, (ry - rid) // 2))
    roof = np.asarray(im.crop((ex0 + (ex1 - ex0) // 6, ry0, ex1 - (ex1 - ex0) // 6, max(ry0 + 6, ry - 2)))).copy()
    roof[..., 3] = 255
    rf = f"{cid}_roof.webp"
    Image.fromarray(roof).save(os.path.join(out_dir, rf), "WEBP", lossless=True, quality=100, method=6)
    hu = float(e["height_units"])
    scale = hu / (base - top)
    rel = f"art/atlas/{e['sheet']}/stages/"
    st = {"bands": [{"file": rel + fn, "y0": y0, "y1": y1, "hinge_units": round((base - y1) * scale, 4),
                     "height_units": round((y1 - y0) * scale, 4), "roof": k == 1} for k, (fn, y0, y1) in enumerate(files)],
          "height_units": hu, "px": [w, h], "base_y": base, "roof_y": ry, "wall_x": [wx0, wx1 + 1],
          "side_file": rel + sf, "roof_file": rel + rf,
          "gable": {"eave_l": [ex0, er], "eave_r": [ex1, er], "ridge": [ridge_x, rid]}}
    return st, (im, ry, (wx0, wx1), (ex0, ex1, er), (ridge_x, rid), side, Image.fromarray(roof))


def main():
    cat = {e["id"]: e for e in json.load(open(os.path.join(ATLAS, "catalog.json")))}
    ids = sorted(k for k in cat if k.startswith("story_wc_houses_"))
    by_sheet, cells = {}, []
    for cid in ids:
        st, viz = build(cid, cat[cid])
        by_sheet.setdefault(cat[cid]["sheet"], {})[cid] = st
        cells.append((cid, viz))
        print(cid, "roof", st["roof_y"], "base", st["base_y"], "eaves", st["gable"]["eave_l"], st["gable"]["eave_r"],
              "ridge", st["gable"]["ridge"])
    for sheet, d in by_sheet.items():
        p = os.path.join(ATLAS, sheet, "stages", "stages.json")
        old = json.load(open(p)) if os.path.exists(p) else {}
        old.update(d)
        json.dump(old, open(p, "w"), indent=1)
    if "--sheet" in sys.argv:
        out = sys.argv[sys.argv.index("--sheet") + 1]
        cw, ch = 330, 330
        sheet = Image.new("RGB", (cw * 7, ch * 2 + 40), (60, 60, 70))
        dr = ImageDraw.Draw(sheet)
        for i, (cid, (im, ry, wx, ex, rg, side, roof)) in enumerate(cells):
            c = Image.new("RGBA", im.size, (90, 90, 100, 255))
            c.alpha_composite(im)
            d = ImageDraw.Draw(c)
            d.line([(0, ry), (im.width, ry)], fill=(255, 0, 0, 255), width=3)
            d.line([(ex[0], ex[2]), (rg[0], rg[1]), (ex[1], ex[2])], fill=(0, 255, 255, 255), width=3)
            c.thumbnail((cw - 90, ch - 20))
            x, y = (i % 7) * cw, (i // 7) * ch
            sheet.paste(c.convert("RGB"), (x, y))
            s2 = side.copy()
            s2.thumbnail((80, 160))
            sheet.paste(s2.convert("RGB"), (x + cw - 85, y))
            r2 = roof.copy()
            r2.thumbnail((80, 60))
            sheet.paste(r2.convert("RGB"), (x + cw - 85, y + 170))
            dr.text((x + 4, y + ch - 16), cid[-4:], fill=(255, 255, 255))
        sheet.save(out)
        print("contact", out)


if __name__ == "__main__":
    main()

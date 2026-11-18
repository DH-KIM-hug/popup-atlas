#!/usr/bin/env python3
"""Cut house facade cards into horizontal fold-up bands (pop-up build stages) — shared, any tale.

  python3 tools/atlas/house_stages.py            # houses listed in HOUSES below
  python3 tools/atlas/house_stages.py story_houses_06:5

A house is built tap by tap: band 0 (the bottom of the wall) folds up from the page on its bottom hinge, band 1 folds
up standing on top of band 0, …, the last band is the roof (+ chimney). Bands are exact horizontal slices of the one
facade card, so stacked they reproduce it pixel for pixel (no seams to align).
  * wall/roof split: scanning up from the base, the first row whose silhouette width leaves the wall width by > 6 %
    (the eave overhang) starts the roof band.
  * wall cuts: N-1 bands of equal height, each cut snapped (±5 % of the wall height) to the row with the strongest
    horizontal edge (a mortar line, a plank seam, a straw-bundle band) so it reads as a die-cut along the material.
Output: game/art/atlas/<sheet>/stages/<id>_b<k>.webp (+ .webp of each cumulative stage for previews) and
game/art/atlas/<sheet>/stages/stages.json: {id: {"bands": [{"file", "y0", "y1", "hinge_units", "height_units"}],
"height_units", "px"}} with y in facade px from the top; hinge_units = height of the band's hinge above the page.
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ATLAS = os.path.join(ROOT, "game", "art", "atlas")
# catalog id -> number of bands (taps in three_pigs: straw 3, wood 5, brick 10 = 2 per band)
HOUSES = {"story_houses_00": 3, "story_houses_03": 5, "story_houses_06": 5, "story_houses_08": 3, "story_houses_09": 3}


def cut_house(cid, n, cat):
    e = cat[cid]
    path = os.path.join(ROOT, "game", e["path"])
    im = np.array(Image.open(path).convert("RGBA"))
    h, w = im.shape[:2]
    op = im[..., 3] > 128
    ys = np.where(op.any(1))[0]
    top, base = int(ys[0]), int(ys[-1]) + 1
    widths = op.sum(1).astype(float)
    wall_w = float(np.median(widths[base - max(4, (base - top) // 8): base - 2]))
    y = base - 3
    while y > top and abs(widths[y] - wall_w) < 0.06 * wall_w:
        y -= 1
    roof_y = y + 1  # first row of the wall band below the eave
    grey = im[..., :3].astype(float).mean(-1)
    edge = np.abs(np.diff(grey, axis=0)).sum(1)  # row y = edge between y and y+1
    wall_h = base - roof_y
    cuts = []
    for k in range(1, n - 1):
        c = int(round(base - wall_h * k / (n - 1)))
        win = max(2, int(0.05 * wall_h))
        lo, hi = max(roof_y + 4, c - win), min(base - 4, c + win)
        cuts.append(int(lo + np.argmax(edge[lo:hi])) + 1 if hi > lo else c)
    bounds = [base] + cuts + [roof_y, top]  # bottom → top
    hu = float(e["height_units"])
    scale = hu / (base - top)
    out_dir = os.path.join(ATLAS, e["sheet"], "stages")
    os.makedirs(out_dir, exist_ok=True)
    bands = []
    for k in range(len(bounds) - 1):
        y1, y0 = bounds[k], bounds[k + 1]
        band = np.zeros_like(im)
        band[y0:y1] = im[y0:y1]
        name = f"{cid}_b{k}.webp"
        Image.fromarray(band[y0:y1]).save(os.path.join(out_dir, name), "WEBP", lossless=True, quality=100, method=6)
        cum = np.zeros_like(im)
        cum[y0:base] = im[y0:base]
        Image.fromarray(cum).save(os.path.join(out_dir, f"{cid}_stage{k}.webp"), "WEBP", lossless=True, quality=100,
                                  method=6)
        bands.append({"file": f"art/atlas/{e['sheet']}/stages/{name}", "y0": int(y0), "y1": int(y1),
                      "hinge_units": round((base - y1) * scale, 4), "height_units": round((y1 - y0) * scale, 4),
                      "roof": k == len(bounds) - 2})
    return {"bands": bands, "height_units": hu, "px": [w, h], "base_y": base, "roof_y": roof_y}


def main():
    cat = {e["id"]: e for e in json.load(open(os.path.join(ATLAS, "catalog.json")))}
    want = dict(a.split(":") for a in sys.argv[1:]) if sys.argv[1:] else HOUSES
    res = {}
    for cid, n in want.items():
        res[cid] = cut_house(cid, int(n), cat)
        print(cid, "bands", [(b["y0"], b["y1"]) for b in res[cid]["bands"]], "roof_y", res[cid]["roof_y"])
    sheets = {cat[c]["sheet"] for c in res}
    for s in sheets:
        p = os.path.join(ATLAS, s, "stages", "stages.json")
        old = json.load(open(p)) if os.path.exists(p) else {}
        old.update({c: r for c, r in res.items() if cat[c]["sheet"] == s})
        json.dump(old, open(p, "w"), indent=1)
        print("wrote", p)


if __name__ == "__main__":
    main()

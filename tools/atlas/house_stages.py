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
  * openings (2026-11-18, three_pigs phase 2): a straight cut through a window or door read as a die-cut slicing it;
    each cut now steps around the openings listed in OPENINGS (facade px boxes): in those columns the boundary
    jumps up to the opening's top, so the whole window / door stays in the band below (that band gets a tab, the
    bands above a notch). Wall pixels outside the wall's own width (the eave tips) go to the roof band.
    A band's hinge stays at its straight cut row (y0/y1); img_y0/img_y1 are the rows its image covers.
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
HOUSES = {"story_houses_00": 3, "story_houses_03": 5, "story_houses_06": 5, "story_houses_08": 3, "story_houses_09": 3,
          "story_wc_shop_00": 2, "story_sm_cottage_00": 2}
# windows / doors (x0, y0, x1, y1 in facade px, measured on a grid sheet), kept whole in one band
OPENINGS = {
    "story_houses_00": [(72, 158, 150, 228), (160, 165, 278, 302)],
    "story_houses_03": [(42, 130, 158, 210), (162, 130, 265, 282), (272, 130, 388, 210)],
    "story_houses_06": [(26, 166, 139, 262), (138, 153, 254, 309), (253, 166, 367, 262)],
    "story_houses_08": [],
    "story_houses_09": [],
    "story_wc_shop_00": [(90, 230, 300, 445), (296, 225, 432, 470)],
    # sunmoon cottage (2026-11-22): lattice paper door and the paper-screen window
    "story_sm_cottage_00": [(214, 207, 362, 422), (422, 207, 588, 343)],
}
# die-cut window glass (x0, y0, x1, y1; the blue panes inside go transparent, mullions stay) so a pig standing just
# behind the front wall shows its face in the window, framed by it (2026-11-18 user: "아기돼지들 집에 있어야하지 않겠니?")
GLASS = {
    "story_houses_00": [(85, 170, 138, 223)],
    "story_houses_03": [(78, 142, 123, 200), (308, 142, 353, 200)],
    "story_houses_06": [(62, 188, 105, 243), (290, 188, 333, 243)],
}
# door leaf (x0, y0 top of the leaf, x1; bottom = base; arch = round top) cut out as its own card on a side hinge
DOORS = {
    "story_houses_00": (166, 172, 267, True),
    "story_houses_03": (168, 138, 260, False),
    "story_houses_06": (157, 193, 237, True),
    # witch_candy shop (2026-11-19): the mint door pasted into the drawn doorway (tools/atlas/wc_shop_door.py); the
    # optional 5th value is the leaf's bottom row (the stone steps below stay on the wall)
    "story_wc_shop_00": (304, 242, 425, True, 443),
    # sunmoon cottage: the lattice paper door leaf; the veranda boards and the stepping stone stay on the wall
    "story_sm_cottage_00": (214, 207, 362, False, 422),
}
# hand-picked wall cut rows (bottom → top) where the window rows leave too little room for even bands: a cut through a
# window row steps up around the windows, so they stand whole on the band below
# wood (v2, user: "the first stage is a lone door"): band 0 = floor, sill and the plank walls up to the windows + door
# starts as a foundation, not a floating door
# (sunmoon 2026-11-22) wall / roof split row and the wall's own x extent where the automatic reads miss (a stone base
# wider than the walls, a veranda)
ROOF_Y = {"story_sm_cottage_00": 205}
WALL_X = {"story_sm_cottage_00": (60, 668)}
CUTS = {"story_houses_06": [293, 275, 214], "story_houses_03": [211, 172, 140]}


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
    roof_y = ROOF_Y.get(cid, y + 1)  # first row of the wall band below the eave
    extra = {}
    for (gx0, gy0, gx1, gy1) in GLASS.get(cid, []):
        sub = im[gy0:gy1, gx0:gx1].astype(int)
        blue = (sub[..., 2] > sub[..., 0] + 15) & (sub[..., 3] > 0)
        im[gy0:gy1, gx0:gx1][blue] = 0
    if GLASS.get(cid):
        extra["windows"] = [[(g[0] + g[2]) / 2.0, (g[1] + g[3]) / 2.0] for g in GLASS[cid]]
        extra["window_boxes"] = [list(g) for g in GLASS[cid]]
    if cid in DOORS:
        dx0, dy0, dx1, arch = DOORS[cid][:4]
        dbot = int(DOORS[cid][4]) if len(DOORS[cid]) > 4 else base
        yy, xx = np.mgrid[0:h, 0:w]
        r = (dx1 - dx0) / 2.0
        cx = (dx0 + dx1) / 2.0
        leaf = (xx >= dx0) & (xx < dx1) & (yy >= dy0) & (yy < dbot)
        if arch:
            leaf &= (yy >= dy0 + r) | ((xx + 0.5 - cx) ** 2 + (yy + 0.5 - (dy0 + r)) ** 2 <= r * r)
        door = np.where(leaf[..., None], im, 0).astype(np.uint8)
        im[leaf] = 0
        out_dir0 = os.path.join(ATLAS, e["sheet"], "stages")
        os.makedirs(out_dir0, exist_ok=True)
        Image.fromarray(door[dy0:dbot, dx0:dx1]).save(os.path.join(out_dir0, f"{cid}_door.webp"), "WEBP", lossless=True,
                                                      quality=100, method=6)
        extra["door"] = {"file": f"art/atlas/{e['sheet']}/stages/{cid}_door.webp", "x0": dx0, "x1": dx1, "y0": dy0,
                         "y1": int(dbot)}
    grey = im[..., :3].astype(float).mean(-1)
    edge = np.abs(np.diff(grey, axis=0)).sum(1)  # row y = edge between y and y+1
    wall_h = base - roof_y
    # cut rows: only rows that cross no window (openings that stand on the base, i.e. doors, are stepped around
    # below); spread evenly over those rows, then snapped to the strongest material line nearby that is also allowed
    ops = OPENINGS.get(cid, [])
    allowed = [y for y in range(base - 4, roof_y + 4, -1)
               if not any(oy0 - 2 <= y <= oy1 + 2 for (ox0, oy0, ox1, oy1) in ops if oy1 < base - 3)]
    cuts = []
    for k in range(1, n - 1):
        if cid in CUTS:
            cuts.append(int(CUTS[cid][k - 1]))
            continue
        if not allowed:
            cuts.append(int(round(base - wall_h * k / (n - 1))))
            continue
        c = allowed[min(len(allowed) - 1, int(round(len(allowed) * k / (n - 1))))]
        win = max(2, int(0.04 * wall_h))
        prev = cuts[-1] if cuts else base
        minh = max(4, int(0.6 * len(allowed) / (n - 1)))
        cand = [y for y in allowed if abs(y - c) <= win and y <= prev - minh]
        cuts.append(int(max(cand, key=lambda y: edge[y - 1])) if cand else c)
    bounds = [base] + cuts + [roof_y, top]  # bottom → top
    hu = float(e["height_units"])
    scale = hu / (base - top)
    out_dir = os.path.join(ATLAS, e["sheet"], "stages")
    os.makedirs(out_dir, exist_ok=True)
    # per-column boundaries: bnd[k][x] = first row (from the top) of band k-1 above cut k; band k = rows bnd[k+1]..bnd[k]
    xs_all = np.arange(w)
    wall_cols = np.where(op[base - max(4, (base - top) // 8): base - 2].any(0))[0]
    wx0, wx1 = int(wall_cols[0]), int(wall_cols[-1])
    if cid in WALL_X:
        wx0, wx1 = WALL_X[cid]
    bnd = []
    for k, c in enumerate(bounds):
        row = np.full(w, c, dtype=int)
        if 0 < k < len(bounds) - 1:
            for (ox0, oy0, ox1, oy1) in OPENINGS.get(cid, []):
                if oy0 < c < oy1:
                    row[ox0:ox1] = np.minimum(row[ox0:ox1], oy0)  # the opening stays whole in the band below
            # eave tips (outside the wall's own width, just under the roof line) belong to the roof; lower down, pixels
            # outside the measured wall width are wall edge (nail heads, shutters) and stay with their band (v2: sending
            # them to the roof stretched the roof card's bounds to the floor and the roof drew as a giant gable)
            if k == len(bounds) - 2:
                tip = roof_y + max(4, int(0.12 * (base - roof_y)))
                row[(xs_all < wx0) | (xs_all > wx1)] = tip
        bnd.append(row)
    for k in range(1, len(bnd)):  # keep boundaries ordered (a band never has negative height)
        bnd[k] = np.minimum(bnd[k], bnd[k - 1])
    bands = []
    yy = np.arange(h)[:, None]
    for k in range(len(bounds) - 1):
        y1, y0 = bounds[k], bounds[k + 1]
        mask = (yy >= bnd[k + 1][None, :]) & (yy < bnd[k][None, :])
        band = np.where(mask[..., None], im, 0).astype(np.uint8)
        rows = np.where(mask.any(1))[0]
        iy0, iy1 = (int(rows[0]), int(rows[-1]) + 1) if rows.size else (y0, y1)
        name = f"{cid}_b{k}.webp"
        Image.fromarray(band[iy0:iy1]).save(os.path.join(out_dir, name), "WEBP", lossless=True, quality=100, method=6)
        cum = np.where((yy >= bnd[k + 1][None, :])[..., None], im, 0).astype(np.uint8)
        cum[base:] = 0
        Image.fromarray(cum).save(os.path.join(out_dir, f"{cid}_stage{k}.webp"), "WEBP", lossless=True, quality=100,
                                  method=6)
        bands.append({"file": f"art/atlas/{e['sheet']}/stages/{name}", "y0": int(y0), "y1": int(y1),
                      "img_y0": iy0, "img_y1": iy1,
                      "hinge_units": round((base - y1) * scale, 4), "height_units": round((y1 - y0) * scale, 4),
                      "roof": k == len(bounds) - 2})
    extra["wall_x"] = [wx0, wx1 + 1]  # the wall's own width (no eaves): where a box's side walls stand
    return {"bands": bands, "height_units": hu, "px": [w, h], "base_y": base, "roof_y": roof_y, **extra}


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

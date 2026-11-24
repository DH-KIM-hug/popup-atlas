#!/usr/bin/env python3
"""House bodies for every building card (2026-11-23, user: "집들은 무조건 입체적으로 아주 잘 들어맞게").

  python3 tools/atlas/house_bodies.py [ids...] [--sheet artifacts/houses/bodies_contact.jpg]

A house card is a front; its body is the front's own silhouette extruded straight back (a pop-up prism), so every
corner of the body meets the front card exactly at its cut edge: side walls stand on the drawn wall edges, the roof
surface follows the drawn roof line (ridge, slopes, eave overhang with its soffit), the back repeats the outline.
Per card this writes game/art/atlas/bodies.json (merge: only the listed ids are replaced) with, in facade px:
  poly       body outline (clockwise from the top-left eave), chimneys and thin decorations removed, walls straight,
             each column one run (overhang underside where the roof sticks out past the walls)
  roof_y     wall top row (rows above print the roof, below the wall); wall_x [x0, x1]; base_y; px [w, h]
  chimneys   [[x0, y_top, x1, y_seat]] boxes cut from the drawn chimney (seat = deepest roof row under it)
  side / roof / back / chimney files: crops of the card's own art (game/art/atlas/<sheet>/bodies/)
    side  a plain strip of its wall (lowest-detail window between the wall edge and the door), mirror-tiled
    roof  a strip of its own roofing just above the eaves, mirror-tiled
    back  the full card size: the body outline filled with its own wall (tiled) below roof_y and its own gable /
          roof print above (no door, no windows on the wall)
  depth      suggested body depth as a fraction of the wall width
Godot builds the mesh in game/core/world/house_body.gd (SetPiece boxes, template village houses).
"""
import json, os, sys
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ATLAS = os.path.join(ROOT, "game", "art", "atlas")
OUT_JSON = os.path.join(ATLAS, "bodies.json")

IDS = ([f"village_houses_{i:02d}" for i in range(21) if i not in (10, 11)]
       + ["korean_village_00", "korean_village_01", "korean_village_02", "korean_village_03", "korean_village_04",
          "fairytale_west_04", "fairytale_west_05", "fairytale_west_06", "fairytale_west_10",
          "winter_snow_09", "winter_snow_10",
          "story_houses_00", "story_houses_03", "story_houses_06", "story_houses_08", "story_houses_09",
          "story_wc_shop_00", "story_sm_cottage_00", "story_sm_village_02", "story_wg_cottage_00"]
       + ["house_barn_terracotta", "house_cottage_terracotta", "house_cottage_thatch", "house_round_thatch",
          "house_stone_moss", "house_tall_slate"]
       + [f"story_wc_houses_a_{i:02d}" for i in range(7)] + [f"story_wc_houses_b_{i:02d}" for i in range(7)])

# per card: roof_y / wall_x / clip (x0, x1 columns the body may use: a windmill's tower, not its sails) /
# no_chimney / depth (fraction of the wall width) / chimney_k (opening width as a fraction of the card width)
OVERRIDE = {
    "story_wc_houses_b_05": {"roof_y": 245},
    "story_sm_cottage_00": {"roof_y": 230, "wall_x": [63, 668]},
    "story_wg_cottage_00": {"roof_y": 242, "wall_x": [35, 630], "side_rect": [35, 244, 630, 345]},
    "winter_snow_09": {"chimneys": [[193, 5, 252, 70]]},
    # roofs whose own print has no plain roofing band: the kit's paper swatch of the same material
    "village_houses_01": {"roof_mat": "terracotta"},
    "village_houses_06": {"no_chimney": True, "roof_mat": "terracotta"},
    "village_houses_08": {"no_chimney": True},
    "korean_village_02": {"no_chimney": True},
    "korean_village_03": {"no_chimney": True},
    "korean_village_04": {"no_chimney": True},
    "fairytale_west_06": {"roof_y": 176, "wall_x": [27, 212], "chimneys": [[166, 15, 207, 85]]},
    "story_houses_00": {"wall_x": [28, 380]},
    "story_wc_houses_a_00": {"roof_mat": "slate"},
    "story_wc_houses_a_02": {"roof_y": 298, "roof_mat": "slate", "chimneys": [[41, 80, 95, 238]]},
    "story_wc_houses_a_06": {"roof_mat": "slate"},
    "story_wc_houses_b_01": {"roof_mat": "slate", "chimneys": [[218, 17, 282, 118]], "side_rect": [34, 377, 164, 395]},
    "story_wc_houses_b_04": {"wall_x": [30, 270], "chimneys": [[42, 37, 97, 150]]},
    "story_wc_houses_b_06": {"roof_y": 182, "chimneys": [[227, 22, 282, 120]]},
    "house_round_thatch": {"roof_mat": "thatch"},
    "story_houses_06": {"roof_mat": "terracotta"},
    # windmill: the tower and its cap; the sails stay on the front card
    "village_houses_05": {"poly": [[45, 120], [62, 62], [101, 34], [140, 62], [157, 120], [167, 264], [35, 264]],
                          "roof_y": 120, "lines": [[48.6, -0.0], [154.0, 0.0]], "depth": 0.9, "roof_mat": "slate"},
}
# patjuk wave 2 ("fence backs are flat"): the yard's stone-and-clay walls with their straw caps get a thin body
OVERRIDE.update({"story_pj_yard_00": {"depth": 0.06, "no_chimney": True},
                 "story_pj_yard_01": {"depth": 0.18, "no_chimney": True}})
DEPTH = 0.72  # default body depth / wall width


def load(cid, e):
    im = Image.open(os.path.join(ROOT, "game", e["path"])).convert("RGBA")
    return im


def components(mask):
    """Label 4-connected components (numpy + BFS); returns labels, sizes."""
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    sizes = [0]
    ys, xs = np.nonzero(mask)
    n = 0
    for y0, x0 in zip(ys, xs):
        if lab[y0, x0]:
            continue
        n += 1
        q = deque([(y0, x0)])
        lab[y0, x0] = n
        c = 0
        while q:
            y, x = q.popleft()
            c += 1
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    q.append((yy, xx))
        sizes.append(c)
    return lab, sizes


def morph(mask, k, op):
    if k < 3:
        return mask
    k |= 1
    im = Image.fromarray((mask * 255).astype(np.uint8))
    f = ImageFilter.MinFilter(k) if op == "erode" else ImageFilter.MaxFilter(k)
    return np.asarray(im.filter(f)) > 127


def opening(mask, k):
    # pad so shapes touching the image edge are not eaten
    p = k + 2
    m = np.pad(mask, p)
    r = morph(morph(m, k, "erode"), k, "dilate")
    return r[p:-p, p:-p]


def roof_row(op):
    ys = np.where(op.any(1))[0]
    top, base = int(ys[0]), int(ys[-1]) + 1
    xs = [np.where(op[y])[0] for y in range(op.shape[0])]
    span = np.array([(x[-1] - x[0] + 1) if len(x) else 0 for x in xs], float)
    lo = base - int((base - top) * 0.45)
    wall = float(np.median(span[lo:base - 4]))
    y = lo
    while y > top + 4:
        if span[y] > wall * 1.06 or span[y] < wall * 0.8:
            break
        y -= 1
    return y + 1, top, base


def wall_edges(op, ry, base, clip):
    lefts, rights = [], []
    for y in range(ry + (base - ry) // 5, base - max(3, (base - ry) // 8)):
        xs = np.where(op[y, clip[0]:clip[1]])[0]
        if len(xs):
            lefts.append(xs[0] + clip[0])
            rights.append(xs[-1] + clip[0])
    lefts, rights = np.array(lefts), np.array(rights)
    # the wall edge is the most common edge column (steps, bushes and pumpkins stick out on a few rows)
    def mode(a):
        v, c = np.unique(a, return_counts=True)
        m = float(np.median(a))
        good = a[np.abs(a - m) < max(4, 0.04 * (rights.max() - lefts.min()))]
        return int(np.median(good)) if len(good) else int(m)
    return mode(lefts), mode(rights) + 1


def plain_strip(arr, y0, y1, x0, x1, sw, avoid):
    """Column window [x, x+sw) inside [x0, x1) with the least detail (gradient energy), avoiding `avoid` ranges."""
    g = arr[y0:y1, :, :3].astype(float).mean(2)
    gx = np.abs(np.diff(g, axis=1))
    gy = np.abs(np.diff(g, axis=0))
    e = np.zeros(arr.shape[1])
    e[:-1] += gx.sum(0)
    e[:] += np.pad(gy.sum(0), (0, 0))
    alpha = arr[y0:y1, :, 3] > 200
    best, bx = None, x0
    for x in range(x0, max(x0 + 1, x1 - sw)):
        if any(not (x + sw <= a or x >= b) for a, b in avoid):
            continue
        if alpha[:, x:x + sw].mean() < 0.97:
            continue
        v = e[x:x + sw].sum()
        if best is None or v < best:
            best, bx = v, x
    return bx


def first_row(col):
    ys = np.where(col)[0]
    return int(ys[0]) if len(ys) else 10 ** 6


def find_chimneys(roof, ry, wx0, wx1, base, ov):
    """Chimneys: narrow plateaus standing up out of the roof line with a vertical side (1-D grey opening of the
    column heights; a gable's apex is cut by the opening too, but it has no jump at its sides)."""
    h, w = roof.shape
    H = np.array([base - first_row(roof[:, x]) if roof[:, x].any() else 0 for x in range(w)], float)
    ww = wx1 - wx0
    k = max(5, int(ov.get("chimney_k", 0.2) * ww)) | 1
    r = k // 2

    def win(a, f):
        p = np.pad(a, r, mode="edge")
        return np.array([f(p[i:i + k]) for i in range(len(a))])
    Ho = win(win(H, np.min), np.max)
    Hm = H.max()
    cand = (H - Ho) > 0.035 * Hm
    out = []
    x = 0
    while x < w:
        if not cand[x]:
            x += 1
            continue
        x0 = x
        while x < w and cand[x]:
            x += 1
        x1 = x
        if x1 - x0 < 3 or x1 - x0 > 0.22 * ww or x1 <= wx0 + 2 or x0 >= wx1 - 2:
            continue
        # vertical side: a jump between neighbouring columns near either end of the run
        jl = max(abs(H[i] - H[i - 1]) for i in range(max(1, x0 - 2), min(w, x0 + 3)))
        jr = max(abs(H[i] - H[i - 1]) for i in range(max(1, x1 - 2), min(w, x1 + 3)))
        if max(jl, jr) < 0.04 * Hm:
            continue
        # grow to the stack's full width: columns whose top sits on the plateau height
        top = H[x0:x1].max()
        while x0 > 0 and H[x0 - 1] > top - 0.6 * (top - Ho[x0 - 1]) and H[x0 - 1] - Ho[x0 - 1] > 0.01 * Hm:
            x0 -= 1
        while x1 < w and H[x1] > top - 0.6 * (top - Ho[x1]) and H[x1] - Ho[x1] > 0.01 * Hm:
            x1 += 1
        yt = int(base - top)
        out.append([int(x0), yt, int(x1), int(base - Ho[x0:x1].min())])
    return out


def find_patch(arr, region, pw, ph):
    """The patch inside `region` closest to the region's dominant colour with the least detail (RGBA, opaque)."""
    reg = region & (arr[..., 3] > 200)
    rgb = arr[..., :3].astype(float)
    px = rgb[reg]
    if len(px) == 0:
        return np.full((ph, pw, 4), 200, np.uint8)
    q = (px // 32).astype(int)
    keys = q[:, 0] * 64 + q[:, 1] * 8 + q[:, 2]
    mode = np.bincount(keys).argmax()
    dom = px[keys == mode].mean(0)
    ys, xs = np.nonzero(reg)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    lum = rgb.mean(2)
    for scale in (1.0, 0.7, 0.45, 0.25):
        cw = max(4, min(int(round(pw * scale)), x1 - x0))
        ch = max(4, min(int(round(ph * scale)), y1 - y0))
        best, bxy = None, None
        step = max(1, min(cw, ch) // 5)
        for yy in range(y0, max(y0 + 1, y1 - ch + 1), step):
            for xx in range(x0, max(x0 + 1, x1 - cw + 1), step):
                if reg[yy:yy + ch, xx:xx + cw].mean() < 0.97:
                    continue
                pt = rgb[yy:yy + ch, xx:xx + cw]
                col = np.abs(pt.reshape(-1, 3) - dom).sum(1).mean()
                L = lum[yy:yy + ch, xx:xx + cw]
                det = np.abs(np.diff(L, axis=1)).mean() + np.abs(np.diff(L, axis=0)).mean()
                v = col + 3.0 * det
                if best is None or v < best:
                    best, bxy = v, (yy, xx)
        if best is not None:
            out = arr[bxy[0]:bxy[0] + ch, bxy[1]:bxy[1] + cw].copy()
            m = reg[bxy[0]:bxy[0] + ch, bxy[1]:bxy[1] + cw]
            if not m.all():
                out[~m, :3] = np.clip(dom.round(), 0, 255).astype(np.uint8)
            out[..., 3] = 255
            return out
    out = np.zeros((max(4, min(ph, 8)), max(4, min(pw, 8)), 4), np.uint8)
    out[..., :3] = np.clip(dom.round(), 0, 255).astype(np.uint8)
    out[..., 3] = 255
    return out


def patch_ok(arr, region, patch, tol=28.0):
    """The patch's colour is close to the region's dominant colour (no decoration in it)."""
    px = arr[..., :3][region].astype(float)
    q = (px // 32).astype(int)
    keys = q[:, 0] * 64 + q[:, 1] * 8 + q[:, 2]
    dom = px[keys == np.bincount(keys).argmax()].mean(0)
    pm = patch[..., :3].reshape(-1, 3).astype(float)
    return float(np.abs(pm - dom).sum(1).mean()) < tol * 3


def mirror_tile(a):
    """2x2 mirrored copy: tiles seamlessly with plain repeat."""
    top = np.concatenate([a, a[:, ::-1]], 1)
    return np.concatenate([top, top[::-1]], 0)


def dp(points, eps):
    """Douglas-Peucker on an open polyline."""
    if len(points) < 3:
        return points
    a, b = np.array(points[0], float), np.array(points[-1], float)
    d = b - a
    L = np.hypot(*d)
    pts = np.array(points, float)
    if L < 1e-9:
        dist = np.hypot(*(pts - a).T)
    else:
        dist = np.abs(d[0] * (pts[:, 1] - a[1]) - d[1] * (pts[:, 0] - a[0])) / L
    i = int(np.argmax(dist))
    if dist[i] > eps:
        return dp(points[:i + 1], eps)[:-1] + dp(points[i:], eps)
    return [points[0], points[-1]]


def fit_line(ys, xs, tol):
    """Robust x = a + b*y (two passes, outliers past tol dropped)."""
    ys, xs = np.asarray(ys, float), np.asarray(xs, float)
    keep = np.abs(xs - np.median(xs)) < tol
    for _ in range(2):
        if keep.sum() < 4:
            break
        bb, aa = np.polyfit(ys[keep], xs[keep], 1)
        keep = np.abs(xs - (aa + bb * ys)) < tol * 0.5
    if keep.sum() < 4:
        return float(np.median(xs)), 0.0
    bb, aa = np.polyfit(ys[keep], xs[keep], 1)
    if abs(bb) > 0.25:  # a wall leans at most a little; more is a decoration
        return float(np.median(xs[keep])), 0.0
    if abs(bb) > 0.12:
        ym = float(np.median(ys[keep]))
        xm = aa + bb * ym
        bb = float(np.clip(bb, -0.12, 0.12))
        aa = xm - bb * ym
    return float(aa), float(bb)


def fill_holes(m):
    h, w = m.shape
    pad = np.zeros((h + 2, w + 2), np.uint8)
    pad[1:-1, 1:-1] = (~m) * 255
    pad[0, :] = pad[-1, :] = 255
    pad[:, 0] = pad[:, -1] = 255
    li = Image.fromarray(pad).copy()
    ImageDraw.floodfill(li, (0, 0), 128)
    return np.asarray(li)[1:-1, 1:-1] != 128


def trace(mask):
    """Outer boundary of a hole-free blob along pixel edges (image coords, clockwise on screen: inside on the
    right of travel), as a list of corner points."""
    h, w = mask.shape
    m = np.pad(mask, 1)
    out = {}
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        X, Y = x - 1, y - 1
        if not m[y - 1, x]:
            out.setdefault((X, Y), []).append((X + 1, Y))
        if not m[y, x + 1]:
            out.setdefault((X + 1, Y), []).append((X + 1, Y + 1))
        if not m[y + 1, x]:
            out.setdefault((X + 1, Y + 1), []).append((X, Y + 1))
        if not m[y, x - 1]:
            out.setdefault((X, Y + 1), []).append((X, Y))
    start = min(out.keys(), key=lambda p: (p[1], p[0]))
    loop = [start]
    cur = start
    prev_d = (1, 0)
    while True:
        nxt = out[cur]
        if len(nxt) > 1:  # pinch: take the sharpest right turn
            def turn(q):
                d = (q[0] - cur[0], q[1] - cur[1])
                return prev_d[0] * d[1] - prev_d[1] * d[0]
            nxt.sort(key=turn, reverse=True)
        q = nxt.pop(0)
        prev_d = (q[0] - cur[0], q[1] - cur[1])
        if q == start:
            break
        loop.append(q)
        cur = q
    # drop collinear corners
    pts = []
    n = len(loop)
    for i in range(n):
        a, b, c = loop[i - 1], loop[i], loop[(i + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
            pts.append(b)
    return pts


def simplify_loop(pts, eps):
    n = len(pts)
    i0 = 0
    i1 = max(range(n), key=lambda i: (pts[i][0] - pts[0][0]) ** 2 + (pts[i][1] - pts[0][1]) ** 2)
    a = dp(pts[i0:i1 + 1], eps)
    b = dp(pts[i1:] + [pts[0]], eps)
    return a[:-1] + b[:-1]


def classify(poly, lines, ry, base):
    """Material per edge poly[i] -> poly[i+1]: 0 wall, 1 roof, 2 soffit (eave underside), 3 base (no face)."""
    mats = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        L = max(1e-6, (dx * dx + dy * dy) ** 0.5)
        ox, oy = dy / L, -dx / L  # outward normal (screen coords, y down)
        if y0 >= base - 1 and y1 >= base - 1:
            mats.append(3)
            continue
        on_wall = False
        for (aa, bb) in lines:
            if abs(x0 - (aa + bb * y0)) < 4 and abs(x1 - (aa + bb * y1)) < 4 and min(y0, y1) >= ry - 3:
                on_wall = True
        if on_wall or (abs(oy) < 0.35 and min(y0, y1) >= ry - 2):
            mats.append(0)
        elif oy > 0.5:
            mats.append(2)
        else:
            mats.append(1)
    return mats


def build(cid, e, stage):
    ov = OVERRIDE.get(cid, {})
    im = load(cid, e)
    arr = np.asarray(im)
    h, w = arr.shape[:2]
    op = arr[..., 3] > 90
    lab, sizes = components(op)
    big = max(sizes)
    op = np.isin(lab, [i for i, s in enumerate(sizes) if i and s > 0.04 * big])
    ry0, top, base = roof_row(op)
    ys_ = np.where(op.any(1))[0]
    base = int(ys_[-1]) + 1
    if "poly" in ov:  # drawn by hand (a windmill: tower + cap, not the sails)
        poly = [list(p) for p in ov["poly"]]
        ry = int(ov["roof_y"])
        lines = ov["lines"]
        mimg = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mimg).polygon([tuple(p) for p in poly], fill=255)
        M = np.asarray(mimg) > 127
        chim = []
    else:
        # walls: robust lines through the left / right silhouette edges of the lower wall rows
        ry_guess = int(ov.get("roof_y", stage.get("roof_y", ry0)))
        rows = range(ry_guess + (base - ry_guess) // 5, base - max(3, (base - ry_guess) // 8))
        L, R, Y = [], [], []
        for y in rows:
            xs = np.where(op[y])[0]
            if len(xs):
                L.append(xs[0]); R.append(xs[-1] + 1); Y.append(y)
        wid = (np.median(R) - np.median(L))
        if "wall_x" in ov:
            lines = [(float(ov["wall_x"][0]), 0.0), (float(ov["wall_x"][1]), 0.0)]
        else:
            lines = [fit_line(Y, L, max(4, 0.04 * wid)), fit_line(Y, R, max(4, 0.04 * wid))]
        # wall top: the eave underside just outside each wall (the overhang's lowest row), else the guess
        if "roof_y" in ov:
            ry = int(ov["roof_y"])
        else:
            cand = []
            for k, (aa, bb) in enumerate(lines):
                sgn = -1 if k == 0 else 1
                bots = []
                for off in range(3, 10):
                    x = int(round(aa + bb * ry_guess + sgn * off))
                    if not (0 <= x < w):
                        continue
                    col = op[:, x]
                    ys = np.where(col)[0]
                    if not len(ys):
                        continue
                    run = ys[np.concatenate([[True], np.diff(ys) == 1]).cumprod().astype(bool)]
                    bots.append(int(run[-1]) + 1)
                if bots:
                    bt = int(np.median(bots))
                    if top + 0.12 * (base - top) < bt < base - 0.25 * (base - top):
                        cand.append(bt)
            ry = max(cand) if cand else ry_guess
        wx = lambda k, y: lines[k][0] + lines[k][1] * y
        roof_raw = op.copy()
        roof_raw[ry + 1:] = False
        roof_clean = opening(roof_raw, max(3, int(0.018 * w)))
        roof = roof_raw.copy()
        chim = []
        wx0, wx1 = int(round(wx(0, ry))), int(round(wx(1, ry)))
        if not ov.get("no_chimney"):
            chim = [list(c) for c in ov["chimneys"]] if "chimneys" in ov else find_chimneys(roof_clean, ry, wx0, wx1, base, ov)
            for c in chim:
                x0, x1 = c[0], c[2]
                tl = first_row(roof[:, max(0, x0 - 2)])
                tr = first_row(roof[:, min(w - 1, x1 + 1)])
                tl = ry if tl > ry else tl
                tr = ry if tr > ry else tr
                for x in range(max(0, x0), min(w, x1)):
                    f = (x - x0 + 0.5) / max(1, x1 - x0)
                    t = int(round(tl + (tr - tl) * f))
                    roof[:t, x] = False
                    roof[t:ry + 1, x] = True
        wall = Image.new("L", (w, h), 0)
        ImageDraw.Draw(wall).polygon([(wx(0, ry - 1), ry - 1), (wx(1, ry - 1), ry - 1), (wx(1, base), base),
                                      (wx(0, base), base)], fill=255)
        M = roof | (np.asarray(wall) > 127)
        M[base:] = False
        lab2, s2 = components(M)
        cx = int((wx0 + wx1) / 2)
        keep = lab2[min(base - 2, (ry + base) // 2), cx]
        M = lab2 == keep
        M = fill_holes(M)
        # close pinches and pad 1 px so HouseBody covers PaperCard's downscaled contour edge
        M = morph(morph(np.pad(M, 4), 3, "dilate"), 3, "erode")[4:-4, 4:-4] & True
        M = morph(np.pad(M, 4), 3, "dilate")[4:-4, 4:-4] & True
        M[base:] = False
        M = fill_holes(M)
        poly = simplify_loop(trace(M), 0.6)
    for c in chim:  # seat: the deepest roof row under the stack (it sinks into the roof)
        under = [first_row(M[:, x]) for x in range(max(0, c[0]), min(w, c[2]))]
        under = [u for u in under if u < h]
        c[3] = int(max(under)) + 3 if under else c[3]
    mats = classify(poly, lines, ry, base)
    mask = M
    # side tile: the most wall-like patch (closest to the wall's dominant colour, least detail), mirror-tiled
    wx0 = int(round(lines[0][0] + lines[0][1] * ry))
    wx1 = int(round(lines[1][0] + lines[1][1] * ry))
    wall_reg = np.zeros((h, w), bool)
    if "side_rect" in ov:
        sx0, sy0, sx1, sy1 = ov["side_rect"]
        wall_reg[max(0, sy0):min(h, sy1), max(0, sx0):min(w, sx1)] = True
    else:
        wall_reg[ry + 3:base - 3, max(0, wx0 + 3):max(0, wx1 - 3)] = True
    # small patches: a plain piece of wall exists between the windows and painted flowers (mirror-tiled it reads as
    # the plain wall material; a bigger patch dragged a sunflower or a log end along every side wall)
    side = None
    for frac in (0.12, 0.08, 0.05):
        pw = max(10, int(min((wx1 - wx0) * frac, (base - ry) * 0.4)))
        side = find_patch(arr, wall_reg & M & (arr[..., 3] > 200), pw, pw)
        if patch_ok(arr, wall_reg & M & (arr[..., 3] > 200), side):
            break
    # roof tile: the same search over the roof (between the roof line and the eaves, chimneys excluded)
    tops = np.array([first_row(M[:, x]) for x in range(w)])
    rtop = int(tops.min())
    roof_reg = np.zeros((h, w), bool)
    for x in range(w):
        if tops[x] < ry - 4 and not any(c[0] - 4 <= x < c[2] + 4 for c in chim):
            # the outer band just under the roof line: roofing on every kind of front (dormers sit lower)
            roof_reg[tops[x] + 2:tops[x] + 2 + max(6, int((ry - tops[x]) * 0.42)), x] = True
    roof_reg &= M & (arr[..., 3] > 200)
    rph = max(8, int((ry - rtop) * 0.2))
    roofc = find_patch(arr, roof_reg, max(10, int(rph * 1.8)), rph) if roof_reg.sum() > 200 else side.copy()
    # back: own gable / roof print above the wall top, plain wall tile below, body outline as alpha
    tile = mirror_tile(side)
    th, tw = tile.shape[:2]
    fill = np.zeros_like(arr)
    for y in range(h):
        fill[y] = np.tile(tile[y % th], (w // tw + 2, 1))[:w]
    back = fill.copy()
    back[:ry] = np.where((arr[:ry, :, 3:4] > 200), arr[:ry], fill[:ry])
    back[..., 3] = np.where(mask, 255, 0)
    chim_tex = None
    if chim:
        c = chim[0]
        ct = arr[c[1]:max(c[1] + 4, min(c[3], ry)), max(0, c[0]):c[2]].copy()
        aa = ct[..., 3] > 200
        if aa.any():
            ct[~aa, :3] = ct[aa][:, :3].mean(0)
        ct[..., 3] = 255
        chim_tex = ct
    sheet_dir = e.get("_dir")
    od = os.path.join(ROOT, "game", sheet_dir, "bodies")
    os.makedirs(od, exist_ok=True)
    rel = f"{sheet_dir}/bodies/"
    files = {}
    for k, img in (("side", mirror_tile(side)), ("roof", mirror_tile(roofc)), ("back", back), ("chimney", chim_tex)):
        if img is None:
            continue
        fn = f"{cid}_{k}.webp"
        Image.fromarray(img).save(os.path.join(od, fn), "WEBP", lossless=True, quality=100, method=6)
        files[k + "_file"] = rel + fn
    out = {"px": [w, h], "base_y": base, "roof_y": int(ry), "wall_lines": [[round(a, 3), round(b, 5)] for a, b in lines],
           "poly": [[int(x), int(y)] for x, y in poly], "mats": mats, "chimneys": chim,
           "depth": float(ov.get("depth", DEPTH)), "side_px": [int(side.shape[1]), int(side.shape[0])],
           "roof_px": [int(roofc.shape[1]), int(roofc.shape[0])]}
    # the template draws the rim-stripped copy (game/art/atlas_clean, cropped): its px = these px - clean_off
    cp = os.path.join(ROOT, "game", e["path"].replace("art/atlas/", "art/atlas_clean/"))
    if cp != os.path.join(ROOT, "game", e["path"]) and os.path.exists(cp):
        ca = np.asarray(Image.open(cp).convert("RGBA"))[..., 3] > 90
        ys2, xs2 = np.nonzero(ca)
        ys1, xs1 = np.nonzero(arr[..., 3] > 90)
        out["clean_off"] = [int(xs1.min() - xs2.min()), int(ys1.min() - ys2.min())]
        # the stripped rim: how much smaller the clean silhouette is (px per side)
        out["clean_rim"] = round(max(0.0, ((xs1.max() - xs1.min()) - (xs2.max() - xs2.min())) / 2.0), 1)
        out["clean_px"] = [int(ca.shape[1]), int(ca.shape[0])]
    out.update(files)
    if ov.get("roof_mat"):  # tools/atlas/building_kit.py tiles (2x2 mirrored swatches)
        tp = os.path.join(ROOT, "game", "art", "buildings", "tiles", ov["roof_mat"] + ".webp")
        tw = Image.open(tp).size[0] // 2
        s_est = float(e.get("height_units", 0.7)) * 1.25 / max(1, base - rtop)
        k = max(1, int(round(0.13 / s_est)))  # one swatch ~0.26 world wide
        out["roof_file"] = f"art/buildings/tiles/{ov['roof_mat']}.webp"
        out["roof_px"] = [k, k]
    return out, (im, poly, ry, (wx0, wx1), chim, side, roofc, back, mats)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sheet = sys.argv[sys.argv.index("--sheet") + 1] if "--sheet" in sys.argv else None
    if sheet in args:
        args.remove(sheet)
    ids = args or IDS
    cat = {}
    for e in json.load(open(os.path.join(ATLAS, "catalog.json"))):
        e = dict(e)
        e["_dir"] = f"art/atlas/{e['sheet']}"
        cat[e["id"]] = e
    for e in json.load(open(os.path.join(ROOT, "game", "art", "cards", "catalog.json"))):
        e = dict(e)
        e["path"] = e["path"].replace("res://", "")
        e["_dir"] = os.path.dirname(e["path"])
        e["sheet"] = ""
        cat[e["id"]] = e
    old = json.load(open(OUT_JSON)) if os.path.exists(OUT_JSON) else {}
    cells = []
    for cid in ids:
        if cid not in cat:
            print("no card", cid)
            continue
        e = cat[cid]
        sp = os.path.join(ROOT, "game", e["_dir"], "stages", "stages.json")
        stage = json.load(open(sp)).get(cid, {}) if os.path.exists(sp) else {}
        st, viz = build(cid, e, stage)
        old[cid] = st
        cells.append((cid, viz))
        print(cid, "roof_y", st["roof_y"], "wall", st["wall_lines"], "base", st["base_y"], "poly", len(st["poly"]),
              "chimneys", st["chimneys"])
    # merge-only write (re-read just before writing: other sessions may have added entries)
    cur = json.load(open(OUT_JSON)) if os.path.exists(OUT_JSON) else {}
    for cid, _ in cells:
        cur[cid] = old[cid]
    json.dump(cur, open(OUT_JSON, "w"), indent=1)
    if sheet:
        cw, ch, ncol = 360, 300, 6
        rows = (len(cells) + ncol - 1) // ncol
        S = Image.new("RGB", (cw * ncol, ch * rows), (52, 52, 60))
        dr = ImageDraw.Draw(S)
        for i, (cid, (im, poly, ry, wx, chim, side, roofc, back, mats)) in enumerate(cells):
            c = Image.new("RGBA", im.size, (95, 95, 105, 255))
            c.alpha_composite(im)
            d = ImageDraw.Draw(c)
            colm = [(255, 255, 255, 255), (0, 255, 255, 255), (255, 0, 255, 255), (60, 60, 60, 255)]
            for k in range(len(poly)):
                d.line([tuple(poly[k]), tuple(poly[(k + 1) % len(poly)])], fill=colm[mats[k]], width=2)
            d.line([(0, ry), (im.width, ry)], fill=(255, 0, 0, 255), width=1)
            for q in chim:
                d.rectangle(q, outline=(255, 255, 0, 255), width=2)
            c.thumbnail((cw - 110, ch - 20))
            x, y = (i % ncol) * cw, (i // ncol) * ch
            S.paste(c.convert("RGB"), (x, y))
            b = Image.fromarray(back)
            bb = Image.new("RGBA", b.size, (95, 95, 105, 255))
            bb.alpha_composite(b)
            bb.thumbnail((105, 100))
            S.paste(bb.convert("RGB"), (x + cw - 108, y))
            s2 = Image.fromarray(side)
            s2.thumbnail((50, 90))
            S.paste(s2.convert("RGB"), (x + cw - 108, y + 105))
            r2 = Image.fromarray(roofc)
            r2.thumbnail((100, 50))
            S.paste(r2.convert("RGB"), (x + cw - 108, y + 200))
            dr.text((x + 4, y + ch - 16), cid, fill=(255, 255, 255))
        os.makedirs(os.path.dirname(os.path.abspath(sheet)), exist_ok=True)
        S.save(sheet, quality=88)
        print("contact", sheet)


if __name__ == "__main__":
    main()

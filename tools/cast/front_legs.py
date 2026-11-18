#!/usr/bin/env python3
"""Swap every traveller figure's leg_l / leg_r for FRONT-VIEW legs (boot toes toward the reader, no 팔자 splay).

  python3 tools/atlas/slice_atlas.py art_src/cast/raw/cast_traveller_legs_front.png --out art_src/cast/sliced
  python3 tools/cast/front_legs.py            (run after tools/cast/cut_cast_rig.py; cut_cast_rig calls it itself)

2026-11-18: the figures were drawn standing with side-view boots pointing outward, so the walk toward the camera read as
a duck walk. Sheet cast_traveller_legs_front (tools/cast/make_jobs.py) = 4 legs: coat trousers L, R; no-coat trousers
(ochre outer seam) L, R. Each figure keeps its hip pivot and leg length; the new leg is scaled so its sole sits on the
old sole line and its width at the first visible row (rig.json parts.leg_*.vis, just below the coat hem / at the crotch)
matches the old leg there, then centred on that span. The top is capped round (hidden behind the body/hips anyway) like
the cutter's. The side-view legs from the cutter are kept in art_src/cast/legs_side/ (backup, not used).
"""
import json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from characters import CHARS, char_of, is_front, sliced_path

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RIG = os.path.join(ROOT, "game", "art", "cast", "rig")
SRC = os.path.join(ROOT, "game", "art", "cast")
SL = os.path.join(ROOT, "art_src", "cast", "sliced", "cast_traveller_legs_front")
BACKUP = os.path.join(ROOT, "art_src", "cast", "legs_side")
PIECES = {("coat", "leg_l"): 0, ("coat", "leg_r"): 1, ("nocoat", "leg_l"): 2, ("nocoat", "leg_r"): 3}


def row_span(alpha, y):
    xs = np.where(alpha[y] > 128)[0]
    return (int(xs[0]), int(xs[-1]) + 1) if len(xs) else None


def fit_leg(piece, hip_y, sole_y, vis_y, vx0, vx1):
    """Scale + place piece (RGBA array, tight) in figure px: top at or above hip_y, sole at sole_y, span [vx0,vx1) at vis_y."""
    ph, pw = piece.shape[:2]
    top_y = hip_y - 4
    s = (sole_y - top_y) / ph
    # the piece row that lands on vis_y, and its width there
    r = int(round((vis_y - top_y) / s))
    r = min(max(r, 0), ph - 1)
    sp = row_span(piece[..., 3], r)
    pw_vis = (sp[1] - sp[0]) if sp else pw
    sx = (vx1 - vx0) / (pw_vis * s)
    sx = float(np.clip(sx, 0.8, 1.25))
    nw, nh = max(1, round(pw * s * sx)), sole_y - top_y
    im = Image.fromarray(piece).resize((nw, nh), Image.LANCZOS)
    a = np.array(im)
    # round cap at the top (like the cutter's hidden leg top), so a swung leg's corner never pokes past the body
    rr = nw / 2.0
    for y in range(int(rr)):
        dy = rr - y
        half = max(0.0, rr * rr - dy * dy) ** 0.5
        xs = np.arange(nw) + 0.5
        cut = np.abs(xs - nw / 2.0) > half + 0.5
        a[y, cut, 3] = 0
    # centre the visible span: the piece's span at vis row, scaled
    c_piece = ((sp[0] + sp[1]) / 2.0 if sp else pw / 2.0) * s * sx
    x0 = int(round((vx0 + vx1) / 2.0 - c_piece))
    return a, x0, top_y, s, sx, int(round(boot_row(piece) * s))


def boot_row(piece):
    """First piece row of the boot: where the trouser cuff ends and the leg narrows (> 12 %) into the boot shaft."""
    al = piece[..., 3] > 200
    w = al.sum(1).astype(float)
    h = len(w)
    for y in range(int(h * 0.5), int(h * 0.9)):
        if w[y] < 0.88 * np.median(w[int(h * 0.55):y]) if y > int(h * 0.55) + 4 else False:
            return y
    return int(h * 0.72)


def region_med(fig, y0, y1, x0, x1):
    blk = fig[y0:y1, x0:x1]
    m = blk[..., 3] > 220
    return np.median(blk[..., :3][m], 0) if m.sum() > 20 else None


def match_colours(a, by, fig, vis_y, vx0, vx1, sole_y, xa, xb):
    """Per-channel gain so the new trouser / boot match this figure's own trouser / boot print (sampled from the figure)."""
    L = sole_y - vis_y
    cx, hw = (vx0 + vx1) / 2.0, (vx1 - vx0) / 4.0
    tro_old = region_med(fig, vis_y + 3, vis_y + max(6, int(0.25 * L)), int(cx - hw), int(cx + hw))
    al = fig[..., 3] > 220
    yb0, yb1 = sole_y - int(0.30 * L), sole_y - int(0.14 * L)
    xs = np.where(al[yb0:yb1, xa:xb].any(0))[0]
    boot_old = None
    if len(xs):
        bx0, bx1 = xa + xs[0], xa + xs[-1]
        q = (bx1 - bx0) // 4
        boot_old = region_med(fig, yb0, yb1, bx0 + q, bx1 - q)
    h = a.shape[0]
    rows = np.arange(h)
    wb = np.clip((rows - (by - 3)) / 6.0, 0, 1)[:, None]  # 0 trouser .. 1 boot
    out = a[..., :3].astype(float)
    gains = []
    for old, sel in ((tro_old, rows < by - 4), (boot_old, rows > by + 8)):
        new = region_med(a, int(rows[sel][0]), int(rows[sel][-1]) + 1, a.shape[1] // 4, 3 * a.shape[1] // 4)
        g = np.ones(3) if old is None or new is None else np.clip(old / np.maximum(new, 1), 0.7, 1.4)
        gains.append(g)
    g = gains[0][None, :] * (1 - wb) + gains[1][None, :] * wb
    a[..., :3] = np.clip(out * g[:, None, :], 0, 255).astype(np.uint8)
    return gains


def load_pieces(ch, variant):
    """{(kind, side): tight RGBA array} of a character's leg sheet (characters.CHARS)."""
    sheet = ch["legs"][variant]
    out = {}
    for k, idx in ch["pieces"].items():
        im = np.array(Image.open(sliced_path(sheet, idx, ch["order"])).convert("RGBA"))
        ys, xs = np.where(im[..., 3] > 8)
        out[k] = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return out


def main():
    rig_p = os.path.join(RIG, "rig.json")
    rig = json.load(open(rig_p))
    os.makedirs(BACKUP, exist_ok=True)
    # 2026-11-18: per character (tools/cast/characters.py); the traveller entry = the original single-character path
    for cname, ch in CHARS.items():
        if not os.path.isdir(os.path.join(os.path.dirname(SL), ch["legs"]["front"])):
            continue
        if any(char_of(f) == cname and is_front(f) for f in rig):
            main_char(rig, cname, ch)
    json.dump(rig, open(rig_p, "w"), indent=1)


def main_char(rig, cname, ch):
    pieces = load_pieces(ch, "front")
    for fid, r in rig.items():
        if char_of(fid) != cname or not is_front(fid):
            continue
        kind = ch["kind"](fid)
        for side in ("leg_l", "leg_r"):
            p = r["parts"][side]
            name = f"{fid}_{side}.png"
            if "vis" not in p:
                raise RuntimeError(f"{fid}: rig.json has no vis row; re-run tools/cast/cut_cast_rig.py")
            if not p.get("front"):  # the cutter just wrote the side-view leg: keep it
                shutil.copyfile(os.path.join(RIG, name), os.path.join(BACKUP, name))
            hip_x, hip_y = p["hip"]
            vis_y, vx0, vx1 = p["vis"]
            sole_y = r["full_bbox"][3]
            top_y = hip_y - int(round(0.035 * (r["full_bbox"][3] - r["full_bbox"][1])))
            a, x0, ty, s, sx, by = fit_leg(pieces[(kind, side)], top_y + 4, sole_y, vis_y, vx0, vx1)
            fig = np.array(Image.open(os.path.join(SRC, fid + ".webp")).convert("RGBA"))
            xa, xb = (0, r["split"]) if side == "leg_l" else (r["split"], fig.shape[1])
            gains = match_colours(a, by, fig, vis_y, vx0, vx1, sole_y, xa, xb) if ch["match"] else [np.ones(3)]
            ys, xs = np.where(a[..., 3] > 8)
            a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            bb = [x0 + int(xs.min()), ty + int(ys.min()), x0 + int(xs.max()) + 1, ty + int(ys.max()) + 1]
            Image.fromarray(a).save(os.path.join(RIG, name))
            p["bbox"] = bb
            p["front"] = True
            print(f"{fid} {side} scale {s:.3f} x{sx:.3f} gain {np.round(gains, 2).tolist()} bbox {bb} hip {p['hip']}")


if __name__ == "__main__":
    main()

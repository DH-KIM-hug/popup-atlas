#!/usr/bin/env python3
"""Bent-knee leg cards for the front-facing walk (swapped in by CastPuppet while a foot is up).

  python3 tools/atlas/slice_atlas.py art_src/cast/raw/cast_traveller_legs_half.png --out art_src/cast/sliced
  python3 tools/atlas/slice_atlas.py art_src/cast/raw/cast_traveller_legs_lift.png --out art_src/cast/sliced
  python3 tools/cast/lift_legs.py          (after front_legs.py; cut_cast_rig.py calls it itself)

2026-11-18 (user: "잘린 다리가 코트 위를 삐져나와서 이상해"): the swing leg used to be the straight front leg slid up and
squashed, which showed its cut top / cuff band under the coat hem. Now each figure gets two pre-drawn variants per leg
(Codex sheets cast_traveller_legs_half / _lift, same 4-piece order as cast_traveller_legs_front: coat L, R, no-coat L, R):
  half = knee slightly bent (natural length 0.90 of the straight hip→sole), lift = knee up, foot toward us (0.76).
Each variant is fitted exactly like front_legs.fit_leg: same top line (hidden under the coat / hips piece), same width
at the first visible row, hip pivot unchanged, sole at hip + ratio × (sole - hip). Colours are matched per row class
(trouser / boot) to that figure's final straight leg. rig.json parts.leg_*.alt = {half: {bbox, ratio}, lift: {...}}.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import front_legs as fl

ROOT = fl.ROOT
RIG = fl.RIG
SLICED = os.path.join(ROOT, "art_src", "cast", "sliced")
VARIANTS = {"half": ("cast_traveller_legs_half", 0.90), "lift": ("cast_traveller_legs_lift", 0.76)}


def load_pieces(sheet):
    out = {}
    for k, idx in fl.PIECES.items():
        im = np.array(Image.open(os.path.join(SLICED, sheet, f"{sheet}_{idx:02d}.webp")).convert("RGBA"))
        ys, xs = np.where(im[..., 3] > 8)
        out[k] = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return out


def row_classes(a):
    """Per row: True = boot (dark plum-brown), from the row median colour vs the bottom (boot) and top (trouser) colours."""
    h = a.shape[0]
    med = np.zeros((h, 3))
    for y in range(h):
        m = a[y, :, 3] > 200
        med[y] = np.median(a[y, m, :3], 0) if m.sum() > 3 else med[y - 1] if y else 0
    trou = np.median(med[int(h * 0.1):int(h * 0.3)], 0)
    boot = np.median(med[int(h * 0.80):int(h * 0.92)], 0)
    isb = np.linalg.norm(med - boot, axis=1) < np.linalg.norm(med - trou, axis=1)
    # boot start = the split row with the fewest misclassified rows (boot rows above it + trouser rows below it),
    # searched in the lower half (stitches, creases and the sole rim make single rows noisy)
    best, first = None, h - 1
    for y in range(h // 2, h - 4):
        err = int(isb[h // 2:y].sum()) + int((~isb[y:]).sum())
        if best is None or err < best:
            best, first = err, y
    return first


def region(a, y0, y1):
    blk = a[max(0, y0):max(y0 + 1, y1), a.shape[1] // 4: 3 * a.shape[1] // 4]
    m = blk[..., 3] > 220
    return np.median(blk[..., :3][m], 0) if m.sum() > 20 else None


def stats(a, y0, y1):
    blk = a[max(0, y0):max(y0 + 1, y1), a.shape[1] // 5: 4 * a.shape[1] // 5]
    m = blk[..., 3] > 220
    if m.sum() < 20:
        return None
    px = blk[..., :3][m].astype(float)
    return px.mean(0), px.std(0) + 1.0


def match_to(a, ref):
    """Per-channel mean/std transfer: trouser rows of `a` to the trouser of `ref` (that figure's final straight leg),
    boot rows to its boot (median gains left the no-coat lift trousers visibly darker/greyer than the straight leg)."""
    ba, br = row_classes(a), row_classes(ref)
    ha, hr = a.shape[0], ref.shape[0]
    out = a[..., :3].astype(float)
    res = []
    for (ya0, ya1), (yr0, yr1) in (((int(ha * 0.12), ba - 6), (int(hr * 0.12), br - 6)), ((ba + 4, ha - 6), (br + 4, hr - 6))):
        sa, sr = stats(a, ya0, ya1), stats(ref, yr0, yr1)
        if sa is None or sr is None:
            res.append(None)
            continue
        k = np.clip(sr[1] / sa[1], 0.6, 1.6)
        res.append((sa[0], sr[0], k))
    rows = np.arange(ha)
    wb = np.clip((rows - (ba - 3)) / 6.0, 0, 1)[:, None, None]
    conv = []
    for r in res:
        conv.append(out if r is None else (out - r[0]) * r[2] + r[1])
    out = conv[0] * (1 - wb) + conv[1] * wb
    a[..., :3] = np.clip(out, 0, 255).astype(np.uint8)
    return [None if r is None else np.round(r[1] - r[0]).tolist() for r in res]


def main():
    rig_p = os.path.join(RIG, "rig.json")
    rig = json.load(open(rig_p))
    sheets = {v: load_pieces(sh) for v, (sh, _) in VARIANTS.items()}
    for fid, r in rig.items():
        if not fid.startswith("cast_traveller"):
            continue
        kind = "nocoat" if "_nocoat" in fid else "coat"
        H = r["full_bbox"][3] - r["full_bbox"][1]
        for side in ("leg_l", "leg_r"):
            p = r["parts"][side]
            hip_x, hip_y = p["hip"]
            vis_y, vx0, vx1 = p["vis"]
            sole_y = r["full_bbox"][3]
            top_y = hip_y - int(round(0.035 * H))
            ref = np.array(Image.open(os.path.join(RIG, f"{fid}_{side}.png")).convert("RGBA"))
            alt = {}
            for v, (_, ratio) in VARIANTS.items():
                sole_v = int(round(hip_y + ratio * (sole_y - hip_y)))
                a, x0, ty, s, sx, _ = fl.fit_leg(sheets[v][(kind, side)], top_y + 4, sole_v, vis_y, vx0, vx1)
                g = match_to(a, ref)
                ys, xs = np.where(a[..., 3] > 8)
                a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
                bb = [x0 + int(xs.min()), ty + int(ys.min()), x0 + int(xs.max()) + 1, ty + int(ys.max()) + 1]
                Image.fromarray(a).save(os.path.join(RIG, f"{fid}_{side}_{v}.png"))
                alt[v] = {"bbox": bb, "ratio": ratio}
                print(f"{fid} {side} {v} bbox {bb} gain {np.round(g, 2).tolist()}")
            p["alt"] = alt
    json.dump(rig, open(rig_p, "w"), indent=1)


if __name__ == "__main__":
    main()

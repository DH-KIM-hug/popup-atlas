#!/usr/bin/env python3
"""Match the three_pigs walkers' drawn leg cards to their own figure's colours (2026-11-22, paper look).

  python3 tools/cast/match_leg_skin.py          (after tools/cast/cut_cast_rig.py; idempotent)

The front / half / lift / side leg cards come from separate leg sheets (cast_tp_legs_*), so on the paper redraw they
came out warmer than the bodies. For every rigged pig / wolf figure and each leg card: the card's pixels are split by
colour into classes (pig skin, overall denim / red, wolf grey fur, cream fur); each class present in both the leg card
and the figure's body card gets a per-channel gain so its median matches the body's median of the same class. Hooves /
paws (dark) are left alone. The original leg cards are kept once in art_src/cast/legs_unmatched/.
"""
import json, os, shutil
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RIG = os.path.join(ROOT, "game", "art", "cast", "rig")
BACK = os.path.join(ROOT, "art_src", "cast", "legs_unmatched")


def hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(-1), rgb.min(-1)
    ch = mx - mn + 1e-6
    h = np.zeros_like(mx)
    rm = mx == r
    gm = (mx == g) & ~rm
    bm = ~rm & ~gm
    h[rm] = (60 * (g[rm] - b[rm]) / ch[rm]) % 360
    h[gm] = 60 * (b[gm] - r[gm]) / ch[gm] + 120
    h[bm] = 60 * (r[bm] - g[bm]) / ch[bm] + 240
    return h, ch / np.maximum(mx, 1e-6), mx


CLASSES = {  # name -> predicate on (hue, sat, value 0..255)
    "skin": lambda h, s, v: ((h < 32) | (h > 345)) & (s > 0.18) & (s < 0.62) & (v > 150),
    "blue": lambda h, s, v: (h > 185) & (h < 235) & (s > 0.2) & (v > 80),
    "red": lambda h, s, v: ((h < 15) | (h > 345)) & (s >= 0.62) & (v > 90),
    "grey": lambda h, s, v: (s < 0.14) & (v > 80) & (v < 200),
    "cream": lambda h, s, v: (s < 0.3) & (v >= 200),
}


def masks(a):
    rgb = a[..., :3].astype(np.float32)
    h, s, v = hsv(rgb)
    op = a[..., 3] > 200
    return {k: op & f(h, s, v) for k, f in CLASSES.items()}


def main():
    rig = json.load(open(os.path.join(RIG, "rig.json")))
    os.makedirs(BACK, exist_ok=True)
    n = 0
    for fid in rig:
        if not (fid.startswith("cast_pig_") or fid.startswith("cast_wolf_")):
            continue
        body = np.asarray(Image.open(os.path.join(RIG, f"{fid}_body.png")).convert("RGBA"))
        hips_p = os.path.join(RIG, f"{fid}_hips.png")
        ref = [body] + ([np.asarray(Image.open(hips_p).convert("RGBA"))] if os.path.exists(hips_p) else [])
        refm = {k: np.concatenate([r[..., :3][masks(r)[k]] for r in ref]) for k in CLASSES}
        for side in ("leg_l", "leg_r"):
            for suf in ("", "_half", "_lift"):
                p = os.path.join(RIG, f"{fid}_{side}{suf}.png")
                if not os.path.exists(p):
                    continue
                bk = os.path.join(BACK, os.path.basename(p))
                if not os.path.exists(bk):
                    shutil.copy2(p, bk)
                a = np.array(Image.open(bk).convert("RGBA"))
                out = a[..., :3].astype(np.float32)
                gains = {}
                for k, m in masks(a).items():
                    if m.sum() < 40 or len(refm[k]) < 200:
                        continue
                    g = np.clip(np.median(refm[k], 0) / np.maximum(np.median(a[..., :3][m], 0), 1), 0.75, 1.3)
                    out[m] *= g
                    gains[k] = np.round(g, 2).tolist()
                a[..., :3] = np.clip(out, 0, 255).astype(np.uint8)
                Image.fromarray(a).save(p)
                n += 1
                if suf == "":
                    print(fid, side, gains)
    print(n, "leg cards matched")


if __name__ == "__main__":
    main()

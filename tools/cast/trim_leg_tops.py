#!/usr/bin/env python3
"""Trim the hidden top of front-view leg cards to what the body + hips cards cover at rest.

  python3 tools/cast/trim_leg_tops.py cast_wolf_calm cast_wolf_shout

The front legs (front_legs.py / lift_legs.py) are generated wider than some figures' thighs; above the hem (rig.json
leg `vis` row) the leg card must be hidden behind the body / hips, but where the body card has no pixels (the wolf's
left thigh beside his tail) a strip of leg card showed: "a sliver beside the thigh" (2026-11-18 three_pigs phase 2).
For every leg card (straight, half, lift) rows above the hem keep only pixels covered by body or hips (alpha > 0),
except a taper just above the hem (TAPER px) where the allowed span widens linearly from the covered thigh run to
the leg's own width at the hem, so the leg reads as a calf flaring out of the thigh instead of a step.
Run after cut_cast_rig.py for figures that need it (idempotent).
"""
import json, os, sys
import numpy as np
from PIL import Image

TAPER = 46
RIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "game", "art", "cast", "rig")


def trim(key, rig):
    e = rig[key]
    W, H = e["size"]
    cover = np.zeros((H, W), bool)
    for part in ("body", "hips"):
        bb = e["parts"][part]["bbox"]
        a = np.array(Image.open(os.path.join(RIG, f"{key}_{part}.png")).convert("RGBA"))[..., 3] > 8
        cover[bb[1]:bb[1] + a.shape[0], bb[0]:bb[0] + a.shape[1]] |= a
    n = 0
    for side in ("leg_l", "leg_r"):
        p = e["parts"][side]
        vis = int(p.get("vis", [p["hip"][1]])[0]) - 6
        cards = [(f"{key}_{side}.png", p["bbox"])]
        for v, alt in p.get("alt", {}).items():
            cards.append((f"{key}_{side}_{v}.png", alt["bbox"]))
        for fn, bb in cards:
            path = os.path.join(RIG, fn)
            im = np.array(Image.open(path).convert("RGBA"))
            h, w = im.shape[:2]
            rows = max(0, min(h, vis - bb[1]))
            hx = int(p["hip"][0]) - bb[0]  # hip column in card px
            a = im[..., 3] > 0
            hem = min(h - 1, rows)
            lc = np.where(a[hem])[0]
            if lc.size == 0:
                continue
            l1, r1 = int(lc[0]), int(lc[-1])  # leg span at the hem
            kill = np.zeros_like(a)
            for y in range(rows):
                cov = cover[bb[1] + y, bb[0]:bb[0] + w] if bb[1] + y < H else np.zeros(w, bool)
                cov = cov[:w]
                # covered run through the hip column (the thigh), else nothing
                l0, r0 = hx, hx - 1
                if 0 <= hx < w and cov[hx]:
                    l0 = hx
                    while l0 > 0 and cov[l0 - 1]:
                        l0 -= 1
                    r0 = hx
                    while r0 < w - 1 and cov[r0 + 1]:
                        r0 += 1
                u = (y - (rows - TAPER)) / TAPER
                if u > 0 and r0 >= l0:
                    lo = int(round(l0 + (min(l0, l1) - l0) * u))
                    hi = int(round(r0 + (max(r0, r1) - r0) * u))
                    keep = np.zeros(w, bool)
                    keep[max(lo, 0):hi + 1] = True
                    keep |= cov
                else:
                    keep = cov
                kill[y] = a[y] & ~keep
            n += int(kill.sum())
            im[kill] = 0
            Image.fromarray(im).save(path)
    print(key, "leg pixels trimmed", n)


if __name__ == "__main__":
    rig = json.load(open(os.path.join(RIG, "rig.json")))
    for k in sys.argv[1:]:
        trim(k, rig)

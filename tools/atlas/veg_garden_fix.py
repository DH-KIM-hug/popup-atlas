#!/usr/bin/env python3
"""After `add_sheet.py story_veg_garden` (2026-11-23): fill_holes restores the anti-aliased magenta rims of REAL holes
(wheel spokes, trellis gaps, between tomato stakes) and undoes the slicer's despill. This sheet has no purple except
the small turnips' blue-violet shoulders (dark, blue-leaning), so every light magenta-leaning pixel is key residue:
clear it (alpha 0) where it touches transparency, else pull it to the mean of its non-magenta neighbours.
  python3 tools/atlas/veg_garden_fix.py [sheet ...]   (default story_veg_garden story_veg_ground)"""
import glob, sys
import numpy as np
from PIL import Image
from PIL import ImageFilter


def dil(m, it=1):
    im = Image.fromarray(m.astype(np.uint8) * 255)
    for _ in range(it):
        im = im.filter(ImageFilter.MaxFilter(3))
    return np.asarray(im) > 127


def box(x, k=7):
    r = k // 2
    x = np.pad(x.astype(np.float64), r, mode="edge")
    c = np.cumsum(np.cumsum(np.pad(x, ((1, 0), (1, 0))), 0), 1)
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)

# the plot read bright orange under the warm key light: take it toward cocoa brown (saturation, value)
TONE = {"story_veg_ground_00": (0.8, 0.8), "story_veg_ground_02": (0.85, 0.85)}


def tone(p, sat, val):
    im = Image.open(p).convert("RGBA")
    a = np.asarray(im).astype(np.float64)
    rgb = a[..., :3]
    grey = rgb.mean(axis=2, keepdims=True)
    rgb = (grey + (rgb - grey) * sat) * val
    a[..., :3] = rgb
    Image.fromarray(a.clip(0, 255).astype(np.uint8)).save(p, "WEBP", lossless=True, quality=100, method=6)
    print(p, "toned", sat, val)


for sheet in (sys.argv[1:] or ["story_veg_garden", "story_veg_ground"]):
    for p in sorted(glob.glob(f"game/art/atlas/{sheet}/{sheet}_*.webp")):
        a = np.array(Image.open(p).convert("RGBA")).astype(np.int32)
        r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
        mag = (al > 0) & (r > 120) & (b > 90) & (g < np.minimum(r, b) - 40) & (r > b * 0.75)
        mag = dil(mag, 1) & (al > 0) & (g < np.minimum(r, b) - 15) & (b > g + 25)
        if not mag.any():
            continue
        clear = al < 128
        edge = mag & dil(clear, 3)
        # grow the cleared edge through connected residue
        a[edge, 3] = 0
        inner = mag & ~edge
        if inner.any():
            good = (al > 128) & ~mag
            for c in range(3):
                s = box(np.where(good, a[..., c], 0))
                n = box(good.astype(float))
                a[..., c] = np.where(inner & (n > 0.05), (s / np.maximum(n, 1e-3)).astype(np.int32), a[..., c])
        Image.fromarray(a.clip(0, 255).astype(np.uint8)).save(p, "WEBP", lossless=True, quality=100, method=6)
        print(p, "cleared", int(edge.sum()), "refilled", int(inner.sum()))

for cid, (sat, val) in TONE.items():
    sh = cid.rsplit("_", 1)[0]
    if sh in (sys.argv[1:] or ["story_veg_garden", "story_veg_ground"]):
        tone(f"game/art/atlas/{sh}/{cid}.webp", sat, val)

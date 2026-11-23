#!/usr/bin/env python3
"""Turnip v4 holes (2026-11-23, user on v3: "구멍을 그렇게 파니...? 너무 이상한데"): derived cards, no new generation.

- story_tn_garden_15  planting hole, TOP-DOWN (laid flat on the plot): a small dark dip cut from the dug-soil sheet
  (story_veg_ground_02), darker toward the bottom of the dip, a lit far lip and a shaded near lip.
- story_tn_garden_16  a tiny heap of loose soil (standing, low): story_tn_garden_05 with its burrow arch patched over
  with its own clumps and squashed to a low pile.
- story_tn_garden_17  the mouse hole, low: story_tn_garden_13 cut to a low bank (the top of the dome and its top grass
  gone), so the arch is most of the card; it sits tucked at the plot's rim between grass tufts.

Writes game/art/atlas/story_tn_garden/<id>.webp + catalog entries (merge-only: the catalog is re-read right before
writing). Run `--import` after.
  python3 tools/atlas/tn_holes.py
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ATLAS = os.path.join(ROOT, "game/art/atlas")
OUT = os.path.join(ATLAS, "story_tn_garden")
rng = np.random.default_rng(7)


def load(rel):
    return np.asarray(Image.open(os.path.join(ATLAS, rel)).convert("RGBA")).astype(np.float64)


def wobbly_ellipse(w, h, cx, cy, rx, ry, amp=0.06, n=7):
    """Alpha of a hand-cut ellipse (low-frequency wobble on the radius)."""
    yy, xx = np.mgrid[0:h, 0:w]
    ang = np.arctan2((yy - cy) / ry, (xx - cx) / rx)
    r = np.hypot((xx - cx) / rx, (yy - cy) / ry)
    wob = np.zeros_like(ang)
    for k in range(2, n):
        wob += rng.uniform(-1, 1) * amp / k * np.cos(k * ang + rng.uniform(0, 6.28))
    return r, (r < 1.0 + wob)


def planting_hole():
    src = load("story_veg_ground/story_veg_ground_02.webp")
    H, W = src.shape[:2]
    w, h = 200, 150
    x0, y0 = (W - w) // 2, (H - h) // 2
    tex = src[y0:y0 + h, x0:x0 + w, :3].copy()
    r, inside = wobbly_ellipse(w, h, w / 2, h / 2, w * 0.46, h * 0.44)
    # the dip: dark at the bottom (a little nearer than the centre: seen from the front, the far wall shows)
    yy, xx = np.mgrid[0:h, 0:w]
    rd = np.hypot((xx - w / 2) / (w * 0.30), (yy - h * 0.56) / (h * 0.27))
    depth = np.clip(1.0 - rd, 0.0, 1.0) ** 0.8
    shade = 1.0 - 0.72 * depth
    # the lips: the far lip (top of the image) catches the light, the near lip is in shade
    lip = np.clip((r - 0.72) / 0.28, 0, 1)
    far = np.clip(-(yy - h / 2) / (h / 2), 0, 1)
    shade *= 1.0 + 0.22 * lip * far - 0.12 * lip * (1 - far)
    rgb = tex * shade[..., None]
    rgb = rgb * np.array([0.92, 0.88, 0.86])  # damp, freshly dug: a touch cooler / darker than the plot
    a = np.where(inside, 255, 0).astype(np.uint8)
    a = np.asarray(Image.fromarray(a).filter(ImageFilter.GaussianBlur(0.8)))
    a = np.where(a > 128, 255, 0)
    out = np.dstack([rgb.clip(0, 255), a]).astype(np.uint8)
    return Image.fromarray(out)


def soil_heap():
    s = load("story_tn_garden/story_tn_garden_05.webp")
    h, w = s.shape[:2]
    # patch the arch (x 104..176, y 64..112) with clumps from the left flank, feathered in
    px0, px1, py0, py1 = 100, 180, 60, 114
    dx = -70
    patch = s[py0:py1, px0 + dx:px1 + dx, :3]
    r, m = wobbly_ellipse(px1 - px0, py1 - py0, (px1 - px0) / 2, (py1 - py0) / 2, (px1 - px0) * 0.5, (py1 - py0) * 0.5, amp=0.02)
    f = np.clip((1.05 - r) / 0.25, 0, 1)[..., None]
    reg = s[py0:py1, px0:px1, :3]
    s[py0:py1, px0:px1, :3] = reg * (1 - f) + patch * f
    im = Image.fromarray(s.clip(0, 255).astype(np.uint8))
    bb = im.getbbox()
    im = im.crop(bb)
    return im.resize((im.width, int(im.height * 0.55)), Image.LANCZOS)


def mouse_hole_low():
    s = load("story_tn_garden/story_tn_garden_13.webp")
    h, w = s.shape[:2]
    # a low bank: keep everything under a flat arc from (0, 168) over (166, 92) to (w, 168)
    yy, xx = np.mgrid[0:h, 0:w]
    cx, top, side = 166.0, 92.0, 168.0
    arc = top + (side - top) * ((xx - cx) / (w * 0.5)) ** 2
    jag = 2.0 * np.sin(xx * 0.31) + 1.5 * np.sin(xx * 0.13 + 1.0)  # a torn, hand-cut top edge
    keep = yy >= arc + jag
    a = s[..., 3] * keep
    # a narrow dark band along the new top edge (the cut through the soil, in shade)
    edge = keep & (yy < arc + jag + 4)
    s[..., :3] = np.where(edge[..., None], s[..., :3] * 0.72, s[..., :3])
    s[..., 3] = a
    im = Image.fromarray(s.clip(0, 255).astype(np.uint8))
    return im.crop(im.getbbox())


CARDS = [
    ("story_tn_garden_15", planting_hole, "small planting hole in tilled soil (top-down, lay flat)", "story_ground", 0.06,
     ["farm", "garden", "hole", "soil", "planting", "story", "turnip", "flat"]),
    ("story_tn_garden_16", soil_heap, "tiny low heap of loose dug soil", "story_prop", 0.03,
     ["farm", "garden", "soil", "heap", "story", "turnip"]),
    ("story_tn_garden_17", mouse_hole_low, "low grassy bank with a mouse hole", "story_prop", 0.05,
     ["farm", "garden", "mouse_hole", "story", "turnip"]),
]


def main():
    made = []
    for cid, fn, label, cat, hu, tags in CARDS:
        im = fn()
        p = os.path.join(OUT, cid + ".webp")
        im.save(p, "WEBP", lossless=True, quality=100, method=6)
        made.append({"id": cid, "path": f"art/atlas/story_tn_garden/{cid}.webp", "sheet": "story_tn_garden",
                     "category": cat, "label": label, "height_units": hu, "cross_slot": False, "biome": "meadow",
                     "season": "summer", "tags": tags, "px": [im.width, im.height]})
        print(cid, im.size)
    cpath = os.path.join(ATLAS, "catalog.json")
    cat = json.load(open(cpath))  # re-read right before writing (merge-only)
    ids = {e["id"] for e in made}
    cat = [e for e in cat if e["id"] not in ids] + made
    json.dump(cat, open(cpath, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""wolf_goats v2 (2026-11-24): cut the doorway hole into the cottage's lower wall band.

The band story_wg_cottage_00_b0.webp never had the hole house_stages.py cuts for DOORS (alpha 255 behind the leaf
since phase 1), so the painted door stayed on the wall while the leaf swung inward: the door always looked shut and
everyone walked through it (audit v1: "mom vanishes at the closed door"). Same leaf mask as house_stages.py DOORS.

  python3 tools/atlas/wg_door_hole.py
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ST = os.path.join(ROOT, "game/art/atlas/story_wg_cottage/stages")
cid = "story_wg_cottage_00"
d = json.load(open(os.path.join(ST, "stages.json")))[cid]
door = d["door"]
dx0, dx1, dy0, dbot = door["x0"], door["x1"], door["y0"], door["y1"]
for b in d["bands"]:
    p = os.path.join(ROOT, "game", b["file"])
    im = np.array(Image.open(p).convert("RGBA"))
    h, w = im.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    yy = yy + b["img_y0"]  # band rows in facade px
    r = (dx1 - dx0) / 2.0
    cx = (dx0 + dx1) / 2.0
    leaf = (xx >= dx0) & (xx < dx1) & (yy >= dy0) & (yy < dbot)
    leaf &= (yy >= dy0 + r) | ((xx + 0.5 - cx) ** 2 + (yy + 0.5 - (dy0 + r)) ** 2 <= r * r)
    n = int((leaf & (im[..., 3] > 0)).sum())
    if n:
        im[leaf] = 0
        Image.fromarray(im).save(p, "WEBP", lossless=True, quality=100, method=6)
    print(b["file"], "cleared", n)

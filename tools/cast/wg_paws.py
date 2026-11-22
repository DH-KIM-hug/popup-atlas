#!/usr/bin/env python3
"""wolf_goats (2026-11-23): the wolf's paw seen through the door gap from inside the cottage, cut from his shared
crouching figure (cast_wolf_paw_show: the forearm reaching forward with a floury white paw) -> tale art
game/stories/wolf_goats/art/paw_white.webp, and the same paw before the flour (white -> his grey fur) -> paw_grey.webp.
  python3 tools/cast/wg_paws.py
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
src = Image.open(os.path.join(ROOT, "game/art/cast/cast_wolf_paw_show.webp")).convert("RGBA")
a = np.array(src)
crop = a[300:432, 318:440].copy()
# keep only the arm: everything left of the diagonal from the elbow down is torso / leg
h, w = crop.shape[:2]
yy, xx = np.mgrid[0:h, 0:w]
crop[(xx < 0.55 * yy - 20), 3] = 0
out = os.path.join(ROOT, "game/stories/wolf_goats/art")
os.makedirs(out, exist_ok=True)
Image.fromarray(crop).save(os.path.join(out, "paw_white.webp"), "WEBP", lossless=True, quality=100, method=6)
# "발이 시커멓단다": the paw before the flour is a dark charcoal-brown (value kept as shading, darkened)
f = crop.astype(float)
lum = f[..., :3].mean(-1, keepdims=True)
white = (f[..., 3] > 0)
dark = np.array([74, 66, 62], float)
f[..., :3] = dark * (0.55 + 0.45 * lum / 230.0)
Image.fromarray(f.clip(0, 255).astype(np.uint8)).save(os.path.join(out, "paw_grey.webp"), "WEBP", lossless=True,
                                                          quality=100, method=6)
print("paws", crop.shape, int(white.sum()), "white px recoloured")

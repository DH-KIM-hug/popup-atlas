#!/usr/bin/env python3
"""Split a keyed card whose two objects touch, at the emptiest column inside [lo, hi] (fractions of width).
  python3 tools/art/split_manual.py sh2_conifers_b_04 0.5 0.75   -> <name>a.png, <name>b.png (trimmed, hinge kept)"""
import sys
import numpy as np
from PIL import Image
K = "/Users/house_of_4k2b/orca/popup-atlas/art_src/cards/keyed"
name, lo, hi = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
im = Image.open(f"{K}/{name}.png").convert("RGBA")
a = np.asarray(im)
col = (a[..., 3] > 40).sum(0)
x0, x1 = int(lo * a.shape[1]), int(hi * a.shape[1])
cut = x0 + int(np.argmin(col[x0:x1]))
for tag, part in (("a", a[:, :cut]), ("b", a[:, cut:])):
    al = part[..., 3] > 20
    ys, xs = np.nonzero(al)
    crop = part[max(0, ys.min() - 6):ys.max() + 1, max(0, xs.min() - 6):xs.max() + 7]
    Image.fromarray(crop, "RGBA").save(f"{K}/{name}{tag}.png")
    print(name + tag, crop.shape, "cut at", cut, "col px", col[cut])

#!/usr/bin/env python3
"""Single-character reference crops for 「라푼젤」 round-2 jobs: the k-th figure (left to right) of a raw sheet on
white, saved as art_src/cast/raw/ref_rp_<role>.png.  python3 tools/cast/rapunzel_refs.py"""
import numpy as np
from PIL import Image

R = "art_src/cast/raw/"
PICK = {"rap": ("cast_rp_rap_expr", 0), "gothel": ("cast_rp_gothel_expr", 0), "prince": ("cast_rp_prince_expr", 0),
        "father": ("cast_rp_father_expr", 0), "mother": ("cast_rp_mother_expr", 0),
        "rap_short": ("cast_rp_rap_short", -1)}


def figures(a):
    rgb = a[..., :3].astype(int)
    fg = ~((rgb[..., 0] > 200) & (rgb[..., 2] > 200) & (rgb[..., 1] < 90))
    cols = fg.sum(0) > 3
    segs, s = [], None
    for x, c in enumerate(cols):
        if c and s is None:
            s = x
        elif not c and s is not None:
            if x - s > 25:
                segs.append((s, x))
            s = None
    if s is not None:
        segs.append((s, len(cols)))
    return fg, segs


if __name__ == "__main__":
    import os
    for role, (sheet, k) in PICK.items():
        p = R + sheet + ".png"
        if not os.path.exists(p):
            print("missing", p)
            continue
        a = np.array(Image.open(p).convert("RGB"))
        fg, segs = figures(a)
        x0, x1 = segs[k]
        ys = np.where(fg[:, x0:x1].any(1))[0]
        crop = a[ys[0]:ys[-1] + 1, x0:x1].copy()
        m = fg[ys[0]:ys[-1] + 1, x0:x1]
        crop[~m] = 255
        out = np.full((crop.shape[0] + 40, crop.shape[1] + 40, 3), 255, np.uint8)
        out[20:-20, 20:-20] = crop
        Image.fromarray(out).save(R + f"ref_rp_{role}.png")
        print(role, len(segs), "figures ->", out.shape)

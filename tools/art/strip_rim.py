#!/usr/bin/env python3
"""Remove the printed light-cream outline ("sticker border") that the generator draws around every card.
Critic r2: "uniform white sticker border screams vinyl sticker sheet". The 3D PaperCard edge and the paper_print rim
already show a thin cream core at the cut, so the printed rim is a double border.

Method: peel the silhouette ring by ring (1 px erosion steps). A ring counts as rim while most of its pixels are
light, low-saturation cream. Cream pixels inside the rim rings become transparent; coloured edge pixels stay.
The new cut is antialiased with a 1 px blurred keep-mask, then the card is re-trimmed so the subject still touches
the bottom edge (the hinge).
  python3 tools/art/strip_rim.py IN.png OUT.png      (single file, for previews)
  from strip_rim import strip_rim                     (used by publish_cards.py)"""
import sys
import numpy as np
from PIL import Image, ImageFilter


def _cream(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return (lum > 0.70) & (sat < 0.42) & (r >= b)


def strip_rim(im: Image.Image, max_frac=0.014, stop=0.45):
    im = im.convert("RGBA")
    a = np.asarray(im, dtype=np.float32) / 255.0
    rgb, alpha = a[..., :3], a[..., 3]
    cream = _cream(rgb)
    mask = Image.fromarray(((alpha > 0.5) * 255).astype(np.uint8))
    kmax = max(3, round(max_frac * max(im.size)))
    remove = np.zeros(alpha.shape, bool)
    prev = np.asarray(mask) > 0
    rings = 0
    for i in range(kmax):
        mask = mask.filter(ImageFilter.MinFilter(3))
        cur = np.asarray(mask) > 0
        ring = prev & ~cur
        n = ring.sum()
        if n == 0:
            break
        frac = (ring & cream).sum() / n
        if frac < (stop if i > 0 else stop * 0.6):
            break
        remove |= ring & cream
        rings += 1
        prev = cur
    # one more ring: the cream->ink transition pixels (lighter than the print, not quite cream)
    if rings:
        mask = mask.filter(ImageFilter.MinFilter(3))
        ring = prev & ~(np.asarray(mask) > 0)
        r_, g_, b_ = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        lum = 0.299 * r_ + 0.587 * g_ + 0.114 * b_
        remove |= ring & (lum > 0.55) & (r_ >= b_)
    # also drop the semi-transparent fringe outside the solid silhouette when it is cream
    remove |= (alpha > 0) & (alpha <= 0.5) & cream
    # keep = the solid, non-removed silhouette grown by 1 px; anything outside it (old fringe) goes
    solid = (alpha > 0.5) & ~remove
    sm = Image.fromarray((solid * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))  # drop specks
    keep = sm.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.7))
    k = np.asarray(keep, dtype=np.float32) / 255.0
    na = np.minimum(alpha, k)
    na[na < 0.04] = 0.0
    out = np.dstack([rgb, na])
    res = Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA")
    bb = res.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if bb:
        res = res.crop(bb)
    return res, rings


if __name__ == "__main__":
    r, n = strip_rim(Image.open(sys.argv[1]))
    r.save(sys.argv[2])
    print("rings", n, r.size)

#!/usr/bin/env python3
"""Restore pixels the magenta keyer wrongly cleared INSIDE a sprite (2026-11-19, witch_candy).

  python3 tools/atlas/fill_holes.py <raw.png> <slices dir> [--tol 0.30] [--keep-hole-min 0]

The slicer keys hue 278-337° as background, so purple candies, a lilac ribbon or a glass jar's purple sweets came out as
holes. A hole is a transparent region of a card that does not touch the card's border (fully enclosed by the sprite).
Inside such a hole every pixel whose RAW colour is far from the sheet's background (distance > tol in 0..1 RGB) is
restored opaque with its raw colour; pixels that really are background magenta stay clear (die-cut doorways, gaps
between hanging strings). Opaque pixels ≥ 3 px inside the sprite also take back their raw colour (undoes the
slicer's despill on purples, which turned a plum dress green-mottled); the edge keeps the despill. Cards are rewritten in place; _slices.json bboxes map them back to the raw sheet.
"""
import json, os, sys
import numpy as np
from PIL import Image
from PIL import ImageDraw

raw_p, sdir = sys.argv[1], sys.argv[2]
tol = float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 0.30
raw = np.asarray(Image.open(raw_p).convert("RGB")).astype(np.float32) / 255.0
b = np.concatenate([raw[:6].reshape(-1, 3), raw[-6:].reshape(-1, 3), raw[:, :6].reshape(-1, 3), raw[:, -6:].reshape(-1, 3)])
bg = np.median(b, axis=0)
meta = json.load(open(os.path.join(sdir, "_slices.json")))
for m in meta["sprites"]:
    p = os.path.join(sdir, m["id"] + ".webp")
    if not os.path.exists(p):
        continue  # dropped / merged piece
    im = np.array(Image.open(p).convert("RGBA"))
    h, w = im.shape[:2]
    x0, y0 = int(m["bbox"][0]) - 4, int(m["bbox"][1]) - 4  # the slicer pads 4 px
    clear = im[..., 3] < 128
    # enclosed holes = clear pixels not reachable from the border (flood fill on a padded mask, in C)
    mk = Image.fromarray(np.pad(clear, 1, constant_values=True).astype(np.uint8) * 255)
    ImageDraw.floodfill(mk, (0, 0), 128)
    hole = (np.asarray(mk)[1:-1, 1:-1] == 255)
    ys, xs = np.where(hole)
    ry, rx = ys + y0, xs + x0
    ok = (ry >= 0) & (ry < raw.shape[0]) & (rx >= 0) & (rx < raw.shape[1])
    ys, xs, ry, rx = ys[ok], xs[ok], ry[ok], rx[ok]
    col = raw[ry, rx]
    far = np.sqrt(((col - bg) ** 2).sum(-1)) > tol
    im[ys[far], xs[far], :3] = (col[far] * 255).astype(np.uint8)
    im[ys[far], xs[far], 3] = 255
    fixed = int(far.sum())
    # despill undo (witch_candy: a reddish-purple dress came out green-mottled): opaque pixels at least 3 px inside
    # the sprite take their raw colour back when the raw is far from the background; edges keep the despill
    op = Image.fromarray(((im[..., 3] > 100) * 255).astype(np.uint8))
    from PIL import ImageFilter
    inner = np.asarray(op.filter(ImageFilter.MinFilter(7))) > 0
    ys, xs = np.where(inner)
    ry, rx = ys + y0, xs + x0
    ok = (ry >= 0) & (ry < raw.shape[0]) & (rx >= 0) & (rx < raw.shape[1])
    ys, xs, ry, rx = ys[ok], xs[ok], ry[ok], rx[ok]
    col = raw[ry, rx]
    cur = im[ys, xs, :3].astype(np.float32) / 255.0
    chg = ((np.abs(col - cur).max(-1) > 0.04) | (im[ys, xs, 3] < 255)) & (np.sqrt(((col - bg) ** 2).sum(-1)) > tol)
    im[ys[chg], xs[chg], :3] = (col[chg] * 255).astype(np.uint8)
    im[ys[chg], xs[chg], 3] = 255  # the keyer had made purple cloth half transparent
    fixed += int(chg.sum())
    if fixed:
        Image.fromarray(im).save(p, "WEBP", lossless=True, quality=100, method=6)
        print(m["id"], "restored", fixed, "px")

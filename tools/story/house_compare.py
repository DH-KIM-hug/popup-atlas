#!/usr/bin/env python3
"""Before / after house sheets (2026-11-23): python3 tools/story/house_compare.py BEFORE_ROOT AFTER_ROOT OUT_DIR

Per tale: OUT_DIR/<tale>_before_after.jpg (the two audit sheets stacked), and OUT_DIR/houses_before_after.jpg: one row
per house (every tale), the r35 / l70 / high / back views before (left half) and after (right half), with the red
(background through the house) counts.
"""
import glob, json, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import house_audit as A  # noqa: E402

VIEWS = ["r35", "l70", "high", "back_r"]
CW, CH = 240, 180


def crop(p):
    im = Image.open(p).convert("RGB")
    enc, mag, _ = A.holes(im)
    a = np.asarray(im).copy()
    a[mag] = (70, 72, 80)
    a[enc] = (255, 30, 30)
    ys, xs = np.where(~mag)
    t = Image.fromarray(a)
    if len(xs):
        t = t.crop((max(0, xs.min() - 16), max(0, ys.min() - 16), min(im.width, xs.max() + 16), min(im.height, ys.max() + 16)))
    t.thumbnail((CW - 4, CH - 16))
    return t, int(enc.sum())


def main():
    bro, aro, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    rows = []
    for tdir in sorted(glob.glob(os.path.join(aro, "*"))):
        tale = os.path.basename(tdir)
        a = os.path.join(tdir, f"{tale}_audit.jpg")
        b = os.path.join(bro, tale, f"{tale}_audit.jpg")
        if os.path.exists(a) and os.path.exists(b):
            ia, ib = Image.open(a), Image.open(b)
            w = max(ia.width, ib.width)
            s = Image.new("RGB", (w, ia.height + ib.height + 40), (30, 30, 34))
            d = ImageDraw.Draw(s)
            d.text((8, 6), "BEFORE", fill=(255, 200, 120))
            s.paste(ib, (0, 20))
            d.text((8, ib.height + 24), "AFTER", fill=(140, 255, 140))
            s.paste(ia, (0, ib.height + 40))
            s.thumbnail((2400, 4000))
            s.save(os.path.join(out, f"{tale}_before_after.jpg"), quality=86)
        for f in sorted(glob.glob(os.path.join(tdir, f"{tale}__*__front.png"))):
            nm = os.path.basename(f)[len(tale) + 2:-len("__front.png")]
            if nm.startswith("kit_"):
                continue
            rows.append((tale, nm))
    S = Image.new("RGB", (CW * len(VIEWS) * 2 + 20, CH * len(rows) + 30), (36, 36, 42))
    d = ImageDraw.Draw(S)
    d.text((8, 8), "BEFORE (left)  |  AFTER (right)   red = background seen through the house", fill=(255, 255, 255))
    for r, (tale, nm) in enumerate(rows):
        y = 30 + r * CH
        for side, root in enumerate([bro, aro]):
            for c, v in enumerate(VIEWS):
                p = os.path.join(root, tale, f"{tale}__{nm}__{v}.png")
                x = side * (CW * len(VIEWS) + 20) + c * CW
                if not os.path.exists(p):
                    d.text((x + 6, y + 6), "-", fill=(200, 200, 200))
                    continue
                t, n = crop(p)
                S.paste(t, (x + 2, y + 2))
                d.text((x + 4, y + CH - 14), f"{tale}/{nm[:18]} {v} {n}", fill=(255, 120, 120) if n > 30 else (160, 230, 160))
    S.save(os.path.join(out, "houses_before_after.jpg"), quality=84)
    print("wrote", out, len(rows), "houses")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Building kit sheet (2026-11-23): python3 tools/story/kit_sheet.py OUT_DIR TALE OUT.jpg

Rows: one per kit preset rendered by house_orbit.sh (6th argument) — the nine solo orbit views (front, ±35°, ±70°,
back-¾ both sides, high, low) and the context shot on the meadow; then the castle's story-like shots (approach on the
road, gate close-up, tower window close-up) large.
"""
import glob, os, sys
import numpy as np
from PIL import Image, ImageDraw

VIEWS = ["front", "r35", "l35", "r70", "l70", "back_r", "back_l", "high", "low"]
CW, CH = 260, 200


def solo(p):
    im = Image.open(p).convert("RGB")
    a = np.asarray(im).astype(int)
    mag = (a[..., 0] > 170) & (a[..., 1] < 90) & (a[..., 2] > 170)
    b = np.asarray(im).copy()
    b[mag] = (214, 206, 188)  # paper-cream backdrop
    ys, xs = np.where(~mag)
    t = Image.fromarray(b)
    if len(xs):
        t = t.crop((max(0, xs.min() - 20), max(0, ys.min() - 20), min(im.width, xs.max() + 20), min(im.height, ys.max() + 20)))
    t.thumbnail((CW - 4, CH - 18))
    return t


def main():
    out, tale, dst = sys.argv[1:4]
    names = sorted(os.path.basename(f)[len(tale) + 2:-len("__front.png")]
                   for f in glob.glob(os.path.join(out, f"{tale}__kit_*__front.png")))
    story = [s for s in ("approach", "gate", "window") if os.path.exists(os.path.join(out, f"{tale}__kit_castle__{s}.png"))]
    big_h = 420 if story else 0
    S = Image.new("RGB", (CW * (len(VIEWS) + 1) + 10, 34 + CH * len(names) + big_h), (40, 38, 36))
    d = ImageDraw.Draw(S)
    d.text((8, 10), "Building kit (game/art/buildings/kit.json): orbit views on paper backdrop + the building on the meadow",
           fill=(255, 255, 255))
    for r, nm in enumerate(names):
        y = 34 + r * CH
        for c, v in enumerate(VIEWS + ["ctx"]):
            p = os.path.join(out, f"{tale}__{nm}__{v}.png")
            if not os.path.exists(p):
                continue
            if v == "ctx":
                t = Image.open(p).convert("RGB")
                t.thumbnail((CW - 4, CH - 18))
            else:
                t = solo(p)
            S.paste(t, (c * CW + 2, y + 2))
            d.text((c * CW + 4, y + CH - 14), f"{nm[4:]} {v}", fill=(255, 235, 180))
    if story:
        y = 34 + CH * len(names) + 6
        w = (S.width - 10) // 3
        for i, s in enumerate(story):
            t = Image.open(os.path.join(out, f"{tale}__kit_castle__{s}.png")).convert("RGB")
            t.thumbnail((w - 6, big_h - 24))
            S.paste(t, (i * w + 4, y))
            d.text((i * w + 8, y + big_h - 20), f"castle {s}", fill=(255, 235, 180))
    S.save(dst, quality=86)
    print("kit sheet", dst, names)


if __name__ == "__main__":
    main()

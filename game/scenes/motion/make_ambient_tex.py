#!/usr/bin/env python3
"""Ambient paper cut-outs for the motion bench (C_motion r3): butterfly wings and drifting leaves.
Each is a die-cut card: cream cut border, one base colour, printed detail. usage: python3 make_ambient_tex.py"""
from PIL import Image, ImageDraw, ImageFilter
import math, random, os
OUT = os.path.join(os.path.dirname(__file__), "tex"); random.seed(3)
CREAM = (246, 236, 214, 255)
def finish(im):  # light paper grain
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a:
                n = random.randint(-7, 7); px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)), a)
    return im
WINGS = {"orange": ((232, 128, 46), (120, 52, 28)), "lemon": ((240, 200, 70), (150, 96, 30)),
         "blue": ((70, 138, 178), (30, 58, 92)), "rose": ((222, 110, 120), (120, 40, 60))}
for name, (base, dark) in WINGS.items():
    S = 128; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # wing on the right of the body line x=0: upper fore-wing + lower hind-wing; outline = cream border
    fore = [(4, 60), (40, 8), (96, 6), (122, 30), (110, 62), (60, 70)]
    hind = [(4, 66), (60, 70), (100, 84), (96, 116), (60, 124), (20, 104)]
    for poly, grow in ((fore, 6), (hind, 6)):
        d.polygon(poly, fill=CREAM)
    im = im.filter(ImageFilter.MaxFilter(9)); d = ImageDraw.Draw(im)
    d.polygon(fore, fill=base + (255,)); d.polygon(hind, fill=tuple(int(c * 0.9) for c in base) + (255,))
    d.line([(6, 62), (112, 30)], fill=dark + (255,), width=3); d.line([(6, 66), (90, 110)], fill=dark + (255,), width=3)
    for cx, cy, r in ((88, 30, 9), (64, 96, 8), (108, 50, 5)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=dark + (255,)); d.ellipse((cx - r / 2.5, cy - r / 2.5, cx + r / 2.5, cy + r / 2.5), fill=CREAM)
    for i in range(7):
        a = 0.25 + i * 0.17; x = 110 + 6 * math.cos(a * 6); d.ellipse((x - 3 - i * 6, 18 + i * 6 - 3, x + 3 - i * 6, 18 + i * 6 + 3), fill=CREAM)
    finish(im).save(f"{OUT}/wing_{name}.png")
LEAVES = {"ochre": (214, 160, 52), "red": (196, 70, 44), "orange": (226, 120, 40), "sage": (128, 150, 82)}
for name, base in LEAVES.items():
    W, H = 64, 96; im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [(W / 2 + 22 * math.sin(t * math.pi) * (1 if t < 1 else -1) * (0.6 + 0.4 * math.sin(t * math.pi)), 6 + (H - 14) * (t if t < 1 else 2 - t)) for t in [i / 20 for i in range(41)]]
    pts = [(W / 2 + 24 * math.sin(math.pi * u) ** 0.8, 6 + (H - 14) * u) for u in [i / 24 for i in range(25)]]
    pts += [(W / 2 - 24 * math.sin(math.pi * u) ** 0.8, 6 + (H - 14) * u) for u in [i / 24 for i in range(24, -1, -1)]]
    d.polygon(pts, fill=CREAM); im = im.filter(ImageFilter.MaxFilter(5)); d = ImageDraw.Draw(im)
    d.polygon(pts, fill=base + (255,)); dk = tuple(int(c * 0.6) for c in base) + (255,)
    d.line([(W / 2, 4), (W / 2, H - 4)], fill=dk, width=2)
    for k in range(1, 5):
        y = 12 + k * 15; d.line([(W / 2, y + 8), (W / 2 + 15, y)], fill=dk, width=2); d.line([(W / 2, y + 8), (W / 2 - 15, y)], fill=dk, width=2)
    finish(im).save(f"{OUT}/leaf_{name}.png")
print("ok", sorted(os.listdir(OUT)))

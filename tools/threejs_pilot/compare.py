#!/usr/bin/env python3
"""Side-by-side sheet: Godot native | three.js at the same moments.

  python3 tools/threejs_pilot/compare.py out.jpg "label|godot.jpg|three.png" ...
Each row: the Godot frame (left) and the three.js frame (right), both scaled to the same height; the three.js frame
is centre-cropped to the Godot aspect (4:3 at 1366x1024) so the framing compares directly.
"""
import sys
from PIL import Image, ImageDraw, ImageFont

H = 600


def fit(im, aspect):
    w, h = im.size
    if w / h > aspect:
        nw = int(h * aspect)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    return im.resize((int(H * aspect), H), Image.LANCZOS)


def main():
    out = sys.argv[1]
    rows = [a.split('|') for a in sys.argv[2:]]
    try:
        font = ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc', 26)
    except OSError:
        font = ImageFont.load_default()
    tiles = []
    for label, g, t in rows:
        gi = Image.open(g).convert('RGB')
        aspect = gi.size[0] / gi.size[1]
        tiles.append((label, fit(gi, aspect), fit(Image.open(t).convert('RGB'), aspect)))
    W = tiles[0][1].size[0]
    pad, head = 12, 44
    sheet = Image.new('RGB', (W * 2 + pad * 3, head + len(tiles) * (H + pad + 34) + pad), (28, 22, 18))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 8), 'Godot native (Mobile renderer)', fill=(240, 232, 214), font=font)
    d.text((W + pad * 2, 8), 'three.js r184 (WebGL2)', fill=(240, 232, 214), font=font)
    y = head
    for label, gi, ti in tiles:
        d.text((pad, y), label, fill=(220, 205, 170), font=font)
        y += 34
        sheet.paste(gi, (pad, y))
        sheet.paste(ti, (W + pad * 2, y))
        y += H + pad
    sheet.save(out, quality=88)
    print(out, sheet.size)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Wave 1 before / after sheet: rows of (label, before image or text, after image or text) -> one jpg.
  python3 tools/story/w1_sheet.py rows.json out.jpg
rows.json: [{"label": "...", "before": "path|text:...", "after": "path|text:..."}]"""
import json, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

rows = json.load(open(sys.argv[1]))
W, H, LW = 900, 420, 260
try:
    F = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 20)
    FS = ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", 16)
except Exception:
    F = FS = ImageFont.load_default()


def cell(spec):
    c = Image.new("RGB", (W, H), (30, 30, 30))
    d = ImageDraw.Draw(c)
    if spec.startswith("text:"):
        y = 12
        for para in spec[5:].split("\n"):
            for ln in textwrap.wrap(para, 86) or [""]:
                d.text((12, y), ln, fill=(230, 230, 200), font=FS)
                y += 21
        return c
    im = Image.open(spec).convert("RGB")
    im.thumbnail((W, H))
    c.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
    return c


out = Image.new("RGB", (LW + 2 * W + 20, 40 + len(rows) * (H + 10)), (12, 12, 12))
d = ImageDraw.Draw(out)
d.text((LW + 10, 8), "BEFORE (gate audit v1)", fill=(255, 160, 120), font=F)
d.text((LW + W + 20, 8), "AFTER (wave 1)", fill=(150, 230, 150), font=F)
for i, r in enumerate(rows):
    y = 40 + i * (H + 10)
    for k, ln in enumerate(textwrap.wrap(r["label"], 22)):
        d.text((10, y + 10 + 24 * k), ln, fill=(255, 255, 255), font=F)
    out.paste(cell(r["before"]), (LW + 10, y))
    out.paste(cell(r["after"]), (LW + W + 20, y))
out.save(sys.argv[2], quality=85)
print(sys.argv[2], out.size)

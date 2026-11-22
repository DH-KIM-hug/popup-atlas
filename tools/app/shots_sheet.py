#!/usr/bin/env python3
"""Contact sheet of the app-shell screenshots (tools/app/shots.sh): landscape row block, then portrait.
  python3 tools/app/shots_sheet.py <dir> [out.jpg]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

d = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else d / 'app_ui_sheet.jpg'
try:
    font = ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc', 22)
except OSError:
    font = ImageFont.load_default()
blocks = []
for kind, cell, cols in (('land', (600, 450), 4), ('port', (360, 480), 7)):
    shots = sorted(d.glob(f'{kind}_*.png'))
    if not shots:
        continue
    rows = (len(shots) + cols - 1) // cols
    W, H = cell[0], cell[1] + 34
    sheet = Image.new('RGB', (cols * W + (cols + 1) * 10, rows * H + (rows + 1) * 10), (40, 34, 30))
    dr = ImageDraw.Draw(sheet)
    for i, p in enumerate(shots):
        im = Image.open(p).convert('RGB')
        im.thumbnail(cell)
        x = 10 + (i % cols) * (W + 10)
        y = 10 + (i // cols) * (H + 10)
        sheet.paste(im, (x, y))
        dr.text((x + 4, y + cell[1] + 4), p.stem, fill=(240, 230, 210), font=font)
    blocks.append(sheet)
w = max(b.width for b in blocks)
full = Image.new('RGB', (w, sum(b.height for b in blocks)), (40, 34, 30))
y = 0
for b in blocks:
    full.paste(b, (0, y))
    y += b.height
full.save(out, quality=88)
print(out, full.size)

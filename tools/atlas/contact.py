#!/usr/bin/env python3
"""Contact sheet of sliced cards: python3 tools/atlas/contact.py <sheet> [...]  -> art_src/atlas/qa/<sheet>_contact.png
Cells show the card on a neutral grey (halos/fringes pop) with its index; red label = halo pixels or touches border."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = 'game/art/atlas'
CELL = 200

def contact(sheet, out_dir='art_src/atlas/qa'):
    d = os.path.join(ROOT, sheet)
    meta = json.load(open(os.path.join(d, '_slices.json')))['sprites']
    cols = 8
    rows = (len(meta) + cols - 1) // cols
    W, H = cols * CELL, rows * (CELL + 18)
    im = Image.new('RGB', (W, H), (52, 48, 44))
    dr = ImageDraw.Draw(im)
    try: font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
    except Exception: font = ImageFont.load_default()
    for k, m in enumerate(meta):
        cx, cy = (k % cols) * CELL, (k // cols) * (CELL + 18)
        bgc = (128, 128, 124) if (k + k // cols) % 2 == 0 else (150, 150, 146)
        dr.rectangle([cx + 2, cy + 2, cx + CELL - 3, cy + CELL - 3], fill=bgc)
        sp = Image.open(os.path.join(d, m['id'] + '.webp'))
        s = min((CELL - 12) / sp.width, (CELL - 12) / sp.height)
        sp = sp.resize((max(1, int(sp.width * s)), max(1, int(sp.height * s))), Image.LANCZOS)
        im.paste(sp, (cx + (CELL - sp.width) // 2, cy + CELL - 6 - sp.height), sp)
        bad = m['halo'] > 20 or m['touches_border']
        dr.text((cx + 4, cy + CELL), f"{k:02d} {m['size'][0]}x{m['size'][1]} h{m['halo']}", fill=(255, 90, 80) if bad else (230, 225, 210), font=font)
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, f'{sheet}_contact.png')
    im.save(p)
    return p

if __name__ == '__main__':
    for s in sys.argv[1:]:
        print(contact(s))

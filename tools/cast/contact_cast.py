#!/usr/bin/env python3
"""Contact sheet of the cast library: python3 tools/cast/contact_cast.py -> art_src/cast/qa/cast_contact.png
Each card on alternating greys (halos pop), scaled by its height_units (so relative sizes read), label = id + halo px
(red when halo > 20 or a standing card does not reach its bottom edge)."""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "atlas"))
from slice_atlas import halo_count

cat = json.load(open(os.path.join(ROOT, "game/art/cast/catalog.json")))
CW, CH, PXU = 300, 330, 560  # cell, px per unit
cols = 6
rows = (len(cat) + cols - 1) // cols
im = Image.new("RGB", (cols * CW, rows * (CH + 20)), (52, 48, 44))
dr = ImageDraw.Draw(im)
try: font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 12)
except Exception: font = ImageFont.load_default()
for k, e in enumerate(cat):
    cx, cy = (k % cols) * CW, (k // cols) * (CH + 20)
    dr.rectangle([cx + 2, cy + 2, cx + CW - 3, cy + CH - 3], fill=(128, 128, 124) if (k + k // cols) % 2 == 0 else (150, 150, 146))
    sp = Image.open(os.path.join(ROOT, "game", e["path"])).convert("RGBA")
    a = np.asarray(sp)
    h = halo_count(a)
    base_gap = sp.height - 1 - int(np.where((a[..., 3] > 128).any(1))[0][-1])
    s = min(e["height_units"] * PXU / sp.height, (CW - 12) / sp.width, (CH - 12) / sp.height)
    sp = sp.resize((max(1, int(sp.width * s)), max(1, int(sp.height * s))), Image.LANCZOS)
    im.paste(sp, (cx + (CW - sp.width) // 2, cy + CH - 6 - sp.height), sp)
    bad = h > 20 or (not e.get("hanging") and base_gap > 6)
    dr.text((cx + 4, cy + CH), f"{e['id']} h{h} b{base_gap}", fill=(255, 90, 80) if bad else (230, 225, 210), font=font)
os.makedirs(os.path.join(ROOT, "art_src/cast/qa"), exist_ok=True)
p = os.path.join(ROOT, "art_src/cast/qa/cast_contact.png")
im.save(p)
print(p)

#!/usr/bin/env python3
"""INT r1: strip the printed cream sticker rim from shared atlas cards (A's tools/art/strip_rim.py).
Writes cleaned copies to game/art/atlas_clean/<sheet>/<id>.webp; originals in game/art/atlas stay untouched.
Scenes remap catalog paths art/atlas/... -> art/atlas_clean/... when the cleaned copy exists.
  python3 tools/world/clean_atlas.py [--all]"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'art'))
from strip_rim import strip_rim
from PIL import Image
G = os.path.join(os.path.dirname(__file__), '..', '..', 'game')
cat = json.load(open(os.path.join(G, 'art/atlas/catalog.json')))
stats = []
for it in cat:
    if it.get('season') == 'winter' and '--all' not in sys.argv:
        continue
    src = os.path.join(G, it['path'])
    dst = os.path.join(G, it['path'].replace('art/atlas/', 'art/atlas_clean/'))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(src).convert('RGBA')
    out, rings = strip_rim(im)
    out.save(dst, 'WEBP', lossless=True)
    stats.append(rings)
print('cleaned', len(stats), 'mean rings', sum(stats) / max(1, len(stats)), 'zero-ring', sum(1 for r in stats if r == 0))

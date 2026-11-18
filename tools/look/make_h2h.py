#!/usr/bin/env python3
"""Blind head-to-head of two versions of OUR scene from the same camera stations.
usage: make_h2h.py --name NAME --a a0.png a1.png ... --b b0.png b1.png ... [--seed N]
Pair i shows a[i] and b[i] side by side (X left, Y right, side order seeded).
Writes artifacts/ab/<name>/pair_NN.jpg and artifacts/ab_keys/<name>.json (pair -> label of version B)."""
import argparse, json, os, random
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument('--name', required=True)
ap.add_argument('--a', nargs='+', required=True)
ap.add_argument('--b', nargs='+', required=True)
ap.add_argument('--seed', type=int, default=0)
a = ap.parse_args()
assert len(a.a) == len(a.b), 'need the same number of views'
rnd = random.Random(f'{a.name}:{a.seed}')
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
out = os.path.join(root, 'artifacts/ab', a.name)
os.makedirs(out, exist_ok=True)
os.makedirs(os.path.join(root, 'artifacts/ab_keys'), exist_ok=True)
try:
    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 44)
except Exception:
    font = ImageFont.load_default()
key = {}
for i, (pa, pb) in enumerate(zip(a.a, a.b)):
    ia = Image.open(pa).convert('RGB').resize((1024, 768), Image.LANCZOS)
    ib = Image.open(pb).convert('RGB').resize((1024, 768), Image.LANCZOS)
    b_left = rnd.random() < 0.5
    left, right = (ib, ia) if b_left else (ia, ib)
    im = Image.new('RGB', (2068, 768), 'white')
    im.paste(left, (0, 0))
    im.paste(right, (1044, 0))
    d = ImageDraw.Draw(im)
    for x, t in ((0, 'X'), (1044, 'Y')):
        d.rectangle((x, 0, x + 70, 60), fill='black')
        d.text((x + 18, 6), t, fill='white', font=font)
    p = f'pair_{i + 1:02d}'
    im.save(os.path.join(out, p + '.jpg'), quality=90)
    key[p] = 'X' if b_left else 'Y'
json.dump(key, open(os.path.join(root, 'artifacts/ab_keys', a.name + '.json'), 'w'))
print(out)

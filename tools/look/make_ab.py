#!/usr/bin/env python3
"""Blind A/B sheets. Each pair = one of OURS vs one REFERENCE, side by side, labelled X (left) and Y (right),
order decided by a seeded shuffle. The answer key goes to artifacts/ab_keys/ (critics must never read it).
usage: make_ab.py --name COMP_rN --ours a.png b.png ... --ref r1.jpg r2.jpg ... [--seed N] [--strip]
  --strip: ours/ref are sequences; each side becomes a 4x2 strip of 8 frames (motion judging)
Output: artifacts/ab/<name>/pair_01.jpg ...  key: artifacts/ab_keys/<name>.json"""
import argparse, json, os, random
from PIL import Image, ImageDraw, ImageFont

def fit(im, w, h):
    im = im.convert('RGB'); r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r + .5), int(im.height * r + .5)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))

def strip(paths, w, h):
    n = min(8, len(paths)); idx = [round(i * (len(paths) - 1) / max(1, n - 1)) for i in range(n)]
    cw, ch = w // 4, h // 2; out = Image.new('RGB', (w, h))
    for k, i in enumerate(idx):
        out.paste(fit(Image.open(paths[i]), cw, ch), ((k % 4) * cw, (k // 4) * ch))
    return out

def label(im, text):
    d = ImageDraw.Draw(im)
    try: f = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 44)
    except Exception: f = ImageFont.load_default()
    d.rectangle((0, 0, 70, 60), fill=(0, 0, 0)); d.text((18, 6), text, fill=(255, 255, 255), font=f)
    return im

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--name', required=True)
    ap.add_argument('--ours', nargs='+', required=True); ap.add_argument('--ref', nargs='+', required=True)
    ap.add_argument('--seed', type=int, default=0); ap.add_argument('--strip', action='store_true')
    a = ap.parse_args(); rnd = random.Random(f'{a.name}:{a.seed}')
    W, H = 1024, 768
    out_dir = f'artifacts/ab/{a.name}'; os.makedirs(out_dir, exist_ok=True); os.makedirs('artifacts/ab_keys', exist_ok=True)
    if a.strip:
        pairs = [(strip(a.ours, W, H), strip(a.ref, W, H))]
    else:
        refs = a.ref[:]; rnd.shuffle(refs)
        pairs = [(fit(Image.open(o), W, H), fit(Image.open(refs[i % len(refs)]), W, H)) for i, o in enumerate(a.ours)]
    key = {}
    for i, (ours, ref) in enumerate(pairs, 1):
        ours_left = rnd.random() < 0.5
        L, R = (ours, ref) if ours_left else (ref, ours)
        sheet = Image.new('RGB', (W * 2 + 16, H), (20, 20, 20))
        sheet.paste(label(L, 'X'), (0, 0)); sheet.paste(label(R, 'Y'), (W + 16, 0))
        p = f'{out_dir}/pair_{i:02d}.jpg'; sheet.save(p, quality=90)
        key[f'pair_{i:02d}'] = 'Y' if ours_left else 'X'   # which label is the REFERENCE
    json.dump(key, open(f'artifacts/ab_keys/{a.name}.json', 'w'), indent=1)
    print(json.dumps({'sheets': sorted(os.listdir(out_dir)), 'dir': out_dir}))

if __name__ == '__main__':
    main()

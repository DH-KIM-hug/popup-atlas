#!/usr/bin/env python3
"""three.js player: the bookshelf data. Read-only on game/.

  python3 tools/threejs/pack_shelf.py [--out threejs/public/data]

Writes data/tales.json (the Godot shelf's order from game/app/tales.json, each tale's title and the cover the Godot
BookModel prints on the front board: cover_art + the cut-paper title at cover.json title_rect, cloth colour) and
copies the cover images to data/shared/covers/<tale>_{art,title}.webp. A tale is listed as `ready` when
data/tales/<tale>/index.json exists (it was exported + packed).
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAME = os.path.join(ROOT, 'game')


def main():
    out = os.path.join(ROOT, 'threejs/public/data')
    if '--out' in sys.argv:
        out = sys.argv[sys.argv.index('--out') + 1]
    cov_dir = os.path.join(out, 'shared/covers')
    os.makedirs(cov_dir, exist_ok=True)
    order = json.load(open(os.path.join(GAME, 'app/tales.json')))['tales']
    tales = []
    for e in order:
        tid = e['id']
        if e.get('hidden'):
            continue
        sc = json.load(open(os.path.join(GAME, 'stories', tid, 'script.json')))
        cj = os.path.join(GAME, 'stories', tid, 'cover.json')
        cov = json.load(open(cj)).get('cover', {}) if os.path.exists(cj) else {}
        item = {'id': tid, 'name': sc.get('title', tid), 'cloth': '#' + cov.get('cloth', '6b4a2a'),
                'cloth_dark': '#' + cov.get('cloth_dark', '4a321c'), 'title_rect': cov.get('title_rect', [0.5, 0.2, 0.84]),
                'ready': os.path.exists(os.path.join(out, 'tales', tid, 'index.json'))}
        for k in ('art', 'title'):
            rp = cov.get(k)
            if rp:
                src = os.path.join(GAME, rp.replace('res://', ''))
                dst = os.path.join(cov_dir, f'{tid}_{k}.webp')
                from PIL import Image
                im = Image.open(src)
                im = im.convert('RGBA') if im.mode in ('RGBA', 'LA', 'P') else im.convert('RGB')
                w = 640 if k == 'art' else 720  # shelf thumbnails (a book is ~25 % of the screen width)
                if im.width > w:
                    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
                im.save(dst, 'WEBP', quality=82, alpha_quality=90, method=5)
                item[k + '_img'] = f'shared/covers/{tid}_{k}.webp'
        sz = os.path.join(out, 'tales', f'{tid}.size.json')
        if os.path.exists(sz):
            item['bytes'] = json.load(open(sz))['wire_bytes']
        tales.append(item)
    json.dump({'tales': tales}, open(os.path.join(out, 'tales.json'), 'w'), ensure_ascii=False, indent=1)
    print('tales.json:', ', '.join(f"{t['id']}{'' if t['ready'] else ' (not exported)'}" for t in tales))


if __name__ == '__main__':
    main()

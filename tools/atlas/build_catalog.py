#!/usr/bin/env python3
"""Build game/art/atlas/catalog.json from slices + hand labels.

labels/<sheet>.json = {"biome": "...", "season": "summer", "tags": [...],
                       "items": {"00": ["label", "category", height_units, cross_slot(0/1), {optional overrides}], ...,
                                 "07": "drop"}}
Indices missing from "items" or set to "drop" are moved to art_src/atlas/rejects/ (kept out of the shipped library).
Overrides dict may set season, biome, tags (added to sheet tags)."""
import glob, json, os, shutil

ROOT = 'game/art/atlas'
LAB = 'tools/atlas/labels'
REJ = 'art_src/atlas/rejects'

def main():
    cat = []
    os.makedirs(REJ, exist_ok=True)
    for lf in sorted(glob.glob(os.path.join(LAB, '*.json'))):
        sheet = os.path.splitext(os.path.basename(lf))[0]
        L = json.load(open(lf))
        sl = json.load(open(os.path.join(ROOT, sheet, '_slices.json')))['sprites']
        for k, m in enumerate(sl):
            it = L['items'].get(f'{k:02d}', 'drop')
            src = os.path.join(ROOT, sheet, m['id'] + '.webp')
            if it == 'drop':
                if os.path.exists(src):
                    shutil.move(src, os.path.join(REJ, m['id'] + '.webp'))
                    if os.path.exists(src + '.import'): os.remove(src + '.import')
                continue
            if not os.path.exists(src):
                print('missing', src); continue
            label, category, h, cross = it[:4]
            ov = it[4] if len(it) > 4 else {}
            tags = sorted(set(L.get('tags', []) + ov.get('tags', [])))
            cat.append({'id': m['id'], 'path': f'art/atlas/{sheet}/{m["id"]}.webp', 'sheet': sheet,
                        'category': category, 'label': label, 'height_units': h, 'cross_slot': bool(cross),
                        'biome': ov.get('biome', L['biome']), 'season': ov.get('season', L.get('season', 'any')),
                        'tags': tags, 'px': m['size']})
    json.dump(cat, open(os.path.join(ROOT, 'catalog.json'), 'w'), indent=1, ensure_ascii=False)
    from collections import Counter
    print(len(cat), 'cards;', dict(Counter(c['sheet'] for c in cat)))
    print(dict(Counter(c['category'] for c in cat)))

if __name__ == '__main__':
    main()

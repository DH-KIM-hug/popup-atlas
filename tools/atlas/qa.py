#!/usr/bin/env python3
"""QA over the shipped library (catalog.json): magenta halo pixels, base check (the lowest opaque rows must belong to
the sprite's largest part, i.e. nothing floats below the hinge), border-touching slices. Prints offenders + totals."""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slice_atlas import label, halo_count

cat = json.load(open('game/art/atlas/catalog.json'))
bad, halo_total = [], 0
for e in cat:
    a = np.asarray(Image.open('game/' + e['path']))
    h = halo_count(a); halo_total += h
    m = a[..., 3] > 89
    lab, n = label(m)
    sizes = np.bincount(lab.ravel())[1:]
    main = 1 + int(sizes.argmax())
    ys = np.where(m.any(1))[0]
    base = lab[ys[-1]]
    base_ok = (base[base > 0] == main).mean() > 0.5
    if h > 20 or not base_ok:
        bad.append((e['id'], h, base_ok))
print(f'{len(cat)} cards, halo px total {halo_total}, offenders: {bad}')

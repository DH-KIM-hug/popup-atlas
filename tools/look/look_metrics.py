#!/usr/bin/env python3
"""Objective look metrics for a frame, so critics and builders compare numbers, not vibes.
usage: look_metrics.py IMG [IMG...]  (prints one JSON line per image)
- lum_mean / lum_p05 / lum_p95: brightness and contrast range (Rec.709 luma, 0..1)
- sat_mean: mean HSV saturation; warmth: mean(R)-mean(B)
- sharp_top / sharp_mid / sharp_bot: Laplacian variance in the top/middle/bottom thirds (tilt-shift profile)
- tiltshift_ratio: sharp_mid / mean(sharp_top, sharp_bot)  (>1 means the middle band is the sharp one)
- edge_density: fraction of pixels on strong edges (scene busyness / prop density)
- palette: 6 dominant colours (median cut)"""
import json, sys
import numpy as np
from PIL import Image, ImageFilter

def metrics(path):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    if w > 1280:
        im = im.resize((1280, int(h * 1280 / w)), Image.LANCZOS); w, h = im.size
    a = np.asarray(im).astype(np.float32) / 255
    lum = a[..., 0] * .2126 + a[..., 1] * .7152 + a[..., 2] * .0722
    hsv = np.asarray(im.convert('HSV')).astype(np.float32) / 255
    g = np.asarray(im.convert('L')).astype(np.float32)
    lap = np.abs(g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:])
    t = lap.shape[0] // 3
    st, sm, sb = (float(lap[i * t:(i + 1) * t].var()) for i in range(3))
    edges = np.asarray(im.convert('L').filter(ImageFilter.FIND_EDGES)).astype(np.float32)
    q = im.quantize(6, method=Image.Quantize.MEDIANCUT); pal = q.getpalette()[:18]
    cnt = sorted(q.getcolors(), reverse=True)
    return {
        'img': path, 'lum_mean': round(float(lum.mean()), 3), 'lum_p05': round(float(np.percentile(lum, 5)), 3),
        'lum_p95': round(float(np.percentile(lum, 95)), 3), 'sat_mean': round(float(hsv[..., 1].mean()), 3),
        'warmth': round(float(a[..., 0].mean() - a[..., 2].mean()), 3),
        'sharp_top': round(st, 1), 'sharp_mid': round(sm, 1), 'sharp_bot': round(sb, 1),
        'tiltshift_ratio': round(sm / max(1e-3, (st + sb) / 2), 2),
        'edge_density': round(float((edges > 40).mean()), 3),
        'palette': ['#%02x%02x%02x' % tuple(pal[i * 3:i * 3 + 3]) for _, i in cnt],
    }

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(json.dumps(metrics(p)))

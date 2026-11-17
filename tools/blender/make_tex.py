#!/usr/bin/env python3
"""Pop-up Atlas kit textures (run by build_kit.py, or alone: python3 tools/blender/make_tex.py).

Inputs  (Codex imagegen, tools/blender/tex_jobs.json): art_src/tex/{fibre,grass_print,path_print,water_print}.png
Outputs:
  art_src/tex/card_atlas.png      4x4 swatches of tinted cardstock (one material for every pop piece)
  art_src/tex/print_<tile>.png    1024 printed page art per tile (edges line up across tiles)
  public/tex/paper_fibre.jpg      seamless cream page texture for the engine's page plane (1024)
  public/tex/paper_fibre_detail.jpg  seamless grey fibre detail (multiply / roughness variation)
Missing inputs fall back to flat colour + noise so the kit always builds.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'art_src', 'tex')
PUB = os.path.join(ROOT, 'public', 'tex')
S = 1024
rng = np.random.default_rng(7)

def hexc(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0

def load(name, fallback_hex, size=S):
    p = os.path.join(SRC, name)
    if os.path.exists(p):
        im = Image.open(p).convert('RGB').resize((size, size), Image.LANCZOS)
        return np.asarray(im, np.float32) / 255.0
    print('  (fallback for', name, ')')
    base = np.ones((size, size, 3), np.float32) * hexc(fallback_hex)
    n = rng.normal(0, 0.03, (size, size, 1)).astype(np.float32)
    return np.clip(base + n, 0, 1)

def seamless(a):
    """Cross-fade with a half-offset copy so the image tiles (hides any AI seam)."""
    h, w = a.shape[:2]
    b = np.roll(np.roll(a, h // 2, 0), w // 2, 1)
    y = np.abs(np.linspace(-1, 1, h))[:, None]; x = np.abs(np.linspace(-1, 1, w))[None, :]
    m = np.clip((np.maximum(x, y) - 0.62) / 0.3, 0, 1)[..., None]   # 1 near edges -> use shifted copy
    return a * (1 - m) + b * m

def save(a, path, q=None):
    im = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))
    if path.endswith('.jpg'): im.save(path, quality=q or 88, optimize=True)
    else: im.save(path)

def lum(a): return a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11

# ---------------------------------------------------------------- sources
fibre = seamless(load('fibre.png', '#efe3c8'))
grass = seamless(load('grass_print.png', '#9fae7f'))
path = seamless(load('path_print.png', '#d6b47b'))
water = seamless(load('water_print.png', '#6a9aa5'))
path = path * 0.82 + hexc('#efe3c8') * 0.18 * (lum(path) / lum(path).mean())[..., None]
grass_mod = 1 + (lum(grass) / lum(grass).mean() - 1) * 0.8
fl = lum(fibre); detail = (fl / fl.mean())            # ~1.0 mean fibre modulation
detail_soft = 1 + (detail - 1) * 0.55

# ---------------------------------------------------------------- page + detail for the engine
os.makedirs(PUB, exist_ok=True)
save(fibre * (hexc('#efe3c8') / fibre.reshape(-1, 3).mean(0)), os.path.join(PUB, 'paper_fibre.jpg'))
g = np.clip(0.5 + (detail - 1) * 1.2, 0, 1)
save(np.repeat(g[..., None], 3, 2), os.path.join(PUB, 'paper_fibre_detail.jpg'))

# ---------------------------------------------------------------- card atlas (4x4, 256 px cells)
PALETTE = [  # index: name, hex   (kept in sync with build_kit.py CELLS)
    ('cream', '#efe3c8'), ('ochre', '#d4a24c'), ('terracotta', '#c0643f'), ('sage', '#9caf7c'),
    ('sage_dark', '#6f8a5a'), ('sage_light', '#bcc68f'), ('teal', '#5f97a1'), ('teal_light', '#93bfc0'),
    ('brown', '#8a6a4f'), ('brown_dark', '#5e4636'), ('window', '#f4b450'), ('stone', '#cdbb9c'),
    ('ink', '#3a2f2a'), ('white', '#f7f0de'), ('roof', '#b25a3a'), ('ochre_light', '#e3c27d')]
C = S // 4
atlas = np.zeros((S, S, 3), np.float32)
small = np.asarray(Image.fromarray((np.clip(detail_soft / 2, 0, 1) * 255).astype(np.uint8)).resize((C, C), Image.LANCZOS),
                   np.float32) / 255.0 * 2
for i, (_, hx) in enumerate(PALETTE):
    r, c = divmod(i, 4)
    yy = np.linspace(0, 1, C)[:, None, None]
    tint = hexc(hx) * (1.02 - 0.05 * yy)               # faint gradient like hand-coloured card
    atlas[r * C:(r + 1) * C, c * C:(c + 1) * C] = np.clip(tint * small[..., None], 0, 1)
save(atlas, os.path.join(SRC, 'card_atlas.png'))

# ---------------------------------------------------------------- tile prints
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
X = (xx + 0.5) / S - 0.5            # east +
N = 0.5 - (yy + 0.5) / S            # north +  (image top = north)

def lowfreq(seed, amp=0.006, k=6):
    r = np.random.default_rng(seed); out = np.zeros_like(X)
    for _ in range(k):
        fx, fy, ph = r.uniform(2, 9), r.uniform(2, 9), r.uniform(0, 6.3)
        out += np.sin(X * fx * 6.283 + N * fy * 6.283 + ph)
    return out / k * amp * 2

def seg(ax, ay, bx, by):
    px, py = X - ax, N - ay; dx, dy = bx - ax, by - ay
    t = np.clip((px * dx + py * dy) / (dx * dx + dy * dy), 0, 1)
    return np.hypot(px - t * dx, py - t * dy)

def arc_ne():   # quarter arc joining N-mid and E-mid, centred on NE corner
    return np.abs(np.hypot(X - 0.5, N - 0.5) - 0.5)

EDGE = {'N': (0, 0.62), 'E': (0.62, 0), 'S': (0, -0.62), 'W': (-0.62, 0)}

def lines(sides, corner=False):
    if corner: return arc_ne()
    d = np.full_like(X, 9.0)
    for s in sides: d = np.minimum(d, seg(0, 0, *EDGE[s]))
    return d

def sstep(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

def mix(a, b, m): return a * (1 - m[..., None]) + b * m[..., None]

def paint_river(img, d, half=0.19, seed=1):
    d = d + lowfreq(seed, 0.007)
    aa = 1.5 / S
    bank = 1 - sstep(half + 0.012, half + 0.012 + aa, d)      # cream cut-paper bank
    img = mix(img, img * 0.82 + hexc('#3f5a44') * 0.0, (1 - sstep(half + 0.012, half + 0.03, d)) * 0.35)  # bank shadow
    img = mix(img, hexc('#f4ead2') * detail_soft[..., None], bank)
    wat = 1 - sstep(half, half + aa, d)
    deep = np.clip(1 - d / half, 0, 1) ** 0.7
    w = water * (0.9 + 0.1 * (1 - deep))[..., None]
    w = mix(w, w * hexc('#c9e0dd'), sstep(half - 0.03, half, d) * 0.35)   # lighter shallows
    return mix(img, w, wat)

def paint_path(img, d, half=0.14, seed=2, ink=True):
    d = d + lowfreq(seed, 0.006)
    aa = 1.5 / S
    m = 1 - sstep(half, half + aa, d)
    img = mix(img, path, m)
    if ink:   # printed ink edge line, broken here and there like a worn print
        brk = sstep(-0.2, 0.4, lowfreq(seed + 9, 1.0, 4))
        line = (1 - sstep(0.0035, 0.0035 + aa, np.abs(d - half))) * (0.35 + 0.4 * brk)
        img = mix(img, hexc('#7a5a3e'), line)
    return img

def blob(img, cx, cy, rx, ry, hx, alpha=0.55, seed=3):
    e = np.hypot((X - cx) / rx, (N - cy) / ry) + lowfreq(seed, 0.04)
    m = (1 - sstep(1 - 2.5 / (S * rx), 1, e)) * alpha
    return mix(img, hexc(hx) * grass_mod[..., None], m)

def rect(img, x0, y0, x1, y1, hx, alpha=0.9):
    m = ((X > x0) & (X < x1) & (N > y0) & (N < y1)).astype(np.float32)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    return mix(img, hexc(hx) * detail_soft[..., None], m * alpha)

def finish(img):
    img = img * (1 + (detail[..., None] - 1) * 0.25)              # paper fibre through the ink
    # faint die-cut line round the hinged tile
    edge = np.minimum(np.minimum(X + 0.5, 0.5 - X), np.minimum(N + 0.5, 0.5 - N))
    img = img * (1 - 0.18 * (1 - sstep(0.0, 2.2 / S, edge)))[..., None]
    return np.clip(img, 0, 1)

def tile(name):
    img = grass.copy()
    if name == 'grass':
        for i, (cx, cy) in enumerate([(-0.25, 0.22), (0.2, -0.18), (0.28, 0.3)]):
            img = blob(img, cx, cy, 0.07, 0.04, '#7e955f', 0.45, 10 + i)
    elif name == 'hill':
        for i, (cy, ry, hx) in enumerate([(0.1, 0.3, '#6f8a5a'), (-0.05, 0.26, '#839b67'), (-0.25, 0.18, '#a9b885')]):
            img = blob(img, 0.0, cy, 0.46, ry * 0.55, hx, 0.6, 20 + i)
    elif name == 'trees':
        for i, (cx, cy, r) in enumerate([(-0.2, 0.16, 0.17), (0.22, 0.05, 0.13), (-0.02, -0.25, 0.11)]):
            img = blob(img, cx + 0.02, cy - 0.02, r * 1.05, r * 0.95, '#5f7a4c', 0.35, 30 + i)   # shadow
            img = blob(img, cx, cy, r, r, '#6f8a5a', 0.7, 33 + i)
            img = blob(img, cx - r * 0.25, cy + r * 0.25, r * 0.45, r * 0.45, '#b2c08a', 0.5, 36 + i)
    elif name == 'house':
        img = blob(img, 0, -0.02, 0.36, 0.3, '#c2b07e', 0.4, 40)             # yard
        img = rect(img, -0.24, -0.14, 0.24, 0.17, '#b25a3a', 0.92)           # roof from above
        img = rect(img, -0.24, 0.005, 0.24, 0.012, '#7d3b26', 0.8)           # ridge line
        img = rect(img, 0.1, 0.06, 0.16, 0.12, '#8a6a4f', 0.9)               # chimney
        img = paint_path(img, seg(0, -0.2, 0, -0.62), 0.06, 41)              # garden path to door (south)
    elif name.startswith('path'):
        sides = {'path_straight': 'NS', 'path_corner': 'NE', 'path_tee': 'NES', 'path_end': 'N'}[name]
        d = lines(sides, corner=name == 'path_corner')
        if name == 'path_end': d = seg(0, -0.05, 0, 0.62)
        img = paint_path(img, d, 0.14, 50)
    elif name.startswith('river'):
        if name == 'river_straight': d = lines('NS')
        elif name == 'river_corner': d = lines('NE', corner=True)
        else:
            d = np.minimum(seg(0, 0.0, 0, 0.62), np.hypot(X, N + 0.04) - 0.1)   # pond
        img = paint_river(img, d, 0.19, 60)
    elif name == 'bridge':
        img = paint_river(img, lines('NS'), 0.19, 70)
        img = paint_path(img, lines('EW'), 0.14, 71)
        img = rect(img, -0.25, -0.15, 0.25, -0.12, '#a89474', 0.8)          # printed parapets
        img = rect(img, -0.25, 0.12, 0.25, 0.15, '#a89474', 0.8)
    return finish(img)

TILES = ['grass', 'hill', 'trees', 'house', 'path_straight', 'path_corner', 'path_tee', 'path_end',
         'river_straight', 'river_corner', 'river_end', 'bridge']
if __name__ == '__main__':
    only = sys.argv[1:]
    for t in TILES:
        if only and t not in only: continue
        save(tile(t), os.path.join(SRC, f'print_{t}.png'))
        print('print', t)
    print('textures done')

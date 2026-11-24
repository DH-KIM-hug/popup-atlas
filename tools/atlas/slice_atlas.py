#!/usr/bin/env python3
"""Key a magenta-background sprite atlas and slice it into clean RGBA cards (numpy + PIL only).

  python3 tools/atlas/slice_atlas.py art_src/atlas/raw/<sheet>.png [--out game/art/atlas] [--min-area 1500] [--join 5]
  (village_props needs --join 4: woodpile sits 10 px above the rose arch)

Steps: estimate bg colour from the border -> soft key by colour distance -> unmix + despill edge pixels ->
connected components (on a slightly dilated mask so petals/leaves join their sprite) -> merge small fragments into the
nearest big sprite, drop specks and fragments that dangle below a sprite's base -> trim, pad 4 px -> lossless webp.
Writes <out>/<sheet>/<sheet>_<nn>.webp and <out>/<sheet>/_slices.json (bbox in the raw sheet, area, halo count).
Sprites are numbered in reading order (rows top->bottom, then left->right).
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image

PAD = 4


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def estimate_bg(rgb):
    b = np.concatenate([rgb[:6].reshape(-1, 3), rgb[-6:].reshape(-1, 3), rgb[:, :6].reshape(-1, 3), rgb[:, -6:].reshape(-1, 3)])
    # keep magenta-ish border pixels only
    m = (b[:, 0] > 0.6) & (b[:, 2] > 0.6) & (b[:, 1] < 0.4)
    return np.median(b[m] if m.sum() > 50 else b, axis=0)


def key(rgb, bg):
    """alpha from distance to bg; also a 'magenta-ness' term so shaded magenta (darker/lighter) keys too."""
    d = np.sqrt(((rgb - bg) ** 2).sum(-1))
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mag = np.minimum(r, b) - g          # ~1 for pure magenta, <=0 for greens/browns/creams
    hue_bal = np.abs(r - b)             # magenta has r ~= b
    a_dist = smoothstep(0.18, 0.42, d)
    # strongly magenta-hued pixels (any brightness) are background even when far from bg in distance
    a_hue = 1 - smoothstep(0.30, 0.55, mag - hue_bal * 0.8)
    # hue key: the model shades magenta seen through gaps (light pink / dark plum); key by HSV hue window
    mx = rgb.max(-1); mn = rgb.min(-1); ch = mx - mn
    sat = ch / np.maximum(mx, 1e-4)
    hue = np.zeros_like(mx)
    rm = (mx == r) & (ch > 0)
    bm_ = (mx == b) & (ch > 0) & ~rm
    hue[rm] = (60 * (g[rm] - b[rm]) / ch[rm]) % 360
    hue[bm_] = 60 * (r[bm_] - g[bm_]) / ch[bm_] + 240
    win = smoothstep(278, 290, hue) * (1 - smoothstep(328, 337, hue))
    is_mag = win * smoothstep(0.32, 0.5, sat) * smoothstep(0.22, 0.35, mx)
    return np.minimum(np.minimum(a_dist, a_hue), 1 - is_mag)


def box_mean(x, r):
    """mean over a (2r+1)^2 window via cumulative sums; x is HxW or HxWxC."""
    pad = [(r + 1, r)] * 2 + [(0, 0)] * (x.ndim - 2)
    c = np.pad(x, pad).cumsum(0).cumsum(1)
    k = 2 * r + 1
    return c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]


def unmix_local(rgb, a, bg, r=3, near=6, tol=0.12):
    """Pixels in thin gaps (grass blades, wicker) are blends of the sprite colour and magenta. Estimate the local
    sprite colour F from nearby clean (opaque, spill-free) pixels and project obs onto the F..bg line.
    Where the blend model fits (small residual) take alpha from the projection and colour F."""
    rr, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    spill = np.minimum(rr, b) - g
    clean = (a >= 0.98) & (spill <= 0.06)
    cnt = box_mean(clean.astype(np.float32), r)
    F = box_mean(rgb * clean[..., None], r) / np.maximum(cnt, 1)[..., None]
    cand = (a > 0.02) & ~clean & (cnt >= 2) & dilate(a < 0.5, near)
    D = F - bg
    O = rgb - bg
    t = (O * D).sum(-1) / np.maximum((D * D).sum(-1), 1e-4)
    res = np.sqrt(((O - t[..., None] * D) ** 2).sum(-1))
    ok = cand & (res < tol) & (t < 0.97)
    a2 = a.copy(); out = rgb.copy()
    a2[ok] = np.minimum(a[ok], np.clip(t[ok], 0, 1))
    out[ok] = F[ok]
    return out, a2, int(ok.sum())


def unmix_despill(rgb, a, bg):
    out = rgb.copy()
    soft = (a > 0.02) & (a < 0.98)
    if soft.any():
        aa = a[soft][:, None]
        raw_u = (rgb[soft] - (1 - aa) * bg) / aa
        # When (rgb - (1-a)*bg)/a drops R or B below 0 against #FF00FF, dividing G by a creates neon-green edge pixels.
        # Only use full unmix when channels don't severely clip and a >= 0.35; otherwise cap subtraction to avoid clipping.
        valid_u = (aa[:, 0] >= 0.35) & (raw_u.min(-1) >= -0.02)
        safe_u = np.clip(raw_u, 0, 1)
        # Fallback for clipping soft pixels: neutral despill (reduce magenta excess without boosting G above natural max)
        obs = rgb[soft]
        orig_g_ex = np.clip(obs[:, 1] - np.maximum(obs[:, 0], obs[:, 2]), 0.0, None)
        spill_rb = np.clip(np.minimum(obs[:, 0], obs[:, 2]) - obs[:, 1], 0.0, None)
        fb = obs.copy()
        fb[:, 0] = np.where((obs[:, 0] > obs[:, 1]) & (obs[:, 2] > obs[:, 1]), obs[:, 0] - spill_rb, obs[:, 0])
        fb[:, 2] = np.where((obs[:, 0] > obs[:, 1]) & (obs[:, 2] > obs[:, 1]), obs[:, 2] - spill_rb, obs[:, 2])
        chosen = np.where(valid_u[:, None], safe_u, fb)
        # Never allow unmix to invent green excess that was not present in the source pixel
        max_rb = np.maximum(chosen[:, 0], chosen[:, 2])
        cap_g = max_rb + orig_g_ex + 0.04
        chosen[:, 1] = np.minimum(chosen[:, 1], cap_g)
        out[soft] = np.clip(chosen, 0, 1)
    # despill: limit min(R,B) excess over G on edge band pixels
    edge = dilate(a < 0.5, 3) & (a >= 0.02)
    r, g, b = out[..., 0], out[..., 1], out[..., 2]
    spill = np.clip(np.minimum(r, b) - np.maximum(g, 0) - 0.02, 0, None)
    # only where pixel is magenta-tinted (r and b both above g) -> pull r,b down
    fix = edge & (spill > 0) & (r > g) & (b > g)
    out[..., 0] = np.where(fix, r - spill, r)
    out[..., 2] = np.where(fix, b - spill, b)
    return out


def dilate(m, r):
    out = m.copy()
    for _ in range(r):
        n = out.copy()
        n[1:] |= out[:-1]; n[:-1] |= out[1:]; n[:, 1:] |= out[:, :-1]; n[:, :-1] |= out[:, 1:]
        out = n
    return out


def erode(m, r):
    return ~dilate(~m, r)


def label(mask):
    """8-connected components via union-find over run-length rows. Returns (labels, n)."""
    H, W = mask.shape
    parent = [0]
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    lab = np.zeros((H, W), np.int32)
    prev_runs = []
    for y in range(H):
        row = mask[y]
        if not row.any():
            prev_runs = []; continue
        d = np.diff(np.concatenate([[0], row.view(np.int8), [0]]))
        starts = np.where(d == 1)[0]; ends = np.where(d == -1)[0]
        runs = []
        j = 0
        for s, e in zip(starts, ends):
            l = None
            while j < len(prev_runs) and prev_runs[j][1] < s:   # prev run ends (excl) left of s-1 -> no touch
                j += 1
            k = j
            while k < len(prev_runs) and prev_runs[k][0] <= e:  # prev start <= e  (8-connectivity)
                pl = find(prev_runs[k][2])
                if l is None: l = pl
                elif pl != l:
                    lo, hi = min(pl, l), max(pl, l)
                    parent[hi] = lo; l = lo
                k += 1
            if l is None:
                l = len(parent); parent.append(l)
            runs.append((s, e, l))
            lab[y, s:e] = l
        prev_runs = runs
    # flatten
    roots = np.array([find(i) for i in range(len(parent))], np.int32)
    uniq, inv = np.unique(roots, return_inverse=True)
    lab = inv[lab].astype(np.int32)
    # label 0 stays background because roots[0]=0 is the smallest
    return lab, len(uniq) - 1


def bbox(m):
    ys, xs = np.where(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def box_dist(a, b):
    dx = max(0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0, max(a[1], b[1]) - min(a[3], b[3]))
    return max(dx, dy)


def halo_count(rgba):
    """opaque pixels that look like magenta or a magenta blend (min(R,B) well above G, R~B)."""
    a = rgba[..., 3] > 127
    r, g, b = [rgba[..., i].astype(int) for i in range(3)]
    mag = a & (np.minimum(r, b) - g > 45) & (np.abs(r - b) < 70) & (b > 110)
    return int(mag.sum())


def slice_sheet(path, out_root, min_area=1500, merge_dist=26, join_px=5):
    sheet = os.path.splitext(os.path.basename(path))[0]
    im = Image.open(path).convert('RGB')
    rgb = np.asarray(im).astype(np.float32) / 255
    bg = estimate_bg(rgb)
    a = key(rgb, bg)
    a[a < 0.04] = 0
    # remove 1px salt (isolated opaque pixels) and fill pinholes
    solid = a > 0.5
    rgb_u, a, n_unmix = unmix_local(rgb, a, bg)
    a[a < 0.04] = 0
    rgb2 = unmix_despill(rgb_u, a, bg)

    lab, n = label(dilate(solid, join_px))
    lab = np.where(solid | (a > 0.04), lab, 0)
    comps = []
    for i in range(1, n + 1):
        m = lab == i
        area = int((m & solid).sum())
        if area < 30: continue
        comps.append({'ids': [i], 'area': area, 'box': bbox(m), 'main_box': bbox(m)})
    comps.sort(key=lambda c: -c['area'])
    big = [c for c in comps if c['area'] >= min_area]
    small = [c for c in comps if c['area'] < min_area]
    dropped = 0
    for s in small:
        best, bd = None, 1e9
        for b in big:
            d = box_dist(s['box'], b['box'])
            if d < bd: best, bd = b, d
        # merge only if close, and not dangling below the big sprite's base
        if best is not None and bd <= merge_dist and s['box'][3] <= best['main_box'][3] + 2:
            best['ids'] += s['ids']; best['area'] += s['area']
            bb = best['box']; sb = s['box']
            best['box'] = (min(bb[0], sb[0]), min(bb[1], sb[1]), max(bb[2], sb[2]), max(bb[3], sb[3]))
        else:
            dropped += 1
    # reading order: group into rows by vertical centre
    big.sort(key=lambda c: (c['box'][1] + c['box'][3]) / 2)
    rows, cur = [], []
    for c in big:
        cy = (c['box'][1] + c['box'][3]) / 2
        if cur and cy - np.mean([(k['box'][1] + k['box'][3]) / 2 for k in cur]) > 60:
            rows.append(cur); cur = []
        cur.append(c)
    if cur: rows.append(cur)
    ordered = [c for r in rows for c in sorted(r, key=lambda c: c['box'][0])]

    od = os.path.join(out_root, sheet)
    os.makedirs(od, exist_ok=True)
    for f in os.listdir(od):
        if f.endswith('.webp') or f.endswith('.webp.import'):
            os.remove(os.path.join(od, f))
    meta = []
    H, W = a.shape
    for k, c in enumerate(ordered):
        x0, y0, x1, y1 = c['box']
        x0, y0 = max(0, x0), max(0, y0)
        sub = np.isin(lab[y0:y1, x0:x1], c['ids'])
        alpha = np.where(sub, a[y0:y1, x0:x1], 0)
        col = rgb2[y0:y1, x0:x1]
        # bleed colour into transparent area (avoids dark/magenta fringes under filtering)
        rgba = np.zeros((y1 - y0 + 2 * PAD, x1 - x0 + 2 * PAD, 4), np.float32)
        rgba[PAD:-PAD, PAD:-PAD, :3] = col
        rgba[PAD:-PAD, PAD:-PAD, 3] = alpha
        rgba = bleed(rgba)
        out = (np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8)
        name = f'{sheet}_{k:02d}'
        fp = os.path.join(od, name + '.webp')
        Image.fromarray(out, 'RGBA').save(fp, 'WEBP', lossless=True, quality=100, method=6)
        touches = x0 <= 1 or y0 <= 1 or x1 >= W - 1 or y1 >= H - 1
        meta.append({'id': name, 'bbox': [int(x0), int(y0), int(x1), int(y1)], 'area': c['area'],
                     'size': [int(out.shape[1]), int(out.shape[0])], 'halo': halo_count(out),
                     'touches_border': bool(touches), 'parts': len(c['ids'])})
    json.dump({'sheet': sheet, 'bg': [round(float(v), 3) for v in bg], 'dropped': dropped, 'sprites': meta},
              open(os.path.join(od, '_slices.json'), 'w'), indent=1)
    return sheet, meta, dropped


def bleed(rgba, iters=4):
    """Push opaque colours outward into fully transparent pixels (alpha stays 0)."""
    a = rgba[..., 3]
    known = a > 0.5
    col = rgba[..., :3] * known[..., None]
    for _ in range(iters):
        acc = np.zeros_like(col); cnt = np.zeros(a.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            acc += np.roll(np.roll(col, dy, 0), dx, 1)
            cnt += np.roll(np.roll(known, dy, 0), dx, 1)
        new = (~known) & (cnt > 0)
        col[new] = acc[new] / cnt[new][:, None]
        known = known | new
    rgba[..., :3] = np.where((a > 0.5)[..., None], rgba[..., :3], col)
    return rgba


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('raw', nargs='+')
    ap.add_argument('--out', default='game/art/atlas')
    ap.add_argument('--min-area', type=int, default=1500)
    ap.add_argument('--join', type=int, default=5, help='px dilation that joins near parts (gap <= 2*join)')
    args = ap.parse_args()
    for p in args.raw:
        sheet, meta, dropped = slice_sheet(p, args.out, args.min_area, join_px=args.join)
        bad = [m['id'] for m in meta if m['halo'] > 20]
        print(f'{sheet}: {len(meta)} sprites, dropped {dropped} specks, halo>20: {bad}')


if __name__ == '__main__':
    main()

"""Cut the 톡톡 traveller cards into paper-puppet layers: body + hips + left leg + right leg (r2: hips piece in front of the
leg tops, flat-colour rounded leg tops, brass brads at the pivots).

Run: python3 game/art/chars_rig/cut_rig.py   (from repo root)
Outputs <pose>_body.png, <pose>_leg_l.png, <pose>_leg_r.png (full-canvas RGBA, same size as the source,
so parts stay registered) and rig.json with per-part pixel bboxes + hip pivots.
Hidden leg tops (behind the coat / shirt) are repainted by tiling the visible pants texture upward
inside the extrapolated leg silhouette. Same design, no new drawing.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "chars")
POSES = ["sw_trav_walk", "sw_trav_walk_nohat", "sw_trav_hold", "sw_trav_shirt"]  # fan + sit stay single cards


def classify(a):
    R, G, B, A = [a[..., i].astype(int) for i in range(4)]
    op = A > 140
    coat = op & (R - G > 62) & (R > 95)
    skin = op & (R > 205) & (G > 140)
    shirt = op & (G >= R - 8) & (G > 90)
    button = op & (R > 170) & (G > 120) & (B < 110)
    pants = op & ~coat & ~skin & ~shirt & ~button
    return op, pants


def clean(mask, k=5):
    im = Image.fromarray((mask * 255).astype(np.uint8))
    im = im.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))  # open
    im = im.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))  # close
    return np.array(im) > 127


def components_touching_bottom(mask):
    from collections import deque
    h, w = mask.shape
    lab = np.zeros(mask.shape, np.int32)
    keep = np.zeros(mask.shape, bool)
    cur = 0
    for sx in range(w):
        for sy in range(h - 1, h - 60, -1):
            if mask[sy, sx] and not lab[sy, sx]:
                cur += 1
                q = deque([(sy, sx)])
                lab[sy, sx] = cur
                while q:
                    y, x = q.popleft()
                    keep[y, x] = True
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = cur
                            q.append((ny, nx))
    return keep


def label(mask):
    from collections import deque
    h, w = mask.shape
    lab = np.zeros(mask.shape, np.int32)
    n = 0
    for sy, sx in zip(*np.where(mask)):
        if lab[sy, sx]:
            continue
        n += 1
        lab[sy, sx] = n
        q = deque([(sy, sx)])
        while q:
            y, x = q.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = n
                    q.append((ny, nx))
    return lab, n


def brad(img, cx, cy, r=7):
    """Brass split-pin head: dark rim, warm face, small highlight. Drawn only where the layer is opaque."""
    h, w = img.shape[:2]
    for y in range(cy - r - 2, cy + r + 3):
        for x in range(cx - r - 2, cx + r + 3):
            if not (0 <= y < h and 0 <= x < w) or img[y, x, 3] < 128:
                continue
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= r + 1.6 and d > r:  # soft cast shadow ring (lower right)
                if (x - cx) + (y - cy) > 0:
                    img[y, x, :3] = (img[y, x, :3] * 0.62).astype(np.uint8)
            elif d <= r:
                hl = max(0.0, 1.0 - (((x - cx + r * 0.35) ** 2 + (y - cy + r * 0.35) ** 2) ** 0.5) / (r * 0.6))
                base = np.array([150, 112, 52]) if d < r - 1.4 else np.array([88, 60, 26])
                c = base + (np.array([255, 232, 170]) - base) * hl * 0.8
                img[y, x, :3] = np.clip(c, 0, 255).astype(np.uint8)
                img[y, x, 3] = 255


def save_cropped(img, name):
    """Save the part cropped to its alpha bbox (PaperCard maps the whole texture onto the card, so the
    canvas must be the subject; the die-cut rim width is computed from it). Returns the bbox in source px."""
    ys, xs = np.where(img[..., 3] > 8)
    bb = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    Image.fromarray(img[bb[1]:bb[3], bb[0]:bb[2]]).save(os.path.join(HERE, name))
    return bb


def cut(pose):
    src = Image.open(os.path.join(SRC, pose + ".webp")).convert("RGBA")
    a = np.array(src)
    h, w = a.shape[:2]
    rng = np.random.default_rng(7)
    op, pants = classify(a)
    pants[: int(h * 0.5)] = False
    pants = components_touching_bottom(clean(pants))
    band = pants[int(h * 0.80): int(h * 0.93)]
    cols = band.sum(0).astype(float)
    cx0, cx1 = int(w * 0.3), int(w * 0.7)
    split = cx0 + int(np.argmin(cols[cx0:cx1] + np.abs(np.arange(cx0, cx1) - w / 2) * 0.05))
    rows = np.where(pants.any(1))[0]
    top_vis = int(rows[0])
    # Crotch: first row below the visible pants top where the split column opens to the page for 4 rows.
    colA = a[:, max(0, split - 3): split + 4, 3].min(1)
    crotch = h - 60
    for y in range(top_vis + 20, h - 4):
        if (colA[y: y + 4] < 60).all():
            crotch = y
            break
    hip_y = max(top_vis - 14, int(h * 0.5))
    parts = {}
    leg_union = np.zeros_like(pants)
    sil = {}
    for side, xs in (("leg_l", (0, split)), ("leg_r", (split, w))):
        m = np.zeros_like(pants)
        m[:, xs[0]: xs[1]] = pants[:, xs[0]: xs[1]]
        ext = {}
        for y in range(h):
            xx = np.where(m[y])[0]
            if xx.size:
                ext[y] = (int(xx[0]), int(xx[-1]))
        ys = sorted(ext)
        widths = np.array([ext[y][1] - ext[y][0] for y in ys])
        ref_w = np.median(widths[len(ys) // 3: 2 * len(ys) // 3])
        upper = [(y, wd) for y, wd in zip(ys, widths) if y < ys[0] + 0.6 * (ys[-1] - ys[0])]
        narrow = [y for y, wd in upper if wd < ref_w * 0.88]
        full_y = (max(narrow) + 2) if narrow else ys[0] + 2
        full_y = max(full_y, crotch + 4)
        x0f, x1f = ext.get(full_y, ext[ys[len(ys) // 2]])
        # Flat pants colour sampled from the fully visible leg (no tiling: avoids copying creases/lining blotches).
        samp = a[full_y + 6: full_y + 70, x0f + 6: x1f - 5][..., :3].reshape(-1, 3)
        samp_m = m[full_y + 6: full_y + 70, x0f + 6: x1f - 5].reshape(-1)
        col = np.median(samp[samp_m], 0) if samp_m.any() else np.array([110, 75, 45])
        out = np.zeros((h, w, 4), np.uint8)
        out[m] = a[m]
        out[:hip_y] = 0
        cx_leg = (x0f + x1f) / 2.0
        inner_pad = 8
        lo_s, hi_s = {}, {}
        for y in range(hip_y, full_y + 3):
            t = max(0.0, (full_y - y) / max(1, full_y - hip_y))
            grow = int(round(5 * t))
            lo, hi = x0f - grow, x1f + grow
            if side == "leg_l":
                hi = max(hi, split - 1 + inner_pad)
            else:
                lo = min(lo, split - inner_pad)
            # Rounded hip cap.
            r = (hi - lo) / 2.0
            dy = (hip_y + r) - y
            if dy > 0:
                half = (max(0.0, r * r - dy * dy)) ** 0.5
                c = (lo + hi) / 2.0
                lo, hi = int(round(c - half)), int(round(c + half))
            lo_s[y], hi_s[y] = lo, hi
            for x in range(max(0, lo), min(w, hi + 1)):
                if out[y, x, 3] < 200 or not m[y, x]:
                    n = rng.normal(0, 3.0)
                    shade = 1.0 - 0.10 * (abs(x - cx_leg) / max(1.0, r)) ** 2
                    out[y, x, :3] = np.clip(col * shade + n, 0, 255).astype(np.uint8)
                    out[y, x, 3] = 255
            out[y, :max(0, lo)] = 0
            out[y, min(w, hi + 1):] = 0
        oi = out.astype(int)
        red = (oi[..., 0] - oi[..., 1] > 48) | (oi[..., 3] < 60)
        out[red] = 0
        # Below the coat hem: the original die-cut alpha on this side of the split (clean outline), minus coat red.
        y_clean = crotch + 22
        xa, xb = xs
        for y in range(y_clean, h):
            row = a[y, xa:xb].astype(int)
            keep = (row[:, 3] > 0) & ~((row[:, 0] - row[:, 1] > 90) & (row[:, 0] > 150))
            out[y, xa:xb] = 0
            out[y, xa:xb][keep] = a[y, xa:xb][keep]
        # Fill classifier holes (reddish-brown pants pixels read as coat) between the row extents below the crotch.
        for y in range(crotch, h):
            xx = np.where(out[y, :, 3] > 60)[0]
            if xx.size < 2:
                continue
            seg = slice(int(xx[0]), int(xx[-1]) + 1)
            holes = (out[y, seg, 3] <= 60) & (a[y, seg, 3] > 200)
            out[y, seg][holes] = a[y, seg][holes]
        sil[side] = (lo_s, hi_s, cx_leg, col, x0f, x1f)
        piv_y = int(crotch - 0.30 * (crotch - top_vis))
        parts[side] = {"hip": [int(round(cx_leg)), piv_y], "_out": out}
        leg_union |= m
    # Hips piece: in front of the leg tops, covers them down to just below the crotch (rounded hems per leg).
    hips = np.zeros_like(a)
    for side in ("leg_l", "leg_r"):
        lo_s, hi_s, cx_leg, col, x0f, x1f = sil[side]
        hw = max(8.0, (x1f - x0f) / 2.0 + 4)
        for y in range(hip_y, min(h, crotch + 16)):
            if y not in lo_s:
                continue
            for x in range(max(0, lo_s[y]), min(w, hi_s[y] + 1)):
                u = (x - cx_leg) / hw
                bottom = crotch + 12 - 12 * min(1.0, u * u)
                if y > bottom:
                    continue
                if leg_union[y, x] and a[y, x, 3] > 200:
                    hips[y, x] = a[y, x]
                else:
                    hips[y, x, :3] = np.clip(col + rng.normal(0, 3.0), 0, 255).astype(np.uint8)
                    hips[y, x, 3] = 255
    body = a.copy()
    rm = Image.fromarray((leg_union * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))
    body[np.array(rm) > 127, 3] = 0
    lab, n = label(body[..., 3] > 60)
    hip_min = hip_y + 6
    for i in range(1, n + 1):
        ys_, xs_ = np.where(lab == i)
        if ys_.min() > hip_min - 20 or ys_.size < 300:
            body[lab == i, 3] = 0
    # Brads at the leg pivots, on whatever layer is in front there (pin goes through all layers).
    for side in ("leg_l", "leg_r"):
        bx, by = parts[side]["hip"]
        brad(body, bx, by)
        brad(hips, bx, by)
    for side in ("leg_l", "leg_r"):
        out = parts[side].pop("_out")
        parts[side]["bbox"] = save_cropped(out, f"{pose}_{side}.png")
    parts["hips"] = {"bbox": save_cropped(hips, f"{pose}_hips.png")}
    parts["body"] = {"bbox": save_cropped(body, f"{pose}_body.png")}
    sy, sx = np.where(a[..., 3] > 90)
    return {"size": [w, h], "full_bbox": [int(sx.min()), int(sy.min()), int(sx.max()) + 1, int(sy.max()) + 1],
            "split": split, "crotch": int(crotch), "parts": parts}


if __name__ == "__main__":
    rig = {p: cut(p) for p in POSES}
    with open(os.path.join(HERE, "rig.json"), "w") as f:
        json.dump(rig, f, indent=1)
    print(json.dumps({k: (v["crotch"], v["parts"]["leg_l"]["hip"], v["parts"]["leg_r"]["hip"]) for k, v in rig.items()}))

#!/usr/bin/env python3
"""witch_candy v5 (user: "기존 입술을 빼고 하던지...해야되는거 아니냐? 기존 입술위에 덧칠하니깐 이상한데"): replace the ghost-candy
mouth properly. For every ghost figure / ghost walk frame (originals in art_src/cast/black_mouth_orig/):
  1. find the original mouth (the lip ring + its hole + corner ticks; side views: the "C"; hand-placed spots for the
     frames the detector misses),
  2. ERASE it: the region (grown 3 px) is filled with a patch of the same face copied from nearby skin (below / beside /
     above, the cleanest candidate), colour-matched to the region's border and feathered at the edges, so the face
     reads blank with its own felt grain,
  3. draw the NEW mouth: a felt decal from story_wc_mouths (front "oooh" O, or the side O for profile frames), sized
     to the old mouth and placed at its centre.
Writes game/art/cast/cast_<skin>_ghost*.webp and a three-row contact (original / erased / new):
  python3 tools/cast/wc_mouth_v5.py [--erase-only] [--contact out.png]
"""
import glob, os, sys
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ORIG = os.path.join(ROOT, "art_src", "cast", "black_mouth_orig")
OUT = os.path.join(ROOT, "game", "art", "cast")
SKINS = ["dahyun", "candy_witch", "hobak_cat", "rabbit_kid", "bear_kid", "fox_kid"]
# frames the detector misses: (cx, cy, rx, ry) as card fractions, the old mouth's oval
MANUAL = {"cast_candy_witch_ghost_cycle_0.webp": (0.683, 0.353, 0.06, 0.035),
          "cast_bear_kid_ghost_cycle_1.webp": (0.755, 0.37, 0.06, 0.04),
          # the cat's small brown "o" (measured: dark components of the originals)
          "cast_hobak_cat_ghost_front_0.webp": (0.499, 0.327, 0.042, 0.032),
          "cast_hobak_cat_ghost_front_1.webp": (0.499, 0.327, 0.042, 0.032),
          "cast_hobak_cat_ghost_cycle_3.webp": (0.835, 0.264, 0.035, 0.034),
          }
DECALS = os.path.join(ROOT, "game", "art", "atlas", "story_wc_mouths")


def comps(mask):
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
                yy, xx = y + dy, x + dx
                if 0 <= yy < mask.shape[0] and 0 <= xx < mask.shape[1] and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    q.append((yy, xx))
    return lab, n


def _hole(sub):
    inv = Image.fromarray((np.pad(~sub, 1, constant_values=True) * 255).astype(np.uint8)).copy()
    ImageDraw.floodfill(inv, (0, 0), 128)
    return np.asarray(inv)[1:-1, 1:-1] == 255


def find_mouth(arr, name):
    """-> (mask of the old mouth in full-image coords, centre (x, y), width, height, side?)"""
    h, w = arr.shape[:2]
    if name in MANUAL:
        cx, cy, rx, ry = MANUAL[name]
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).ellipse([(cx - rx) * w, (cy - ry) * h, (cx + rx) * w, (cy + ry) * h], fill=255)
        return np.asarray(m) > 0, (cx * w, cy * h), 2 * rx * w, 2 * ry * h, None
    lum = arr[..., :3].astype(float) @ np.array([0.299, 0.587, 0.114])
    a = arr[..., 3] > 200
    for thr in (55, 95, 125):
        for close in (False, True):
            dark = (lum < thr) & a
            dark[: int(h * 0.05)] = False
            dark[int(h * 0.62):] = False
            lab, n = comps(dark)
            best = None
            for k in range(1, n + 1):
                ys, xs = np.where(lab == k)
                bw, bh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
                if not (w * 0.02 < bw < w * 0.36 and 0.5 < bh / max(bw, 1) < 2.8):
                    continue
                sub = lab[ys.min():ys.max() + 1, xs.min():xs.max() + 1] == k
                if close:
                    m0 = Image.fromarray(np.pad(sub, 8).astype(np.uint8) * 255)
                    sub = np.asarray(m0.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.MinFilter(13)))[8:-8, 8:-8] > 0
                hole = _hole(sub)
                if hole.sum() < 0.08 * bw * bh:
                    continue
                if best is None or hole.sum() > best[0]:
                    best = (hole.sum(), ys.min(), xs.min(), sub | hole, close)
            if best:
                _, by, bx, region, was_c = best
                m = np.zeros((h, w), bool)
                m[by:by + region.shape[0], bx:bx + region.shape[1]] = region
                ys, xs = np.where(m)
                return m, ((xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2), xs.max() - xs.min() + 1, \
                    ys.max() - ys.min() + 1, was_c
    # last resort (the cat's side frames: a small brown "o"): the lowest small dark feature in the face band
    dark = (lum < 110) & a
    dark[: int(h * 0.12)] = False
    dark[int(h * 0.42):] = False
    lab, n = comps(dark)
    cands = []
    for k in range(1, n + 1):
        ys, xs = np.where(lab == k)
        if 20 < len(ys) < (w * 0.06) ** 2 and (ys.max() - ys.min()) < h * 0.08:
            cands.append((ys.max(), k))
    if cands:
        k = max(cands)[1]
        m = lab == k
        m = np.asarray(Image.fromarray(m.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
        ys, xs = np.where(m)
        return m, ((xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1, True
    return None


def erase(arr, mask):
    h, w = arr.shape[:2]
    grown = np.asarray(Image.fromarray(mask.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(9))) > 0
    grown &= arr[..., 3] > 0
    ys, xs = np.where(grown)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    bh, bw = y1 - y0, x1 - x0
    border = (np.asarray(Image.fromarray(grown.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(7))) > 0) & ~grown
    border &= arr[..., 3] > 200
    bcol = np.median(arr[border][:, :3].astype(float), axis=0)
    # the border's skin only (not a blush or the nose touching it)
    bc = arr[border][:, :3].astype(float)
    keep = np.abs(bc - bcol).sum(1) < 40
    border_idx = np.where(border)
    border = np.zeros_like(border)
    border[border_idx[0][keep], border_idx[1][keep]] = True
    bcol = np.median(arr[border][:, :3].astype(float), axis=0)
    lum = arr[..., :3].astype(float) @ np.array([0.299, 0.587, 0.114])
    best = None
    cand = []
    for fy in (1.15, 0.9, 0.7, 0.5, -0.6, -0.9):
        for fx in (0.0, -0.6, 0.6, -1.0, 1.0):
            cand.append((int(bh * fy), int(bw * fx)))
    cand += [(0, -int(bw * 1.2)), (0, int(bw * 1.2))]
    need = grown[y0:y1, x0:x1]
    for dy, dx in cand:
        sy0, sx0 = y0 + dy, x0 + dx
        if sy0 < 0 or sx0 < 0 or sy0 + bh > h or sx0 + bw > w or (dy == 0 and dx == 0):
            continue
        src = arr[sy0:sy0 + bh, sx0:sx0 + bw]
        if (src[..., 3][need] < 200).any():
            continue
        # the patch must be plain face: no blush, hair, eyes, nose or the mouth itself in it
        if (grown[sy0:sy0 + bh, sx0:sx0 + bw] & need).any():
            continue
        cols = src[..., :3][need].astype(float)
        far = (np.abs(cols - bcol).sum(1) > 45).mean()
        score = np.abs(np.median(cols, 0) - bcol).sum() + 900 * far + cols.std(0).sum() * 0.5
        if best is None or score < best[0]:
            best = (score, src.copy(), far)
    if best is None or best[2] > 0.02:
        # no clean patch: a fill made of the border's own pixels (random samples, softly blurred: keeps the grain)
        bpx = arr[border][:, :3]
        rng = np.random.default_rng(3)
        patch = np.zeros((bh, bw, 4), np.uint8)
        patch[..., :3] = bpx[rng.integers(0, len(bpx), bh * bw)].reshape(bh, bw, 3)
        patch[..., 3] = 255
        pim = Image.fromarray(patch).filter(ImageFilter.GaussianBlur(0.8))
        patch = np.array(pim)
        patch[..., :3] = np.clip(patch[..., :3].astype(float) - np.median(patch[..., :3].reshape(-1, 3), 0) + bcol, 0, 255).astype(np.uint8)
    else:
        patch = best[1]
        shift = bcol - np.median(patch[..., :3][need].astype(float), 0)
        patch[..., :3] = np.clip(patch[..., :3].astype(float) + shift, 0, 255).astype(np.uint8)
    # feathered paste: full inside, fading over the outer 3 px of the grown region
    soft = np.asarray(Image.fromarray(grown.astype(np.uint8) * 255).filter(ImageFilter.GaussianBlur(1.6))).astype(float) / 255
    soft = np.maximum(soft, mask.astype(float))[y0:y1, x0:x1][..., None]
    reg = arr[y0:y1, x0:x1, :3].astype(float)
    arr[y0:y1, x0:x1, :3] = (reg * (1 - soft) + patch[..., :3].astype(float) * soft).astype(np.uint8)
    return arr


SURPRISED = {"dahyun": "wow_black", "candy_witch": "surprised_black", "hobak_cat": "surprised_black",
             "rabbit_kid": "surprised_black", "bear_kid": "surprised_black", "fox_kid": "surprised_black"}


def native_mouth(skin):
    """The character's own NEW mouth, lifted from its surprised figure (drawn natively with the ghost-candy mouth):
    the largest very dark purple-ish component in the face band -> an RGBA decal."""
    p = os.path.join(OUT, f"cast_{skin}_{SURPRISED[skin]}.webp")
    arr = np.array(Image.open(p).convert("RGBA"))
    h, w = arr.shape[:2]
    rgb = arr[..., :3].astype(float)
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    m = (lum < 70) & (arr[..., 3] > 200) & (rgb[..., 2] >= rgb[..., 1] - 4)
    m[: int(h * 0.12)] = False
    m[int(h * 0.62):] = False
    lab, n = comps(m)
    best = None
    for k in range(1, n + 1):
        ys, xs = np.where(lab == k)
        bw, bh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        if len(ys) < 60 or bw > w * 0.3 or not 0.6 < bh / bw < 1.8:
            continue
        cx = (xs.min() + xs.max()) / 2
        score = len(ys) - abs(cx - w / 2) * 2  # the big round one near the middle of the face
        if best is None or score > best[0]:
            best = (score, k, ys.min(), ys.max(), xs.min(), xs.max())
    _, k, y0, y1, x0, x1 = best
    mm = lab == k
    # include its own highlight / lighter stitched rim: fill the component's holes, grow 2 px
    sub = mm[y0:y1 + 1, x0:x1 + 1]
    sub = sub | _hole(sub)
    full = np.zeros((h, w), bool)
    full[y0:y1 + 1, x0:x1 + 1] = sub
    full = np.asarray(Image.fromarray(full.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
    out = arr.copy()
    out[..., 3] = np.where(full, 255, 0).astype(np.uint8)
    ys, xs = np.where(full)
    return Image.fromarray(out).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def decal(kind):
    """the felt mouth decals (story_wc_mouths): front O (piece 0), side O (piece 4), surprised O (3)."""
    files = sorted(glob.glob(os.path.join(DECALS, "story_wc_mouths_*.webp")))
    idx = {"front": 0, "side": 4, "small": 7}[kind]
    return Image.open(files[min(idx, len(files) - 1)]).convert("RGBA") if files else None


def main():
    erase_only = "--erase-only" in sys.argv
    rows = []
    for s in SKINS:
        for p in sorted(glob.glob(os.path.join(ORIG, f"cast_{s}_ghost*.webp"))):
            name = os.path.basename(p)
            orig = np.array(Image.open(p).convert("RGBA"))
            found = find_mouth(orig, name)
            if found is None:
                print(name, "NO MOUTH FOUND")
                continue
            mask, (cx, cy), mw, mh, was_c = found
            er = erase(orig.copy(), mask)
            new = Image.fromarray(er.copy())
            side = ("cycle" in name and "front" not in name) or was_c
            if not erase_only:
                d = native_mouth(s)
                if d is not None:
                    th = max(10, int(mh * 1.05))  # as tall as the old mouth; a profile is narrower
                    tw = max(8, int(d.width * th / d.height * (0.72 if side else 1.0)))
                    d = d.resize((tw, th), Image.LANCZOS)
                    new.alpha_composite(d, (int(cx - d.width / 2), int(cy - d.height / 2)))
                    na = np.array(new)
                    na[..., 3] = orig[..., 3]  # the card's silhouette stays the original's
                    new = Image.fromarray(na)
            new.save(os.path.join(OUT, name), "WEBP", lossless=True, quality=100, method=6)
            rows.append((name, orig, er, np.array(new), (cx, cy, mw, mh)))
            print(name, "side" if side else "front", int(mw), int(mh))
    if "--contact" in sys.argv:
        out = sys.argv[sys.argv.index("--contact") + 1]
        cells = []
        for name, o, e, n, (cx, cy, mw, mh) in rows:
            col = []
            for im in (o, e, n):
                r = max(mw, mh) * 2.2
                c = Image.fromarray(im).crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r))).resize((120, 120))
                bg = Image.new("RGBA", (120, 120), (190, 190, 190, 255))
                bg.alpha_composite(c)
                col.append(bg)
            cells.append(col)
        cols = 20
        nrow = (len(cells) + cols - 1) // cols
        sheet = Image.new("RGB", (120 * cols, 3 * 120 * nrow + 8 * nrow), (90, 90, 90))
        for i, col in enumerate(cells):
            gx, gy = (i % cols) * 120, (i // cols) * (360 + 8)
            for k, c in enumerate(col):
                sheet.paste(c.convert("RGB"), (gx, gy + 120 * k))
        sheet.save(out)
        print("contact", out)


if __name__ == "__main__":
    main()

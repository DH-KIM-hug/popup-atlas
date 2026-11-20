#!/usr/bin/env python3
"""witch_candy v4 (user: "검은 입술이 기존 입술위에 덮여서 이상한데?"): the ghost-candy figures drew a black lip RING with
skin showing through it and little lip-corner ticks, which read as a ring stuck on a mouth. Here the mouth itself
becomes a solid dark open "oooh" mouth: in the face band, the dark ring component with an enclosed hole is filled
dark (plum-black, a slightly lighter tongue at the bottom), and its thin corner ticks are replaced by skin.

  python3 tools/cast/wc_black_mouth.py [--contact out.png]

Works in place on game/art/cast/cast_<skin>_ghost*.webp; originals are kept once in art_src/cast/black_mouth_orig/.
"""
import glob, os, shutil, sys
from collections import deque
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ORIG = os.path.join(ROOT, "art_src", "cast", "black_mouth_orig")
SKINS = ["dahyun", "candy_witch", "hobak_cat", "rabbit_kid", "bear_kid", "fox_kid"]
FILL = np.array([38, 22, 30])
TONGUE = np.array([92, 34, 46])


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


# mouths the detector cannot find (a "C" touching the cheek, a tiny brown "o"): centre as fractions of the card
MANUAL = {"cast_candy_witch_ghost_cycle_0.webp": (0.683, 0.353), "cast_hobak_cat_ghost_front_0.webp": (0.49, 0.335, 0.06, 0.04),
          "cast_bear_kid_ghost_cycle_1.webp": (0.755, 0.37, 0.07, 0.045), "cast_hobak_cat_ghost_front_1.webp": (0.495, 0.335, 0.06, 0.04)}


def fix(path):
    if os.path.basename(path) in MANUAL:
        return _fallback(path, MANUAL[os.path.basename(path)])
    for thr in (55, 95):  # the cat's walking frames draw a small brown "o" (not black): a looser threshold
        for close in (False, True):  # side views draw a "C": close it to find the mouth opening
            if _fix(path, thr, close):
                return True
    return _fallback(path)


def _fallback(path, at=None):
    """No ring: the lowest small dark feature in the face (the mouth: below the eyes and nose) is replaced by a solid
    dark oval with a black rim drawn over its whole area (a replacement, not an overlay on visible lips)."""
    from PIL import ImageDraw
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    h, w = arr.shape[:2]
    lum = arr[..., :3].astype(float) @ np.array([0.299, 0.587, 0.114])
    dark = (lum < 110) & (arr[..., 3] > 200)
    dark[: int(h * 0.12)] = False
    dark[int(h * 0.42):] = False
    if at is not None and len(at) > 2:  # a given oval (centre, half sizes as card fractions) over the old mouth
        cx, cy, rw, rh = at[0] * w, at[1] * h, at[2] * w, at[3] * h
        d = ImageDraw.Draw(im)
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(21, 16, 21, 255))
        d.ellipse([cx - rw + 3, cy - rh + 3, cx + rw - 3, cy + rh - 3], fill=tuple(FILL) + (255,))
        d.chord([cx - rw + 3, cy - rh + 3, cx + rw - 3, cy + rh - 3], 20, 160, fill=tuple(TONGUE) + (255,))
        im.save(path, "WEBP", lossless=True, quality=100, method=6)
        return True
    if at is not None:  # a given centre: the dark feature there (or a small oval if none)
        dark[: max(0, int(at[1] * h) - int(h * 0.04))] = False
        dark[int(at[1] * h) + int(h * 0.04):] = False
        dark[:, : max(0, int(at[0] * w) - int(w * 0.07))] = False
        dark[:, int(at[0] * w) + int(w * 0.07):] = False
    lab, n = comps(dark)
    cands = []
    for k in range(1, n + 1):
        ys, xs = np.where(lab == k)
        if 20 < len(ys) < (w * 0.06) ** 2 and (ys.max() - ys.min()) < h * 0.08:
            cands.append((ys.max(), xs.min(), xs.max(), ys.min()))
    if not cands:
        if at is None:
            return False
        cands = [(int(at[1] * h) + 6, int(at[0] * w) - 6, int(at[0] * w) + 6, int(at[1] * h) - 6)]
    y1, x0, x1, y0 = max(cands)  # the lowest one
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rw, rh = max(x1 - x0, 8) * 0.75 + 2, max(y1 - y0, 10) * 0.75 + 2
    d = ImageDraw.Draw(im)
    d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(21, 16, 21, 255))
    d.ellipse([cx - rw + 3, cy - rh + 3, cx + rw - 3, cy + rh - 3], fill=tuple(FILL) + (255,))
    d.chord([cx - rw + 3, cy - rh + 3, cx + rw - 3, cy + rh - 3], 20, 160, fill=tuple(TONGUE) + (255,))
    im.save(path, "WEBP", lossless=True, quality=100, method=6)
    return True


def _fix(path, thr, close):
    im = np.array(Image.open(path).convert("RGBA"))
    h, w = im.shape[:2]
    rgb = im[..., :3].astype(float)
    a = im[..., 3] > 200
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    y0, y1 = int(h * 0.05), int(h * 0.62)  # the face band (arms-up figures: the head is in the upper part)
    dark = (lum < thr) & a
    dark[:y0] = False
    dark[y1:] = False
    lab, n = comps(dark)
    best = None
    for k in range(1, n + 1):
        ys, xs = np.where(lab == k)
        bw, bh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        if not (w * 0.02 < bw < w * 0.36 and 0.5 < bh / max(bw, 1) < 2.8):
            continue
        sub = (lab[ys.min():ys.max() + 1, xs.min():xs.max() + 1] == k)
        if close:
            m0 = Image.fromarray(np.pad(sub, 8).astype(np.uint8) * 255)
            sub = np.asarray(m0.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.MinFilter(13)))[8:-8, 8:-8] > 0
        # enclosed hole: inverse of the ring not reachable from the bbox border
        inv = Image.fromarray((np.pad(~sub, 1, constant_values=True) * 255).astype(np.uint8)).copy()
        from PIL import ImageDraw
        ImageDraw.floodfill(inv, (0, 0), 128)
        hole = np.asarray(inv)[1:-1, 1:-1] == 255
        if hole.sum() < 0.08 * bw * bh:
            continue
        if best is None or hole.sum() > best[0]:
            best = (hole.sum(), k, ys.min(), xs.min(), sub, hole)
    if best is None:
        return False
    _, k, by, bx, sub, hole = best
    hh, ww = sub.shape
    # fill the hole (open mouth): plum-black, a darker red tongue in the lower third
    # the lips themselves: black (the cat's brown "o" too)
    ry, rx = np.where(sub & (lab[by:by + hh, bx:bx + ww] == k))
    for y, x in zip(ry, rx):
        im[by + y, bx + x, :3] = (21, 16, 21)
    yy, xx = np.where(hole)
    for y, x in zip(yy, xx):
        im[by + y, bx + x, :3] = TONGUE if y > hh * 0.62 else FILL
        im[by + y, bx + x, 3] = 255
    # corner ticks: thin parts of the ring (removed by an opening) become skin
    m = Image.fromarray((sub * 255).astype(np.uint8))
    opened = np.asarray(m.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))) > 0
    ticks = sub & ~opened
    # their anti-aliased edges too (grey outlines left behind otherwise), but never the ring or the mouth
    tm = Image.fromarray((ticks * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
    ticks = (np.asarray(tm) > 0) & ~opened & ~hole
    ring_out = np.asarray(m.filter(ImageFilter.MaxFilter(9))) > 0
    around = ring_out & ~sub & ~hole
    ay, ax = np.where(around)
    skin = np.median(im[by + ay, bx + ax, :3], axis=0) if len(ay) else np.array([240, 200, 170])
    ty, tx = np.where(ticks)
    for y, x in zip(ty, tx):
        im[by + y, bx + x, :3] = skin
    Image.fromarray(im).save(path, "WEBP", lossless=True, quality=100, method=6)
    return True


def main():
    os.makedirs(ORIG, exist_ok=True)
    done = []
    for s in SKINS:
        for p in sorted(glob.glob(os.path.join(ROOT, "game", "art", "cast", f"cast_{s}_ghost*.webp"))):
            o = os.path.join(ORIG, os.path.basename(p))
            if not os.path.exists(o):
                shutil.copy2(p, o)
            shutil.copy2(o, p)  # always from the original (re-runnable)
            ok = fix(p)
            done.append((os.path.basename(p), ok))
            print(os.path.basename(p), "fixed" if ok else "NO RING FOUND")
    if "--contact" in sys.argv:
        out = sys.argv[sys.argv.index("--contact") + 1]
        cells = []
        for name, ok in done:
            for src in (os.path.join(ORIG, name), os.path.join(ROOT, "game", "art", "cast", name)):
                im = Image.open(src).convert("RGBA")
                w, h = im.size
                c = im.crop((0, 0, w, int(h * 0.55)))
                c.thumbnail((180, 180))
                bg = Image.new("RGBA", (180, 180), (190, 190, 190, 255))
                bg.alpha_composite(c, ((180 - c.width) // 2, 0))
                cells.append(bg)
        cols = 12
        sheet = Image.new("RGB", (180 * cols, 180 * ((len(cells) + cols - 1) // cols)), (120, 120, 120))
        for i, c in enumerate(cells):
            sheet.paste(c.convert("RGB"), ((i % cols) * 180, (i // cols) * 180))
        sheet.save(out)
        print("contact", out)


if __name__ == "__main__":
    main()

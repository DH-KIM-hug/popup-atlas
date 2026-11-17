#!/usr/bin/env python3
"""Chroma-key magenta card sheets and split them into single cards.
  python3 tools/art/key_cards.py [sheet_id ...]      (default: every raw sheet)
raw:   art_src/cards/raw/<sheet>.png
out:   art_src/cards/keyed/<sheet>_<nn>.png  (RGBA, trimmed, bottom edge = lowest opaque row)
       art_src/cards/keyed/_contact_<sheet>.png (labelled check sheet on grey)
Keying: m = min(R,B) - G. Hard background m>=110 & R,B>150. Soft alpha only inside a band near the hard
background (protects terracotta / red paper inside the object), despill in that band, 3px median on alpha."""
import collections, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = "/Users/house_of_4k2b/orca/popup-atlas"
RAW = f"{ROOT}/art_src/cards/raw"
OUT = f"{ROOT}/art_src/cards/keyed"


def dilate(mask, r):
    m = Image.fromarray((mask * 255).astype(np.uint8))
    return np.asarray(m.filter(ImageFilter.MaxFilter(2 * r + 1))) > 127


def key(img):
    a = np.asarray(img.convert("RGB")).astype(np.int32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = np.minimum(R, B) - G
    hard = (m >= 110) & (R > 150) & (B > 150)
    band = dilate(hard, 4)
    alpha = np.ones(m.shape, np.float32)
    soft = np.clip((75 - m) / 45.0, 0, 1)
    alpha[band] = soft[band]
    alpha[hard] = 0
    # Hot-pink leftovers trapped between stems (no palette paper has blue well above green with red high:
    # terracotta, salmon, red all have B <= G). Removed everywhere, softly, with a 1px grow.
    hp = np.clip(((B - G) - 25) / 30.0, 0, 1) * ((R > 170) & (R - G > 90))
    hp = np.maximum(hp, (dilate(hp > 0.5, 1) * 0.7))
    alpha = np.minimum(alpha, 1 - hp)
    band = band | (hp > 0)
    # Despill: in the band pull R and B down to G level for magenta-tinted pixels.
    rgb = a.astype(np.float32)
    sp = band & (m > 0)
    amt = m[sp].astype(np.float32)
    rgb[..., 0][sp] -= amt
    rgb[..., 2][sp] -= amt
    rgb = np.clip(rgb, 0, 255)
    al = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(3))
    al = np.asarray(al).astype(np.float32) / 255
    # Kill faint fringe: anything below 0.25 goes, above 0.85 is solid.
    al = np.clip((al - 0.25) / 0.6, 0, 1)
    return np.dstack([rgb, al * 255]).astype(np.uint8)


def label(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32)
    n = 0
    for y0, x0 in zip(*np.nonzero(mask)):
        if lab[y0, x0]:
            continue
        n += 1
        lab[y0, x0] = n
        q = collections.deque([(y0, x0)])
        while q:
            y, x = q.popleft()
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    q.append((yy, xx))
    return lab, n


def split(rgba, sheet):
    H, W = rgba.shape[:2]
    S = 4
    small = Image.fromarray(rgba[..., 3]).resize((W // S, H // S), Image.BOX)
    sm = np.asarray(small) > 40
    sm = dilate(sm, 1)          # merge loose petals / leaves of one object (~8 px at full res)
    lab, n = label(sm)
    parts = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) * S * S < 0.004 * H * W:
            continue
        parts.append((ys.min() * S, ys.max() * S + S, xs.min() * S, xs.max() * S + S, lab == i))
    # Reading order: rows by bottom edge (tolerance 12% of H), then x.
    parts.sort(key=lambda p: (round(p[1] / (H * 0.12)), p[2]))
    outs = []
    for k, (y0, y1, x0, x1, lm) in enumerate(parts):
        own = np.asarray(Image.fromarray((lm * 255).astype(np.uint8)).resize((W // S * S, H // S * S), Image.NEAREST))
        own = np.pad(own, ((0, H - own.shape[0]), (0, W - own.shape[1]))) > 0
        own = dilate(own, 2)
        c = rgba.copy()
        c[..., 3] = np.where(own, c[..., 3], 0)
        al = c[..., 3] > 20
        ys, xs = np.nonzero(al)
        yA, yB, xA, xB = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        pad = 6
        crop = c[max(0, yA - pad):yB, max(0, xA - pad):min(W, xB + pad)]   # no pad under the hinge edge
        outs.append(Image.fromarray(crop, "RGBA"))
    return outs


def contact(cards, sheet):
    th = 220
    cols = min(6, max(1, len(cards)))
    rows = (len(cards) + cols - 1) // cols
    cw = 260
    sh = Image.new("RGB", (cols * cw, rows * (th + 30)), (110, 120, 110))
    d = ImageDraw.Draw(sh)
    for i, c in enumerate(cards):
        s = min(th / c.height, (cw - 10) / c.width)
        t = c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))), Image.LANCZOS)
        x = (i % cols) * cw + 5
        y = (i // cols) * (th + 30)
        sh.paste(t, (x, y + th - t.height), t)
        d.text((x, y + th + 6), f"{sheet}_{i:02d} {c.width}x{c.height}", fill=(255, 255, 255))
    sh.save(f"{OUT}/_contact_{sheet}.png")


def main():
    os.makedirs(OUT, exist_ok=True)
    sheets = sys.argv[1:] or sorted(f[:-4] for f in os.listdir(RAW) if f.endswith(".png"))
    for s in sheets:
        p = f"{RAW}/{s}.png"
        if not os.path.exists(p):
            print("missing", s)
            continue
        for f in os.listdir(OUT):
            if f.startswith(s + "_") and f[len(s) + 1:-4].isdigit():
                os.remove(f"{OUT}/{f}")
        rgba = key(Image.open(p))
        cards = split(rgba, s)
        for i, c in enumerate(cards):
            c.save(f"{OUT}/{s}_{i:02d}.png")
        contact(cards, s)
        print(s, len(cards), "cards")


if __name__ == "__main__":
    main()

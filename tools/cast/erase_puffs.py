"""Erase baked breath puffs from cast figures (2026-11-23, user on turnip v3: "왜 자꾸 이상한데서 김이 모락모락 나는거???").

The farm family's sit_tired figures were drawn huffing: a cream cloud beside the face with a wisp from the mouth.
For each figure: the puff = the cream component grown from a seed in the cloud (inside a box, so grandpa's cream beard
is not taken), dilated 2 px for its fringe. Puff pixels inside the figure's own silhouette (a morphological closing of
the figure without the puff: the wisp over cheek / scarf / beard) are inpainted from the surrounding non-puff colours;
the rest (the cloud over the background) becomes transparent.

Idempotent: the first run keeps the originals in art_src/cast/puff_orig/ and every run starts from those.
  python3 tools/cast/erase_puffs.py            # writes game/art/cast/<id>.webp
"""
import shutil
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
CAST = ROOT / "game/art/cast"
ORIG = ROOT / "art_src/cast/puff_orig"

# id: (seed xy in the cloud, boxes [x0, y0, x1, y1] the puff lies in: the cloud and the wisp, never the cream
# collar / apron / beard; grandpa's wisp lies on his cream beard and stays). The first box of a two-box entry is the
# wisp's: every cream pixel in it is puff (the thin taper breaks the cloud's connectivity). Last: the closing size
# (px) that rebuilds the figure's own silhouette under the puff.
FIGS = {
    "cast_farm_grandpa_sit_tired": ((282, 160), [(250, 150, 258, 168), (254, 120, 352, 200)], 9),
    "cast_farm_grandma_sit_tired": ((292, 190), [(205, 170, 265, 193), (255, 150, 330, 225)], 13),
    # the girl's wisp crosses the open gap between chin and collar: a small closing keeps that gap open
    "cast_farm_girl_sit_tired": ((262, 237), [(170, 200, 300, 252), (230, 195, 300, 275)], 7),
}

# grandpa's wisp is a thin pink line on his cream beard: its pink texels in this box are repainted from the beard
LINES = {"cast_farm_grandpa_sit_tired": (203, 154, 250, 167)}

# the girl's jaw ran under her wisp: the jaw line between the two visible ends is filled (polygon, px) and painted
FILL = {"cast_farm_girl_sit_tired": [(227, 226), (219, 230), (204, 241), (198, 245), (186, 245), (186, 226)]}


def cream(px):
    r, g, b = px[..., 0].astype(int), px[..., 1].astype(int), px[..., 2].astype(int)
    mn = np.minimum(np.minimum(r, g), b)
    mx = np.maximum(np.maximum(r, g), b)
    return (mn > 160) & (mx - mn < 92) & (b > 160)


def grow(mask, seed):
    h, w = mask.shape
    out = np.zeros_like(mask)
    q = deque([seed[::-1]])
    while q:
        y, x = q.popleft()
        if y < 0 or x < 0 or y >= h or x >= w or out[y, x] or not mask[y, x]:
            continue
        out[y, x] = True
        q.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    return out


def morph(mask, size, op):
    im = Image.fromarray((mask * 255).astype(np.uint8))
    im = im.filter(ImageFilter.MaxFilter(size) if op == "max" else ImageFilter.MinFilter(size))
    return np.array(im) > 127


def inpaint(rgb, known, todo):
    rgb = rgb.astype(float).copy()
    known = known.copy()
    for _ in range(400):
        left = todo & ~known
        if not left.any():
            break
        acc = np.zeros_like(rgb)
        n = np.zeros(known.shape)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            k = np.roll(np.roll(known, dy, 0), dx, 1)
            c = np.roll(np.roll(rgb, dy, 0), dx, 1)
            acc += c * k[..., None]
            n += k
        fill = left & (n > 0)
        rgb[fill] = acc[fill] / n[fill][:, None]
        known = known | fill
    return rgb


def main():
    ORIG.mkdir(parents=True, exist_ok=True)
    for fid, (seed, box, close) in FIGS.items():
        dst = CAST / f"{fid}.webp"
        src = ORIG / f"{fid}.webp"
        if not src.exists():
            shutil.copy2(dst, src)
        a = np.array(Image.open(src).convert("RGBA"))
        alpha = a[..., 3] > 128
        inbox = np.zeros_like(alpha)
        for x0, y0, x1, y1 in box:
            inbox[y0:y1, x0:x1] = True
        cr = cream(a[..., :3]) & alpha
        puff = grow(cr & inbox, seed)
        if len(box) > 1:
            x0, y0, x1, y1 = box[0]
            wisp = np.zeros_like(alpha)
            wisp[y0:y1, x0:x1] = True
            puff |= cr & wisp
        puff = morph(puff, 5, "max") & inbox  # its fringe (outline / keyed edge), 2 px
        body = alpha & ~puff
        sil = morph(morph(body, close, "max"), close, "min")  # the figure's own silhouette: the wisp inside it is filled
        ring = morph(puff, 3, "max")
        paint = ring & sil & alpha  # the puff inside the silhouette + a 1 px ring (re-sampled, a pixel away)
        known = body & ~ring
        rgb = inpaint(a[..., :3], known, paint)
        out = a.copy()
        out[..., :3] = np.where(paint[..., None], np.clip(rgb, 0, 255), a[..., :3]).astype(np.uint8)
        out[..., 3] = np.where(puff & ~sil, 0, a[..., 3])
        if fid in FILL:
            from PIL import ImageDraw
            pm = Image.new("L", alpha.shape[::-1], 0)
            ImageDraw.Draw(pm).polygon(FILL[fid], fill=255)
            fill = (np.array(pm) > 127) & ~(out[..., 3] > 128)
            rgb4 = inpaint(out[..., :3], (out[..., 3] > 128), fill)
            out[..., :3] = np.where(fill[..., None], np.clip(rgb4, 0, 255), out[..., :3]).astype(np.uint8)
            out[..., 3] = np.where(fill, 255, out[..., 3])
        # smooth the new cut near the puff (steps where the cloud / wisp met the face, scarf, chin)
        near = morph(puff, 9, "max")
        soft = np.array(Image.fromarray(out[..., 3]).filter(ImageFilter.GaussianBlur(2.0)))
        cut = np.where(soft > 140, 255, 0).astype(np.uint8)
        grown = cut.astype(bool) & ~(out[..., 3] > 128)  # texels the smoothing adds: colour them from their neighbours
        out[..., 3] = np.where(near, cut, out[..., 3])
        if (grown & near).any():
            rgb3 = inpaint(out[..., :3], (out[..., 3] > 128) & ~(grown & near), grown & near)
            out[..., :3] = np.where((grown & near)[..., None], np.clip(rgb3, 0, 255), out[..., :3]).astype(np.uint8)
        if fid in LINES:
            x0, y0, x1, y1 = LINES[fid]
            px = out[..., :3].astype(int)
            pink = (px[..., 0] - px[..., 1] > 30) & (px[..., 2] > 140)
            lb = np.zeros_like(alpha)
            lb[y0:y1, x0:x1] = True
            line = morph(pink & lb, 3, "max") & lb & alpha
            rgb2 = inpaint(out[..., :3], alpha & ~line & ~puff, line)
            out[..., :3] = np.where(line[..., None], np.clip(rgb2, 0, 255), out[..., :3]).astype(np.uint8)
        Image.fromarray(out).save(dst, "WEBP", lossless=True)
        print(fid, "puff px", int(puff.sum()), "painted", int(paint.sum()), "cleared", int((puff & ~sil).sum()))


if __name__ == "__main__":
    main()

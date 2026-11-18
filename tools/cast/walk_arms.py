#!/usr/bin/env python3
"""Separate swinging arm cards for the calm walking figures (CastPuppet swings them opposite to the legs).

  python3 tools/atlas/slice_atlas.py art_src/cast/raw/cast_traveller_walk_armless.png --out art_src/cast/sliced
  python3 tools/cast/walk_arms.py          (after front_legs / lift_legs; cut_cast_rig.py calls it itself)

2026-11-18 (user: "군인처럼 걷는 거 같아" — arms frozen at the sides). For each figure in ARMS:
  * arm_l / arm_r = the figure's OWN sleeve + hand pixels (exact design, nothing redrawn), cut along the sleeve seam
    (`seam`, a polyline in figure px, the arm is on the outer side of it) and capped at the top by a disc around the
    shoulder `pivot` (radius CAP): the cap boundary is a circle about the pivot, so when the card rotates about the pivot
    its top edge does not move and never shows a cut.
  * body = the figure's body card with the arm pixels replaced by the torso of the Codex armless sheet
    (cast_traveller_walk_armless, the same three figures drawn without arms), registered to the figure (scale + offset
    search on the torso silhouette) and colour-matched per channel to the figure's own garment next to the seam; only
    the hidden area under the arm is taken from it (the face, front and everything else stay the original pixels).
rig.json parts.arm_l / arm_r = {bbox, pivot} (figure px). Old body PNGs are kept in art_src/cast/rig_backup_v3/.
Expression figures with arms in a pose (hugging, fanning, hands on head) keep baked arms.
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SRC = os.path.join(ROOT, "game", "art", "cast")
RIG = os.path.join(SRC, "rig")
ARMLESS = os.path.join(ROOT, "art_src", "cast", "sliced", "cast_traveller_walk_armless")
CAP = 18
# seam polylines (top → bottom, figure px) and shoulder pivots, read off 3x grid crops of each figure
ARMS = {
    "cast_traveller_coat_calm": {"src": 0,
        "arm_l": {"pivot": [72, 272], "ymax": 467,
                  "seam": [(90, 250), (88, 265), (66, 402), (52, 406), (50, 412), (50, 452), (45, 462)]},
        "arm_r": {"pivot": [247, 272], "ymax": 467,
                  "seam": [(229, 250), (231, 265), (253, 402), (267, 406), (269, 412), (269, 452), (274, 462)]}},
    "cast_traveller_coat_nohat_calm": {"src": 1,
        "arm_l": {"pivot": [72, 255], "ymax": 447,
                  "seam": [(89, 235), (87, 250), (63, 382), (52, 386), (50, 392), (50, 432), (45, 442)]},
        "arm_r": {"pivot": [246, 255], "ymax": 447,
                  "seam": [(229, 235), (231, 250), (255, 382), (266, 386), (268, 392), (268, 432), (273, 442)]}},
    "cast_traveller_nocoat_calm": {"src": 2,
        "arm_l": {"pivot": [78, 250], "ymax": 999, "seam": [(90, 222), (88, 235), (86, 350), (82, 372), (63, 380), (63, 720)]},
        "arm_r": {"pivot": [224, 250], "ymax": 999,
                  "seam": [(212, 222), (214, 235), (216, 350), (220, 372), (239, 380), (239, 720)]}},
}


def seam_x(seam, ys):
    sy = np.array([p[1] for p in seam], float)
    sx = np.array([p[0] for p in seam], float)
    return np.interp(ys, sy, sx)


def arm_mask(alpha, side, spec):
    h, w = alpha.shape
    yy, xx = np.mgrid[0:h, 0:w]
    sx = seam_x(spec["seam"], np.arange(h))[:, None]
    outer = xx < sx if side == "arm_l" else xx > sx
    px, py = spec["pivot"]
    cap = (xx - px) ** 2 + (yy - py) ** 2 <= CAP * CAP
    return (alpha > 0) & (yy <= spec["ymax"]) & ((outer & (yy >= py)) | cap)


def register(orig_a, src, excl):
    """Scale + offset of `src` (RGBA, tight) onto the figure canvas maximising torso-silhouette IoU (outside `excl`)."""
    h, w = orig_a.shape
    ys, xs = np.where(orig_a > 128)
    H = ys.max() - ys.min()
    base = H / src.shape[0]
    best = None
    om = (orig_a > 128) & ~excl
    rows = slice(int(ys.min() + 0.3 * H), int(ys.min() + 0.75 * H))
    for k in np.linspace(0.94, 1.06, 13):
        s = base * k
        im = Image.fromarray(src).resize((max(1, round(src.shape[1] * s)), max(1, round(src.shape[0] * s))), Image.LANCZOS)
        a = np.array(im)
        for dy in range(-16, 17, 4):
            for dx in range(-16, 17, 2):
                x0 = (w - a.shape[1]) // 2 + dx
                y0 = ys.max() + 1 - a.shape[0] + dy
                can = np.zeros((h, w), bool)
                X0, Y0 = max(0, x0), max(0, y0)
                X1, Y1 = min(w, x0 + a.shape[1]), min(h, y0 + a.shape[0])
                can[Y0:Y1, X0:X1] = a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, 3] > 128
                c = can[rows] & ~excl[rows]
                o = om[rows]
                iou = (c & o).sum() / max(1, (c | o).sum())
                if best is None or iou > best[0]:
                    best = (iou, s, x0, y0)
    iou, s, x0, y0 = best
    a = np.array(Image.fromarray(src).resize((max(1, round(src.shape[1] * s)), max(1, round(src.shape[0] * s))), Image.LANCZOS))
    out = np.zeros((h, w, 4), np.uint8)
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(w, x0 + a.shape[1]), min(h, y0 + a.shape[0])
    out[Y0:Y1, X0:X1] = a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    return out, iou, s


def colour_match(reg, fig, fill, band):
    """Per-channel gain on `reg` so its pixels next to the fill match the figure's own pixels there (band = ring mask)."""
    m = band & (fig[..., 3] > 220) & (reg[..., 3] > 220)
    if m.sum() < 50:
        return np.ones(3)
    g = np.clip(np.median(fig[..., :3][m], 0) / np.maximum(np.median(reg[..., :3][m], 0), 1), 0.75, 1.3)
    reg[..., :3] = np.clip(reg[..., :3].astype(float) * g, 0, 255).astype(np.uint8)
    return g


def dilate(m, n):
    for _ in range(n):
        g = m.copy()
        g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
        m = g
    return m


def main(figs=None):
    rig_p = os.path.join(RIG, "rig.json")
    rig = json.load(open(rig_p))
    for fid, spec in ARMS.items():
        if figs is not None and fid not in figs:
            continue
        r = rig[fid]
        if "arm_l" in r["parts"]:
            raise RuntimeError(f"{fid}: body already has its arms cut off; re-run tools/cast/cut_cast_rig.py {fid}")
        fig = np.array(Image.open(os.path.join(SRC, fid + ".webp")).convert("RGBA"))
        h, w = fig.shape[:2]
        bb = r["parts"]["body"]["bbox"]
        body = np.zeros_like(fig)
        body[bb[1]:bb[3], bb[0]:bb[2]] = np.array(Image.open(os.path.join(RIG, f"{fid}_body.png")).convert("RGBA"))
        masks = {s: arm_mask(body[..., 3], s, spec[s]) for s in ("arm_l", "arm_r")}
        allarm = masks["arm_l"] | masks["arm_r"]
        src = np.array(Image.open(os.path.join(ARMLESS, f"cast_traveller_walk_armless_{spec['src']:02d}.webp")).convert("RGBA"))
        ys, xs = np.where(src[..., 3] > 8)
        src = src[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        reg, iou, s = register(fig[..., 3], src, dilate(allarm, 4))
        # fill only below the cap discs' centre line (the shoulders above stay original) and inside the arm masks
        fill = allarm.copy()
        band = dilate(allarm, 10) & ~dilate(allarm, 3)
        g = colour_match(reg, fig, fill, band)
        newbody = body.copy()
        newbody[fill] = 0
        take = fill & (reg[..., 3] > 0)
        newbody[take] = reg[take]
        # never leave the body with a fill pixel where the original body had nothing and the arm is not over it either
        for side in ("arm_l", "arm_r"):
            arm = np.zeros_like(body)
            arm[masks[side]] = body[masks[side]]
            ys, xs = np.where(arm[..., 3] > 8)
            abb = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
            Image.fromarray(arm[abb[1]:abb[3], abb[0]:abb[2]]).save(os.path.join(RIG, f"{fid}_{side}.png"))
            r["parts"][side] = {"bbox": abb, "pivot": list(spec[side]["pivot"])}
        ys, xs = np.where(newbody[..., 3] > 8)
        nbb = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        Image.fromarray(newbody[nbb[1]:nbb[3], nbb[0]:nbb[2]]).save(os.path.join(RIG, f"{fid}_body.png"))
        r["parts"]["body"]["bbox"] = nbb
        print(f"{fid}: armless iou {iou:.3f} scale {s:.3f} gain {np.round(g, 2).tolist()} body {nbb} "
              f"arms {r['parts']['arm_l']['bbox']} {r['parts']['arm_r']['bbox']}")
    json.dump(rig, open(rig_p, "w"), indent=1)


if __name__ == "__main__":
    main()

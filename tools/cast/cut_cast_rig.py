#!/usr/bin/env python3
"""Cut standing cast figures (front-on, legs apart) into PaperPuppet layers: body + hips + leg_l + leg_r.

  python3 tools/cast/cut_cast_rig.py            (from repo root; figures listed in FIGS below)

Input: the sliced RGBA figure cards in game/art/cast/<id>.webp. Output: game/art/cast/rig/<id>_{body,hips,leg_l,leg_r}.png
(each cropped to its alpha bbox) + game/art/cast/rig/rig.json in the chars_rig format (size, full_bbox, split, crotch,
parts{leg_l{hip,bbox}, leg_r{hip,bbox}, hips{bbox}, body{bbox}}) so CastPuppet places them exactly like PaperPuppet.
Method (no colour classifier, works for any outfit): the split column is the open gap between the feet; the crotch is the top
of that gap; each leg = the bottom-touching opaque component on its side below the crotch, trimmed where it widens into
the coat hem; the hidden leg top up to the hip is repainted in the leg's own flat trouser colour with a rounded cap.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SRC = os.path.join(ROOT, "game", "art", "cast")
OUT = os.path.join(SRC, "rig")
FIGS = ["cast_traveller_coat", "cast_traveller_coat_nohat", "cast_traveller_coat_hold",
        "cast_traveller_nocoat", "cast_traveller_nocoat_nohat",
        # 2026-11-18 expressions
        "cast_traveller_coat_surprised", "cast_traveller_coat_nohat_surprised", "cast_traveller_coat_nohat_cold",
        "cast_traveller_coat_calm", "cast_traveller_coat_nohat_calm", "cast_traveller_coat_open_hot",
        "cast_traveller_coat_open_fan", "cast_traveller_nocoat_relieved", "cast_traveller_nocoat_nohat_relieved",
        "cast_traveller_nocoat_calm"]
## Extra hinged arm parts cut out of the body card (card px): poly = what moves (hand + what it holds), pivot = wrist.
## CastPuppet swings the part about the pivot (fanning).
ARM_PARTS = {
    "cast_traveller_coat_open_fan": {"fan": {"poly": [(0, 89), (104, 89), (119, 100), (122, 135), (105, 175), (85, 205),
                                                     (70, 232), (60, 246), (20, 248), (0, 238)], "pivot": [40, 246]}},
}
TARGET_H = None  # None: keep the sliced card resolution (no resampling); an int resamples the figure to that height


def comp_touching_bottom(mask, rows=6):
    h, w = mask.shape
    keep = np.zeros_like(mask)
    q = deque()
    for y in range(h - rows, h):
        for x in np.where(mask[y])[0]:
            if not keep[y, x]:
                keep[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not keep[ny, nx]:
                keep[ny, nx] = True
                q.append((ny, nx))
    return keep


def components(mask):
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
    h, w = img.shape[:2]
    for y in range(cy - r - 2, cy + r + 3):
        for x in range(cx - r - 2, cx + r + 3):
            if not (0 <= y < h and 0 <= x < w) or img[y, x, 3] < 128:
                continue
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if r < d <= r + 1.6 and (x - cx) + (y - cy) > 0:
                img[y, x, :3] = (img[y, x, :3] * 0.62).astype(np.uint8)
            elif d <= r:
                hl = max(0.0, 1.0 - (((x - cx + r * 0.35) ** 2 + (y - cy + r * 0.35) ** 2) ** 0.5) / (r * 0.6))
                base = np.array([150, 112, 52]) if d < r - 1.4 else np.array([88, 60, 26])
                img[y, x, :3] = np.clip(base + (np.array([255, 232, 170]) - base) * hl * 0.8, 0, 255).astype(np.uint8)
                img[y, x, 3] = 255


def save_cropped(img, name):
    ys, xs = np.where(img[..., 3] > 8)
    bb = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    Image.fromarray(img[bb[1]:bb[3], bb[0]:bb[2]]).save(os.path.join(OUT, name))
    return bb


def cut(fid):
    src = Image.open(os.path.join(SRC, fid + ".webp")).convert("RGBA")
    if TARGET_H:
        s = TARGET_H / src.height
        src = src.resize((max(1, round(src.width * s)), TARGET_H), Image.LANCZOS)
    a = np.array(src)
    h, w = a.shape[:2]
    op = a[..., 3] > 128
    ys_all, xs_all = np.where(op)
    fy0, fy1 = int(ys_all.min()), int(ys_all.max()) + 1
    H = fy1 - fy0
    rng = np.random.default_rng(11)
    # split: the most open column near the centre in the foot/shin band
    band = op[int(fy1 - 0.2 * H): fy1 - 2]
    cols = band.sum(0).astype(float)
    cx0, cx1 = int(w * 0.32), int(w * 0.68)
    split = cx0 + int(np.argmin(cols[cx0:cx1] + np.abs(np.arange(cx0, cx1) - w / 2) * 0.02))
    colA = op[:, max(0, split - 2): split + 3].any(1)
    y = fy1 - 3
    while y > fy0 and not colA[y]:
        y -= 1
    crotch = y + 1  # first open row below the body at the split
    if crotch > fy1 - 0.12 * H:
        raise RuntimeError(f"{fid}: no gap between the legs (crotch {crotch}, bottom {fy1})")
    below = op.copy()
    below[:crotch] = False
    parts, legmask, info = {}, np.zeros_like(op), {}
    for side, (xa, xb) in (("leg_l", (0, split)), ("leg_r", (split, w))):
        m = np.zeros_like(op)
        m[:, xa:xb] = below[:, xa:xb]
        m = comp_touching_bottom(m)
        ext = {yy: (int(np.where(m[yy])[0][0]), int(np.where(m[yy])[0][-1])) for yy in range(h) if m[yy].any()}
        yl = sorted(ext)
        span = yl[-1] - yl[0]
        widths = {yy: ext[yy][1] - ext[yy][0] for yy in yl}
        mid = [widths[yy] for yy in yl if yl[0] + 0.35 * span <= yy <= yl[0] + 0.7 * span]
        ref_w = float(np.median(mid)) if mid else float(np.median(list(widths.values())))
        wide = [yy for yy in yl if yy < yl[0] + 0.5 * span and widths[yy] > ref_w * 1.3]
        full_y = (max(wide) + 3) if wide else yl[0] + 2
        x0f, x1f = ext[full_y]
        # leg pixels keep their print from full_y down; above, flat trouser colour up to the hip
        samp_rows = slice(full_y + 4, min(h, full_y + int(0.12 * H)))
        sm = m[samp_rows, x0f + 3: x1f - 2]
        col = np.median(a[samp_rows, x0f + 3: x1f - 2][..., :3][sm], 0) if sm.any() else np.array([90, 60, 40])
        piv_y = int(crotch - 0.055 * H)
        hip_y = int(piv_y - 0.035 * H)
        cx_leg = (x0f + x1f) / 2.0
        out = np.zeros_like(a)
        # the leg's soft anti-aliased outline (alpha 1..128) goes with the leg, not the body
        keep = m.copy()
        for _ in range(3):
            g = keep.copy()
            g[1:] |= keep[:-1]; g[:-1] |= keep[1:]; g[:, 1:] |= keep[:, :-1]; g[:, :-1] |= keep[:, 1:]
            keep = g
        keep &= a[..., 3] > 0
        keep[:, :xa] = False
        keep[:, xb:] = False
        keep[:full_y] = False
        out[keep] = a[keep]
        r = (x1f - x0f) / 2.0 + 2
        lo_in, hi_in = x0f, x1f
        if side == "leg_l":
            hi_in = max(x1f, split + 3)
        else:
            lo_in = min(x0f, split - 3)
        for yy in range(hip_y, full_y + 2):
            # hidden top tapers toward the hip (to 70 % width) so a swung leg's corner never pokes out past the body
            k = 0.7 + 0.3 * (yy - hip_y) / max(1, full_y - hip_y)
            cxx = (lo_in + hi_in) / 2.0
            lo, hi = int(round(cxx - (cxx - lo_in + 1) * k)), int(round(cxx + (hi_in + 1 - cxx) * k))
            rr = (hi - lo) / 2.0
            dy = (hip_y + rr) - yy
            if dy > 0:
                half = max(0.0, rr * rr - dy * dy) ** 0.5
                c = (lo + hi) / 2.0
                lo, hi = int(round(c - half)), int(round(c + half))
            for x in range(max(0, lo), min(w, hi + 1)):
                if out[yy, x, 3] < 200:
                    shade = 1.0 - 0.10 * (abs(x - cx_leg) / max(1.0, r)) ** 2
                    out[yy, x, :3] = np.clip(col * shade + rng.normal(0, 3.0), 0, 255).astype(np.uint8)
                    out[yy, x, 3] = 255
        legmask |= keep
        # vis = first visible leg row (below the coat hem / at the crotch) and its x span: tools/cast/front_legs.py fits the
        # front-view legs to it
        parts[side] = {"hip": [int(round(cx_leg)), piv_y], "vis": [int(full_y), int(x0f), int(x1f) + 1], "_out": out}
        info[side] = (lo_in, hi_in, col, hip_y, full_y)
    # hips piece (behind body, in front of the leg tops): trouser seat from hip_y to just below the crotch
    hips = np.zeros_like(a)
    for side in ("leg_l", "leg_r"):
        lo_in, hi_in, col, hip_y, full_y = info[side]
        cx = (lo_in + hi_in) / 2.0
        hw = (hi_in - lo_in) / 2.0 + 2
        for yy in range(hip_y, min(h, crotch + 10)):
            for x in range(max(0, lo_in - 1), min(w, hi_in + 2)):
                u = (x - cx) / hw
                if yy > crotch + 8 - 10 * min(1.0, u * u):
                    continue
                hips[yy, x, :3] = np.clip(col + rng.normal(0, 3.0), 0, 255).astype(np.uint8)
                hips[yy, x, 3] = 255
    body = a.copy()
    body[legmask, 3] = 0
    lab, n = components(body[..., 3] > 8)
    if n > 1:
        sizes = np.bincount(lab.ravel())[1:]
        main = 1 + int(sizes.argmax())
        for i in range(1, n + 1):
            if i != main and sizes[i - 1] < 400:
                body[lab == i, 3] = 0
    # nothing of the body may hang below the crotch region except real cards (coat hem, hands): faint leftovers go
    lowfaint = (body[..., 3] < 100)
    lowfaint[:crotch] = False
    body[lowfaint, 3] = 0
    for side in ("leg_l", "leg_r"):
        bx, by = parts[side]["hip"]
        brad(body, bx, by)
        brad(hips, bx, by)
    for pname, spec in ARM_PARTS.get(fid, {}).items():
        pm = Image.new("L", (w, h), 0)
        ImageDraw.Draw(pm).polygon(spec["poly"], fill=255)
        sel = np.array(pm) > 127
        arm = np.zeros_like(body)
        arm[sel] = body[sel]
        body[sel, 3] = 0
        parts[pname] = {"bbox": save_cropped(arm, f"{fid}_{pname}.png"), "pivot": list(spec["pivot"])}
    for side in ("leg_l", "leg_r"):
        out = parts[side].pop("_out")
        parts[side]["bbox"] = save_cropped(out, f"{fid}_{side}.png")
    parts["hips"] = {"bbox": save_cropped(hips, f"{fid}_hips.png")}
    parts["body"] = {"bbox": save_cropped(body, f"{fid}_body.png")}
    return {"size": [w, h], "full_bbox": [int(xs_all.min()), fy0, int(xs_all.max()) + 1, fy1],
            "split": split, "crotch": int(crotch), "parts": parts}


def preview(rig, path):
    """Rest pose + legs swung ±22° for every figure, on grey: checks registration and what the swing reveals."""
    tiles = []
    for fid, r in rig.items():
        for ang in (0, 22, -22):
            w, h = r["size"]
            im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            for side in ("leg_r", "leg_l"):
                p = r["parts"][side]
                leg = Image.open(os.path.join(OUT, f"{fid}_{side}.png"))
                full = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                full.paste(leg, tuple(p["bbox"][:2]))
                a_ = ang if side == "leg_l" else -ang
                full = full.rotate(a_, resample=Image.BICUBIC, center=tuple(p["hip"]))
                im.alpha_composite(full)
            for part in ("hips", "body") + tuple(k for k in r["parts"] if k not in ("hips", "body", "leg_l", "leg_r")):
                p = r["parts"][part]
                im.alpha_composite(Image.open(os.path.join(OUT, f"{fid}_{part}.png")), tuple(p["bbox"][:2]))
            tiles.append(im)
    tw = max(t.width for t in tiles) + 10
    cols = 6
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, 770 * rows), (128, 128, 124))
    for k, t in enumerate(tiles):
        sheet.paste(t, ((k % cols) * tw, (k // cols) * 770), t)
    sheet.save(path)
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    figs = sys.argv[1:] or FIGS
    rig_p = os.path.join(OUT, "rig.json")
    rig = json.load(open(rig_p)) if os.path.exists(rig_p) else {}
    for f in figs:
        rig[f] = cut(f)
        print(f, "crotch", rig[f]["crotch"], "hips", rig[f]["parts"]["leg_l"]["hip"], rig[f]["parts"]["leg_r"]["hip"])
    json.dump(rig, open(rig_p, "w"), indent=1)
    # 2026-11-18: swap the side-view legs (toes out = duck walk toward the camera) for the front-view leg sheet
    import front_legs
    if os.path.isdir(front_legs.SL):
        front_legs.main()
        rig = json.load(open(rig_p))
    # 2026-11-18 walk v4: bent-knee swing legs (half / lift) and separate swinging arms for the calm walking figures
    import lift_legs, walk_arms
    if os.path.isdir(os.path.join(lift_legs.SLICED, "cast_traveller_legs_lift")):
        lift_legs.main()
    if os.path.isdir(walk_arms.ARMLESS):
        cut_now = [f for f in walk_arms.ARMS if f in figs]
        if cut_now:
            walk_arms.main(cut_now)
    rig = json.load(open(rig_p))
    print(preview(rig, os.path.join(ROOT, "art_src", "cast", "qa", "rig_preview.png")))

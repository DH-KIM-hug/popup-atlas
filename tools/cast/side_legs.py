#!/usr/bin/env python3
"""Side-view legs for the SIDE walk figures (brad-jointed paper puppet seen in profile), 2026-11-18.

  python3 tools/atlas/slice_atlas.py art_src/cast/raw/cast_tp_legs_side.png --out art_src/cast/sliced
  python3 tools/cast/side_legs.py          (after cut_cast_rig.py; cut_cast_rig calls it itself)

The side figures are drawn mid-stride; cutting their own legs leaves repainted leg tops that show when a leg swings.
Each side figure's leg_l / leg_r is replaced by a drawn side leg (sheet cast_tp_legs_side: near / far pair per
character, foot to the RIGHT, tall plain top hidden behind the body): both legs hang straight from ONE hip joint (the
mean of the two cut hips — in profile both legs pivot at the same point), scaled so the top sits 4 px above the hip and
the sole on the figure's sole line, the far leg (darker) is leg_l and drawn behind, the near leg leg_r. rig.json parts
leg_* get {"side": true}; CastPuppet (phase 2) swings them fore/aft about the hip (±20–25°), knee-free.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from characters import sliced_path, char_of
import three_pigs_cast

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
RIG = os.path.join(ROOT, "game", "art", "cast", "rig")
SHEET = "cast_tp_legs_side"
SLOT = {"pig_a": 0, "pig_b": 1, "pig_c": 2, "wolf": 3}
SIDE_FIGS = [e["id"] for e in three_pigs_cast.ENTRIES if e["rigged"] and e["view"] == "side"]


def piece(k):
    im = np.array(Image.open(sliced_path(SHEET, k, "x")).convert("RGBA"))
    ys, xs = np.where(im[..., 3] > 8)
    return im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def main(figs=None):
    if not os.path.isdir(os.path.join(ROOT, "art_src", "cast", "sliced", SHEET)):
        return
    rig_p = os.path.join(RIG, "rig.json")
    rig = json.load(open(rig_p))
    for fid in SIDE_FIGS:
        if fid not in rig or (figs is not None and fid not in figs):
            continue
        r = rig[fid]
        slot = SLOT[char_of(fid)]
        near, far = piece(2 * slot), piece(2 * slot + 1)
        hl, hr = r["parts"]["leg_l"]["hip"], r["parts"]["leg_r"]["hip"]
        hx, hy = int(round((hl[0] + hr[0]) / 2)), int(min(hl[1], hr[1]))
        H = r["full_bbox"][3] - r["full_bbox"][1]
        top = hy - int(round(0.035 * H))
        sole = r["full_bbox"][3]
        for side, pc in (("leg_l", far), ("leg_r", near)):
            s = (sole - top) / pc.shape[0]
            a = np.array(Image.fromarray(pc).resize((max(1, round(pc.shape[1] * s)), sole - top), Image.LANCZOS))
            # centre the shin column (the piece's top half; the foot sticks out to the right) under the hip
            al = a[: a.shape[0] // 2, :, 3] > 128
            cols = np.where(al.any(0))[0]
            c = (cols[0] + cols[-1]) / 2.0
            x0 = int(round(hx - c))
            Image.fromarray(a).save(os.path.join(RIG, f"{fid}_{side}.png"))
            p = r["parts"][side]
            p["hip"] = [hx, hy]
            p["bbox"] = [x0, top, x0 + a.shape[1], sole]
            p["side"] = True
            p.pop("alt", None)
        # hips piece: the cutter's seat block spans the old stride (a flat rectangle behind the tail); in profile both
        # legs share one joint, so the hips piece is just a round cap over that joint in the near leg's top colour
        rr = max(4, int(round(0.45 * (r["parts"]["leg_r"]["bbox"][2] - r["parts"]["leg_r"]["bbox"][0]) * 0.6)))
        col = np.median(near[: max(2, near.shape[0] // 5), :, :3][near[: max(2, near.shape[0] // 5), :, 3] > 200], 0)
        yy, xx = np.mgrid[0:2 * rr + 1, 0:2 * rr + 1]
        cap = np.zeros((2 * rr + 1, 2 * rr + 1, 4), np.uint8)
        m = (xx - rr) ** 2 + (yy - rr) ** 2 <= rr * rr
        cap[m, :3] = col.astype(np.uint8)
        cap[m, 3] = 255
        Image.fromarray(cap).save(os.path.join(RIG, f"{fid}_hips.png"))
        r["parts"]["hips"] = {"bbox": [hx - rr, hy - rr, hx + rr + 1, hy + rr + 1], "side": True}
        print(f"{fid}: side legs at hip {hx},{hy} sole {sole}")
    json.dump(rig, open(rig_p, "w"), indent=1)


if __name__ == "__main__":
    main()

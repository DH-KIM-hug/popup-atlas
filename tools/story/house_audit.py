#!/usr/bin/env python3
"""House orbit audit sheet (2026-11-23): python3 tools/story/house_audit.py OUT_DIR TALE [--label before]

Reads OUT_DIR/<tale>__<house>__<view>.png (solo renders on magenta from tools/story/house_orbit.gd) and
OUT_DIR/<tale>__story.png. Per view: magenta pixels ENCLOSED by the house (not connected to the image border) are
background showing through the house: seams between front / side / roof, slots under the eaves, open backs, light
leaks. They are painted red on the sheet and counted (HOLES <house> <view> px). Writes OUT_DIR/<tale>_audit.jpg and
OUT_DIR/<tale>_audit.json.
"""
import glob, json, os, sys
import numpy as np
from PIL import Image, ImageDraw

VIEWS = ["front", "r35", "l35", "r70", "l70", "back_r", "back_l", "high", "low"]
CW, CH = 300, 225


def holes(im):
    a = np.asarray(im.convert("RGB")).astype(int)
    mag = (a[..., 0] > 170) & (a[..., 1] < 90) & (a[..., 2] > 170)
    h, w = mag.shape
    m = np.zeros((h + 2, w + 2), np.uint8)
    m[1:-1, 1:-1] = mag * 255
    m[0, :] = m[-1, :] = 255
    m[:, 0] = m[:, -1] = 255
    li = Image.fromarray(m).copy()
    ImageDraw.floodfill(li, (0, 0), 128)
    enc = np.asarray(li)[1:-1, 1:-1] == 255
    # drop 1-2 px anti-alias specks: keep pixels with an enclosed neighbour
    nb = enc[1:-1, 1:-1] & (enc[:-2, 1:-1] | enc[2:, 1:-1] | enc[1:-1, :-2] | enc[1:-1, 2:])
    enc2 = np.zeros_like(enc)
    enc2[1:-1, 1:-1] = nb
    house = ~mag
    return enc2, mag, int(house.sum())


def main():
    out, tale = sys.argv[1], sys.argv[2]
    label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else ""
    names = []
    for f in sorted(glob.glob(os.path.join(out, f"{tale}__*__front.png"))):
        names.append(os.path.basename(f)[len(tale) + 2:-len("__front.png")])
    rows = max(len(names), len(glob.glob(os.path.join(out, f"{tale}__story_*.png"))))
    sheet = Image.new("RGB", (CW * (len(VIEWS) + 1), CH * max(rows, 1) + 30), (40, 40, 46))
    dr = ImageDraw.Draw(sheet)
    dr.text((6, 8), f"{tale} house orbit audit {label}  (red = background seen through the house)", fill=(255, 255, 255))
    rep = {}
    sps = sorted(glob.glob(os.path.join(out, f"{tale}__story_*.png")))
    for r, nm in enumerate(names):
        y = 30 + r * CH
        if r < len(sps):
            s = Image.open(sps[r]).convert("RGB")
            s.thumbnail((CW, CH))
            sheet.paste(s, (0, y))
            dr.text((4, y + CH - 14), "story " + os.path.basename(sps[r])[len(tale) + 8:-4], fill=(255, 255, 0))
        rep[nm] = {}
        for c, v in enumerate(VIEWS):
            p = os.path.join(out, f"{tale}__{nm}__{v}.png")
            if not os.path.exists(p):
                continue
            im = Image.open(p).convert("RGB")
            enc, mag, area = holes(im)
            a = np.asarray(im).copy()
            a[mag] = (70, 72, 80)  # neutral backdrop on the sheet
            a[enc] = (255, 30, 30)
            n = int(enc.sum())
            rep[nm][v] = {"holes_px": n, "house_px": area, "frac": round(n / max(area, 1), 4)}
            # crop to the house
            ys, xs = np.where(~mag)
            t = Image.fromarray(a)
            if len(xs):
                pad = 20
                t = t.crop((max(0, xs.min() - pad), max(0, ys.min() - pad), min(im.width, xs.max() + pad),
                            min(im.height, ys.max() + pad)))
            t.thumbnail((CW - 4, CH - 18))
            sheet.paste(t, ((c + 1) * CW + 2, y + 2))
            col = (255, 90, 90) if n > 30 else (160, 230, 160)
            dr.text(((c + 1) * CW + 4, y + CH - 14), f"{nm[:22]} {v} holes={n}", fill=col)
            print(f"HOLES {tale} {nm} {v} {n} ({n / max(area, 1):.2%})")
    sheet.save(os.path.join(out, f"{tale}_audit.jpg"), quality=88)
    json.dump(rep, open(os.path.join(out, f"{tale}_audit.json"), "w"), indent=1)
    print("sheet", os.path.join(out, f"{tale}_audit.jpg"))


if __name__ == "__main__":
    main()

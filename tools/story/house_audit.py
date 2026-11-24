#!/usr/bin/env python3
"""House orbit audit sheet (2026-11-23): python3 tools/story/house_audit.py OUT_DIR TALE [--label before] [--strict]

Reads OUT_DIR/<tale>__<house>__<view>.png (solo renders on magenta from tools/story/house_orbit.gd) and
OUT_DIR/<tale>__story*.png. Per view: magenta pixels ENCLOSED by the house (not connected to the image border) are
background showing through the house: seams between front / side / roof, slots under the eaves, open backs, light
leaks. For closed houses they are painted red on the sheet and counted (HOLES <house> <view> px). Open structures
(e.g., octagon_pavilion, gazebo) are labeled (open) and excluded from closed-house red failures. Empty renders
(house_px < 50) are flagged EMPTY and solid-black / missing body textures emit BODY_TEX_WARN. Writes
OUT_DIR/<tale>_audit.jpg and OUT_DIR/<tale>_audit.json.
"""
import argparse, glob, json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
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


def load_kit_open():
    kp = os.path.join(ROOT, "game", "art", "buildings", "kit.json")
    pavilions = {"octagon_pavilion", "gazebo"}
    open_cards = set()
    if os.path.exists(kp):
        kit = json.load(open(kp))
        for k, v in kit.get("kit", {}).items():
            if any(p.get("type") == "pavilion" for p in v.get("parts", [])):
                pavilions.add(k)
        for cid, sw in kit.get("swap", {}).items():
            if sw.get("preset") in pavilions:
                open_cards.add(cid)
    return pavilions, open_cards


def load_story_cards(tale):
    sp = os.path.join(ROOT, "game", "stories", tale, "script.json")
    cards = {}
    if os.path.exists(sp):
        sc = json.load(open(sp))
        for b in sc.get("beats", []):
            spr = b.get("spread") or {}
            for s in spr.get("set", []):
                nm = s.get("name")
                cid = s.get("card")
                if nm and cid:
                    cards[nm] = cid
    return cards


def resolve_card_id(nm, story_cards, bodies):
    m = re.match(r"^tmpl_(.+)_-?\d+_-?\d+$", nm)
    if m:
        return m.group(1)
    if nm in story_cards:
        return story_cards[nm]
    if nm in bodies:
        return nm
    return None


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("out")
    ap.add_argument("tale")
    ap.add_argument("--label", default="")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    out, tale, label = args.out, args.tale, args.label

    pavilions, open_cards = load_kit_open()
    story_cards = load_story_cards(tale)
    bp = os.path.join(ROOT, "game", "art", "atlas", "bodies.json")
    bodies = json.load(open(bp)) if os.path.exists(bp) else {}

    names = []
    for f in sorted(glob.glob(os.path.join(out, f"{tale}__*__front.png"))):
        names.append(os.path.basename(f)[len(tale) + 2:-len("__front.png")])
    rows = max(len(names), len(glob.glob(os.path.join(out, f"{tale}__story_*.png"))))
    sheet = Image.new("RGB", (CW * (len(VIEWS) + 1), CH * max(rows, 1) + 30), (40, 40, 46))
    dr = ImageDraw.Draw(sheet)
    dr.text((6, 8), f"{tale} house orbit audit {label}  (red = background seen through the house; cyan = open pavilion)", fill=(255, 255, 255))
    rep = {}
    sps = sorted(glob.glob(os.path.join(out, f"{tale}__story_*.png")))
    closed_red, front_sub30, empty = 0, 0, 0
    open_names = set()
    tex_checked = set()
    if not names:
        empty += 1
        print(f"EMPTY {tale} NO_RENDERS house_px=0")
        dr.text((6, 36), f"EMPTY: no {tale}__*__front.png files found in {out}", fill=(255, 70, 70))

    for r, nm in enumerate(names):
        y = 30 + r * CH
        if r < len(sps):
            s = Image.open(sps[r]).convert("RGB")
            s.thumbnail((CW, CH))
            sheet.paste(s, (0, y))
            dr.text((4, y + CH - 14), "story " + os.path.basename(sps[r])[len(tale) + 8:-4], fill=(255, 255, 0))
        cid = resolve_card_id(nm, story_cards, bodies)
        is_open = (
            (nm.startswith("kit_") and nm[4:] in pavilions)
            or (nm.startswith("tmpl_") and any(nm.startswith(f"tmpl_{oc}_") for oc in open_cards))
            or (cid in open_cards)
        )
        if is_open:
            open_names.add(nm)
        if not is_open and cid and cid in bodies and cid not in tex_checked:
            tex_checked.add(cid)
            sp = bodies[cid]
            for fk in ("side_file", "roof_file", "back_file", "chimney_file"):
                rel = sp.get(fk)
                if not rel:
                    continue
                tp = os.path.join(ROOT, "game", rel)
                if not os.path.exists(tp):
                    print(f"BODY_TEX_WARN {tale} {nm} {cid} {fk} missing:{rel}")
                    continue
                ta = np.asarray(Image.open(tp).convert("RGB"))
                if int(ta.max()) < 15:
                    print(f"BODY_TEX_WARN {tale} {nm} {cid} {fk} black_tex mean={ta.mean((0, 1)).round(1).tolist()}")

        rep[nm] = {}
        black_render_warned = False
        for c, v in enumerate(VIEWS):
            p = os.path.join(out, f"{tale}__{nm}__{v}.png")
            if not os.path.exists(p):
                continue
            im = Image.open(p).convert("RGB")
            enc, mag, area = holes(im)
            a = np.asarray(im).copy()
            a[mag] = (70, 72, 80)  # neutral backdrop on the sheet
            a[enc] = (210, 175, 65) if is_open else (255, 30, 30)
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
            if area < 50:
                empty += 1
                col = (255, 70, 70)
                txt = f"{nm[:17]} {v} EMPTY({area})"
                print(f"EMPTY {tale} {nm} {v} house_px={area}")
            elif is_open:
                col = (110, 220, 240)
                txt = f"{nm[:15]} {v} (open) {n}"
            else:
                if n > 30:
                    closed_red += 1
                    col = (255, 90, 90)
                else:
                    if v == "front" and n > 0:
                        front_sub30 += 1
                    col = (160, 230, 160)
                txt = f"{nm[:22]} {v} holes={n}"
                if not black_render_warned:
                    nonmag = np.asarray(im)[~mag]
                    black_frac = float((nonmag.max(axis=1) <= 2).mean()) if len(nonmag) else 0.0
                    if black_frac > 0.03:
                        black_render_warned = True
                        print(f"BODY_TEX_WARN {tale} {nm} {v} solid_black_render frac={black_frac:.2%}")
            dr.text(((c + 1) * CW + 4, y + CH - 14), txt, fill=col)
            suffix = " (open)" if is_open else ""
            print(f"HOLES {tale} {nm} {v} {n} ({n / max(area, 1):.2%}){suffix}")
    sheet.save(os.path.join(out, f"{tale}_audit.jpg"), quality=88)
    json.dump(rep, open(os.path.join(out, f"{tale}_audit.json"), "w"), indent=1)
    print("sheet", os.path.join(out, f"{tale}_audit.jpg"))
    print(f"SUMMARY {tale} closed_red={closed_red} front_sub30={front_sub30} open={len(open_names)} empty={empty}")
    if args.strict and (closed_red > 0 or empty > 0):
        sys.exit(1)


if __name__ == "__main__":
    main()

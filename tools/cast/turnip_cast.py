#!/usr/bin/env python3
"""Shared cast for 「커다란 순무」 (turnip, 2026-11-23): a countryside grandpa, grandma, their granddaughter, a puppy, a
tabby cat and a little mouse. Generic farm folk and animals, so they live in game/art/cast/ (skins farm_grandpa,
farm_grandma, farm_girl, puppy, tabby_cat, mouse) for later tales.

  python3 tools/cast/turnip_cast.py            # slice standing-figure sheets, copy, MERGE into catalog.json
  python3 tools/cast/turnip_cast.py --cycles   # (--reslice to slice again) also the drawn cycles (add_cycles.py)

Same rules as tools/cast/sunmoon_cast.py: replaces only standing entries whose skin is one of ROLES (never rebuilds the
catalog; cycles are kept), pieces picked by x order, height = px × the sheet's per-role scale from its reference
figures. The catalog is re-read right before it is written (other agents write it too).
Standing heights (catalog units; the stage scales actors by 1.3 unless the tale gives `height`): grandpa 0.28,
grandma 0.26, girl 0.2; animals standing side-on: puppy 0.115, cat 0.105, mouse 0.05.
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from characters import SLICED
from build_cast import drop_specks

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
GP, GM, GIRL, DOG, CAT, MOUSE = "farm_grandpa", "farm_grandma", "farm_girl", "puppy", "tabby_cat", "mouse"
H = {GP: 0.28, GM: 0.26, GIRL: 0.2, DOG: 0.115, CAT: 0.105, MOUSE: 0.05}
ROLES = set(H)
TAGS = {GP: ["grandpa", "person", "adult", "old_man", "farmer", "western", "walker"],
        GM: ["grandma", "person", "adult", "old_woman", "farmer", "western", "walker"],
        GIRL: ["girl", "person", "child", "western", "walker"],
        DOG: ["dog", "puppy", "animal", "pet", "farm", "walker"],
        CAT: ["cat", "animal", "pet", "farm", "walker"],
        MOUSE: ["mouse", "animal", "small", "walker"]}


def _people(role, extra):
    expr = [(0, role, "pull", "side", "pulling, leaning back, fists forward (faces right)", 0),
            (1, role, "tumble", "side", "tumbled over backwards, legs up (back to the left)", 0),
            (2, role, "surprised", "front", "surprised, hands up", 1),
            (3, role, "cheer", "front", "cheering, both arms up", 0),
            (4, role, "sit_tired", "front", "sitting on the ground, tired (휴우)", 0),
            (5, role, "eat", "front", "eating soup from a bowl", 1)]
    more = [(0, role, "side_walk", "side", "standing, side (faces right)", 1),
            (1, role, "back_walk", "back", "standing, back view", 1),
            (2, role, "call", "front", "calling out, hands cupped at the mouth", 1)] + \
           [(3 + i, role, p, v, lab, 0) for i, (p, v, lab) in enumerate(extra)]
    return expr, more


_gp = _people(GP, [("plant", "side", "kneeling, planting a seed (faces right)"),
                   ("water", "side", "watering with a green can (faces right)"),
                   ("clap", "front", "palms together, ready to work (손바닥을 탁탁)")])
_gm = _people(GM, [("encourage", "front", "fists up, encouraging (같이 해 봐요!)"),
                   ("ladle", "front", "ladling soup, bowl in hand"),
                   ("clap", "front", "clapping with joy")])
_gl = _people(GIRL, [("wave", "front", "eager wave"),
                     ("skip", "side", "skipping, one knee up (faces right)"),
                     ("clap", "front", "clapping with joy")])


def _animal(role, last):
    return [(0, role, "calm", "side", "standing, side (faces right)", 1),
            (1, role, "pull", "side", "pulling on its hind legs, leaning back (faces right)", 0),
            (2, role, "tumble", "side", "tumbled onto its back, paws up", 0),
            (3, role, "surprised", "front", "sitting up surprised", 0),
            (4, role, "happy", "front", "standing up on its hind legs, happy", 0),
            (5, role, "sit_tired", "front", "sitting tired, panting", 0),
            (6, role, "eat", "front", "sitting up with a little bowl", 0),
            (7, role) + last]


SHEETS = {
    "cast_tn_lineup": [(0, GP, "calm", "front", "calm, front", 1), (1, GM, "calm", "front", "calm, hands folded", 1),
                       (2, GIRL, "calm", "front", "calm, front", 1),
                       (3, DOG, "side_walk", "side", "standing, side (faces right)", 1),
                       (4, CAT, "side_walk", "side", "standing, side (faces LEFT on the raw; flipped)", 1),
                       (5, MOUSE, "side_walk", "side", "standing, side (faces right)", 1)],
    "cast_tn_grandpa_expr": _gp[0], "cast_tn_grandpa_more": _gp[1],
    "cast_tn_grandma_expr": _gm[0], "cast_tn_grandma_more": _gm[1],
    "cast_tn_girl_expr": _gl[0], "cast_tn_girl_more": _gl[1],
    "cast_tn_dog_expr": _animal(DOG, ("growl", "side", "growling at the cat (faces right)", 0)),
    "cast_tn_cat_expr": _animal(CAT, ("glare", "side", "glaring, back arched (faces right)", 0)),
    "cast_tn_mouse_expr": _animal(MOUSE, ("brave", "front", "brave, fist up (나도 할래요!)", 0)),
}
MIRROR = {("cast_tn_lineup", 4)}  # the lineup cat faces left
WALK = ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]
CYCLES = {
    "cast_tn_grandpa_walk": (GP, WALK), "cast_tn_grandma_walk": (GM, WALK), "cast_tn_girl_walk": (GIRL, WALK),
    "cast_tn_grandma_run": (GM, ["run_cycle:4:side", "run_front:2:front"]),
    "cast_tn_girl_run": (GIRL, ["run_cycle:4:side", "run_front:2:front"]),
    "cast_tn_dog_walk": (DOG, WALK), "cast_tn_cat_walk": (CAT, WALK), "cast_tn_mouse_walk": (MOUSE, WALK),
}
CYCLE_H = {DOG: 1.0, CAT: 1.0, MOUSE: 1.0}
# sheets with refs only on some rows: the median figure of a role is this fraction of its standing height
NOREF = {}


def sliced_path(sheet, idx, _order="x"):
    """idx-th piece from the left among the real figures (the shared helper drops pieces under 30 % of the tallest:
    the lineup mouse is 30 % of grandpa); specks under 1.5 % of the largest area are skipped."""
    sl = json.load(open(os.path.join(SLICED, sheet, "_slices.json")))["sprites"]
    amax = max(m["size"][0] * m["size"][1] for m in sl)
    big = sorted((m for m in sl if m["size"][0] * m["size"][1] > 0.015 * amax), key=lambda m: m["bbox"][0])
    return os.path.join(SLICED, sheet, big[idx]["id"] + ".webp")


def opaque_h(path):
    a = np.array(Image.open(path).convert("RGBA"))[..., 3] > 128
    ys = np.where(a.any(1))[0]
    return float(ys[-1] - ys[0] + 1)


def main():
    new = []
    for sheet, rows in SHEETS.items():
        raw = f"art_src/cast/raw/{sheet}.png"
        if not os.path.exists(raw):
            print("missing", raw)
            continue
        if "--reslice" in sys.argv or not os.path.exists(f"art_src/cast/sliced/{sheet}/_slices.json"):
            subprocess.run([sys.executable, "tools/atlas/slice_atlas.py", raw, "--out", "art_src/cast/sliced"],
                           check=True, capture_output=True)
            subprocess.run([sys.executable, "tools/atlas/fill_holes.py", raw, f"art_src/cast/sliced/{sheet}"],
                           check=True, capture_output=True)
        refs = [r for r in rows if r[5]]
        role_scale = {}
        for role in {r[1] for r in rows}:
            rr = [r for r in refs if r[1] == role]
            if rr:
                role_scale[role] = H[role] * len(rr) / sum(opaque_h(sliced_path(sheet, r[0], "x")) for r in rr)
        for x, role, pose, view, label, _ in rows:
            cid = f"cast_{role}_{pose}"
            dst = f"game/art/cast/{cid}.webp"
            drop_specks(sliced_path(sheet, x, "x"), dst)
            if (sheet, x) in MIRROR:
                Image.open(dst).transpose(Image.FLIP_LEFT_RIGHT).save(dst, "WEBP", lossless=True, quality=100, method=6)
            w, h = Image.open(dst).size
            sc = role_scale.get(role)
            if sc is None:
                hs = sorted(opaque_h(sliced_path(sheet, r[0], "x")) for r in rows if r[1] == role)
                sc = H[role] * NOREF.get(sheet, 1.0) / hs[len(hs) // 2]
                role_scale[role] = sc
            new.append({"id": cid, "path": f"art/cast/{cid}.webp", "sheet": sheet, "category": "cast", "role": role,
                        "variant": pose, "pose": pose, "view": view,
                        "facing": "right" if view == "side" else view, "label": label,
                        "height_units": round(opaque_h(dst) * sc, 3), "cross_slot": False, "biome": "any",
                        "season": "any", "tags": TAGS[role] + ["turnip", pose, view], "px": [w, h],
                        "hanging": False, "skin": role, "parts": {}})
    # merge-only, re-read right before writing (other agents write this catalog too)
    cat = json.load(open("game/art/cast/catalog.json"))
    ids = {e["id"] for e in new}
    keep = [e for e in cat if not (e.get("role") in ROLES and not e.get("cycle")) and e["id"] not in ids]
    json.dump(keep + new, open("game/art/cast/catalog.json", "w"), ensure_ascii=False, indent=1)
    print(len(new), "standing figures;", len(keep) + len(new), "cast cards")
    if "--cycles" in sys.argv:
        for sheet, (skin, plan) in CYCLES.items():
            if not os.path.exists(f"art_src/cast/raw/{sheet}.png"):
                print("missing", sheet)
                continue
            args = [sys.executable, "tools/cast/add_cycles.py", sheet, skin, *plan, "--h",
                    str(CYCLE_H.get(skin, 0.97)), "--tag", "turnip"]
            if "--noslice" in sys.argv:
                args.append("--noslice")
            subprocess.run(args, check=True)


if __name__ == "__main__":
    main()

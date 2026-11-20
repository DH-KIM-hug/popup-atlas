#!/usr/bin/env python3
"""Shared cast for 「사탕 마녀의 핼러윈」 (witch_candy, 2026-11-19): Dahyun (little wizard), the candy witch, 호박이 the
orange cat and three non-speaking friends (rabbit, bear, fox). Generic enough for other tales (a girl, a kind witch, a
cat, animal kids), so they live in game/art/cast/ and are tagged.

  python3 tools/cast/witch_candy_cast.py          # slice the standing-figure sheets, copy, MERGE into catalog.json
  python3 tools/cast/witch_candy_cast.py --cycles # (--reslice to slice again)  also slice the drawn cycles (tools/cast/add_cycles.py)

Unlike tools/cast/build_cast.py (which rewrites catalog.json from its own tables and would drop the drawn cycles),
this replaces only entries whose role is one of ROLES. Figures are not rigged: every walk is a drawn cycle (side 4,
back 2, front 2); standing figures are single cards.
height_units: a sheet's scale = sum(H of its reference figures) / sum(their px heights); each figure = px × scale.
Standing heights: Dahyun 0.26, witch 0.38, cat sitting 0.13, rabbit 0.28 (ears), bear 0.26, fox 0.27.
Pieces are picked by x order on the sheet (the slicer numbers by rows).
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from characters import sliced_path
from build_cast import drop_specks

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
H = {"dahyun": 0.26, "candy_witch": 0.38, "hobak_cat": 0.13, "rabbit_kid": 0.28, "bear_kid": 0.26, "fox_kid": 0.27}
ROLES = set(H)
TAGS = {"dahyun": ["girl", "person", "child", "wizard", "halloween", "walker"],
        "candy_witch": ["witch", "person", "adult", "kind", "halloween", "walker"],
        "hobak_cat": ["cat", "animal", "orange", "walker"],
        "rabbit_kid": ["rabbit", "animal", "child", "halloween", "walker"],
        "bear_kid": ["bear", "animal", "child", "halloween", "pumpkin_costume", "walker"],
        "fox_kid": ["fox", "animal", "child", "halloween", "walker"]}
D, W, C, R, B, F = "dahyun", "candy_witch", "hobak_cat", "rabbit_kid", "bear_kid", "fox_kid"
# sheet -> list of (x index, role, pose, view, label, is_reference) ; None = piece not used
SHEETS = {
    "cast_wc_lineup": [(0, D, "calm", "front", "calm, front", 1), (1, W, "calm", "front", "calm, hands folded", 1),
                       (2, C, "calm", "front", "sitting calm, front", 1), (3, R, "calm", "front", "calm, front", 1),
                       (4, B, "calm", "front", "calm, front", 1), (5, F, "calm", "front", "calm, front", 1)],
    "cast_dahyun_expr_a": [(0, D, "excited", "front", "excited, holding the pumpkin invitation", 1),
                           (1, D, "yuck", "front", "yuck! tongue out, hand up", 1),
                           (2, D, "eager", "front", "eager, hand up (제가 할게요!)", 1),
                           (3, D, "eat", "front", "eating a candy, delighted", 1),
                           (4, D, "reach", "front", "pointing / reaching to the side", 1)],
    "cast_dahyun_expr_b": [(1, D, "wave", "front", "happy wave", 1), (2, D, "wow", "front", "wow, hands at cheeks", 1),
                           (3, D, "side_walk", "side", "standing, side (faces right)", 1),
                           (4, D, "back_walk", "back", "standing, back view", 1)],
    "cast_dahyun_tf_a": [(0, D, "tf_strawberry", "front", "strawberry magic, standing", 1),
                         (1, D, "tf_strawberry_ball", "front", "strawberry ball, rolling (dizzy face)", 0),
                         (2, D, "tf_duck", "front", "duck feet magic, looking down", 1),
                         (3, D, "tf_fish", "side", "fish tail, swimming in the air (faces right)", 0),
                         (4, D, "tf_frog_jump", "side", "frog legs, mid-leap (faces right)", 0)],
    "cast_dahyun_tf_b": [(0, D, "tf_frog_sit", "front", "frog legs crouched, waving", 0),
                         (1, D, "tf_pumpkin", "front", "pumpkin tummy glowing", 1),
                         (2, D, "tf_bat_up", "side", "bat wings up, flying (faces right)", 0),
                         (3, D, "tf_bat_down", "side", "bat wings down, flying (faces right)", 0)],
    "cast_witch_expr_a": [(0, W, "welcome", "front", "welcome wave (어서 와)", 1),
                          (1, W, "magic", "front", "magic stir: both hands to the left, sparkles", 1),
                          (2, W, "giggle", "front", "giggle, hand at mouth (히히)", 1),
                          (3, W, "surprised", "front", "surprised, hands up (어디 가!)", 1),
                          (4, W, "offer", "front", "offering a candy on her palm", 1)],
    "cast_witch_expr_b": [(1, W, "tf_pumpkin", "front", "pumpkin magic tummy", 0),
                          (2, W, "two_candies", "front", "two candies held up (나는 두 개!)", 1),
                          (3, W, "side_walk", "side", "standing, side (faces right)", 1),
                          (4, W, "back_walk", "back", "standing, back view", 1)],
    "cast_cat_expr": [(0, C, "sit", "front", "sitting", 1), (1, C, "meow", "front", "meowing (냐옹!)", 1),
                      (2, C, "nose", "front", "paw over the nose (냄새!)", 1),
                      (3, C, "startled", "side", "startled, arched back (faces right)", 0),
                      (5, C, "tf_fish", "side", "fish tail magic, floating (faces right)", 0)],
    "cast_friends_expr_a": [(0, R, "cheer", "front", "cheering, arms up", 1), (1, B, "cheer", "front", "cheering", 1),
                            (2, F, "cheer", "front", "cheering", 1),
                            (3, R, "tf_frog", "front", "frog legs magic, crouched", 0),
                            (4, B, "tf_duck", "front", "duck feet magic, waddling", 0),
                            (5, F, "tf_bat", "front", "bat wings magic, hovering", 0)],
    "cast_friends_expr_b": [(3, R, "side_walk", "side", "standing, side (faces right)", 1),
                            (4, B, "side_walk", "side", "standing, side (faces right)", 1),
                            (5, F, "side_walk", "side", "standing, side (faces right)", 1)],
    # v5: surprised with the NEW ghost-candy mouth drawn in natively (the reveal uses these, not the arms-up pose)
    "cast_wc_surprised_black": [(0, D, "wow_black", "front", "surprised, ghost-candy mouth", 1),
                                (1, W, "surprised_black", "front", "surprised, ghost-candy mouth", 1),
                                (2, C, "surprised_black", "front", "surprised sitting, ghost-candy mouth", 1),
                                (3, R, "surprised_black", "front", "surprised, ghost-candy mouth", 1),
                                (4, B, "surprised_black", "front", "surprised, ghost-candy mouth", 1),
                                (5, F, "surprised_black", "front", "surprised, ghost-candy mouth", 1)],
    "cast_wc_ghost_lips": [(0, D, "ghost", "front", "ghost play, black lips, arms up", 1),
                           (1, W, "ghost", "front", "ghost play, black lips", 1),
                           (2, C, "ghost", "front", "ghost play on hind legs, black mouth", 0),
                           (3, R, "ghost", "front", "ghost play, black lips", 1),
                           (4, B, "ghost", "front", "ghost play, black lips", 1),
                           (5, F, "ghost", "front", "ghost play, black lips", 1)],
}
# drawn cycles: sheet -> (skin, [cycle:n:view ...]) for tools/cast/add_cycles.py
CYCLES = {
    "cast_dahyun_walk_cycle": (D, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_dahyun_ghost_cycle": (D, ["ghost_cycle:4:side", "ghost_front:2:front"]),
    "cast_dahyun_duck_cycle": (D, ["duck_cycle:4:side"]),
    "cast_witch_walk_cycle": (W, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_witch_ghost_cycle": (W, ["ghost_cycle:4:side", "ghost_front:2:front"]),
    "cast_cat_walk_cycle": (C, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_cat_ghost_cycle": (C, ["ghost_cycle:4:side", "ghost_front:2:front"]),
    "cast_rabbit_walk_cycle": (R, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_rabbit_ghost_cycle": (R, ["ghost_cycle:4:side", "ghost_front:2:front"]),
    "cast_bear_walk_cycle": (B, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_bear_ghost_cycle": (B, ["ghost_cycle:4:side", "ghost_front:2:front"]),
    "cast_fox_walk_cycle": (F, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_fox_ghost_cycle": (F, ["ghost_cycle:4:side", "ghost_front:2:front"]),
}
# the cat's walking figure is shorter than it sits (on four legs): cycles relative to the sitting calm card
CYCLE_H = {C: 0.85}


def opaque_h(path):
    a = np.array(Image.open(path).convert("RGBA"))[..., 3] > 128
    ys = np.where(a.any(1))[0]
    return float(ys[-1] - ys[0] + 1)


def main():
    cat = json.load(open("game/art/cast/catalog.json"))
    keep = [e for e in cat if not (e.get("role") in ROLES and not e.get("cycle"))]
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
        scale = sum(H[r[1]] for r in refs) / sum(opaque_h(sliced_path(sheet, r[0], "x")) for r in refs)
        # a sheet with several characters (lineup, ghost lips): each role with its own reference uses its own scale
        role_scale = {}
        for role in {r[1] for r in refs}:
            rr = [r for r in refs if r[1] == role]
            role_scale[role] = H[role] * len(rr) / sum(opaque_h(sliced_path(sheet, r[0], "x")) for r in rr)
        for x, role, pose, view, label, _ in rows:
            cid = f"cast_{role}_{pose}"
            dst = f"game/art/cast/{cid}.webp"
            drop_specks(sliced_path(sheet, x, "x"), dst)
            w, h = Image.open(dst).size
            new.append({"id": cid, "path": f"art/cast/{cid}.webp", "sheet": sheet, "category": "cast", "role": role,
                        "variant": pose, "pose": pose, "view": view,
                        "facing": "right" if view == "side" else view, "label": label,
                        "height_units": round(opaque_h(dst) * role_scale.get(role, scale), 3), "cross_slot": False, "biome": "any",
                        "season": "any", "tags": TAGS[role] + ["witch_candy", pose, view], "px": [w, h],
                        "hanging": False, "skin": role, "parts": {}})
    json.dump(keep + new, open("game/art/cast/catalog.json", "w"), ensure_ascii=False, indent=1)
    print(len(new), "standing figures;", len(keep) + len(new), "cast cards")
    if "--cycles" in sys.argv:
        for sheet, (skin, plan) in CYCLES.items():
            if not os.path.exists(f"art_src/cast/raw/{sheet}.png"):
                print("missing", sheet)
                continue
            subprocess.run([sys.executable, "tools/cast/add_cycles.py", sheet, skin, *plan, "--h",
                            str(CYCLE_H.get(skin, 0.97)), "--tag", "witch_candy"], check=True)


if __name__ == "__main__":
    main()

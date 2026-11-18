#!/usr/bin/env python3
"""Copy the sliced cast sheets (art_src/cast/sliced/<sheet>/<sheet>_NN.webp, from tools/atlas/slice_atlas.py) into
game/art/cast/<id>.webp under their cast ids and write game/art/cast/catalog.json (same schema as the atlas catalog,
category "cast", plus role/variant/expression and parts for rigged figures).

  for s in cast_traveller cast_traveller_props cast_sun_v2 cast_wind_v2 cast_traveller_expr_a cast_traveller_expr_b; do
    python3 tools/atlas/slice_atlas.py art_src/cast/raw/$s.png --out art_src/cast/sliced; done
  python3 tools/cast/build_cast.py && python3 tools/cast/cut_cast_rig.py && python3 tools/cast/contact_cast.py
"""
import json, os, shutil
import numpy as np
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cut_cast_rig import components
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SL = os.path.join(ROOT, "art_src", "cast", "sliced")
OUT = os.path.join(ROOT, "game", "art", "cast")
RIG_PARTS = ["body", "hips", "leg_l", "leg_r"]

# (sheet, index) -> entry. height_units: traveller 0.36 standing (BRIEF), clothes scaled to him, sky cards match the
# SkyHanger card_height used on the bench (sun 0.5, wind 0.36).
T = ["traveller", "generic", "person", "walker", "coat", "hat", "winter"]
CAST = [
    ("cast_traveller", 0, "cast_traveller_coat", 0.36, "traveller", "coat_hat", T, True, "thick red folk-art coat + brown hat, standing"),
    ("cast_traveller", 1, "cast_traveller_coat_nohat", 0.345, "traveller", "coat", T, True, "coat, no hat"),
    ("cast_traveller", 2, "cast_traveller_coat_hold", 0.355, "traveller", "coat_hat_hold", T + ["cold", "wind"], True, "clutching the coat shut in the wind"),
    ("cast_traveller", 3, "cast_traveller_nocoat", 0.36, "traveller", "shirt_hat", ["traveller", "generic", "person", "walker", "hat", "summer", "warm"], True, "coat off (ending): green shirt, suspenders, hat"),
    ("cast_traveller", 4, "cast_traveller_nocoat_nohat", 0.345, "traveller", "shirt", ["traveller", "generic", "person", "walker", "summer", "warm"], True, "coat and hat off, warm"),
    # 2026-11-18 expression figures (user: he smiled in every beat). Same design and stance, rigged like the above.
    ("cast_traveller_expr_a", 0, "cast_traveller_coat_surprised", 0.36, "traveller", "coat_hat_surprised", T + ["surprised"], True, "startled: wide eyes, open mouth, hands up"),
    ("cast_traveller_expr_a", 1, "cast_traveller_coat_nohat_surprised", 0.345, "traveller", "coat_surprised", T + ["surprised"], True, "hat just blew off: hands to his bare head, mouth open"),
    ("cast_traveller_expr_a", 2, "cast_traveller_coat_nohat_cold", 0.34, "traveller", "coat_cold", T + ["cold", "wind", "shiver"], True, "freezing: hugging himself, teeth chattering, icy cheeks"),
    ("cast_traveller_expr_a", 3, "cast_traveller_coat_calm", 0.36, "traveller", "coat_hat_calm", T + ["calm"], True, "walking face: calm, not grinning"),
    ("cast_traveller_expr_a", 4, "cast_traveller_coat_nohat_calm", 0.345, "traveller", "coat_calm", T + ["calm"], True, "walking face, no hat"),
    ("cast_traveller_expr_b", 0, "cast_traveller_coat_open_hot", 0.36, "traveller", "coat_open_hat_hot", T + ["hot", "sun", "sweat"], True, "warm: coat unbuttoned, flushed, sweat drops, panting"),
    ("cast_traveller_expr_b", 1, "cast_traveller_coat_open_fan", 0.345, "traveller", "coat_open_fan", T + ["hot", "sun", "sweat"], True, "very hot: fanning with his hat, tongue out (hat+hand cut as a 'fan' part)"),
    ("cast_traveller_expr_b", 2, "cast_traveller_nocoat_relieved", 0.36, "traveller", "shirt_hat_relieved", ["traveller", "generic", "person", "walker", "hat", "summer", "warm", "relieved"], True, "coat off, eyes closed, content (cool at last)"),
    ("cast_traveller_expr_b", 3, "cast_traveller_nocoat_nohat_relieved", 0.345, "traveller", "shirt_relieved", ["traveller", "generic", "person", "walker", "summer", "warm", "relieved"], True, "coat and hat off, content"),
    ("cast_traveller_expr_b", 4, "cast_traveller_nocoat_calm", 0.36, "traveller", "shirt_hat_calm", ["traveller", "generic", "person", "walker", "hat", "summer", "calm"], True, "shirt and hat, calm walking face"),
    ("cast_traveller_props", 0, "cast_coat_hung", 0.22, "coat", "flat", ["traveller", "coat", "clothing", "prop"], False, "the coat flat, empty (hung / held up)"),
    ("cast_traveller_props", 1, "cast_coat_folded", 0.12, "coat", "folded", ["traveller", "coat", "clothing", "prop", "in_hand"], False, "the coat folded over, as carried on an arm"),
    ("cast_traveller_props", 2, "cast_coat_ground", 0.08, "coat", "ground", ["traveller", "coat", "clothing", "prop", "on_ground"], False, "the coat dropped on the ground"),
    ("cast_traveller_props", 3, "cast_hat", 0.07, "hat", "front", ["traveller", "hat", "clothing", "prop"], False, "the hat, front"),
    ("cast_traveller_props", 4, "cast_hat_ground", 0.07, "hat", "ground", ["traveller", "hat", "clothing", "prop", "on_ground"], False, "the hat tipped on the ground"),
    ("cast_sun_v2", 0, "cast_sun_smile", 0.5, "sun", "smile", ["sun", "sky", "hanging", "weather", "face"], False, "sun, gentle smile"),
    ("cast_sun_v2", 1, "cast_sun_proud", 0.5, "sun", "proud", ["sun", "sky", "hanging", "weather", "face"], False, "sun, proud wink"),
    ("cast_sun_v2", 2, "cast_sun_beaming", 0.5, "sun", "beaming_hot", ["sun", "sky", "hanging", "weather", "face", "hot"], False, "sun, beaming hot"),
    ("cast_wind_v2", 0, "cast_wind_boast", 0.36, "wind", "boast", ["wind", "cloud", "sky", "hanging", "weather", "face"], False, "wind cloud, boasting smirk"),
    ("cast_wind_v2", 1, "cast_wind_blow", 0.36, "wind", "blowing_hard", ["wind", "cloud", "sky", "hanging", "weather", "face"], False, "wind cloud, blowing hard (to the left)"),
    ("cast_wind_v2", 2, "cast_wind_tired", 0.32, "wind", "tired", ["wind", "cloud", "sky", "hanging", "weather", "face"], False, "wind cloud, tired"),
]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cat = []
    for sheet, idx, cid, hu, role, var, tags, rigged, label in CAST:
        src = os.path.join(SL, sheet, f"{sheet}_{idx:02d}.webp")
        dst = os.path.join(OUT, cid + ".webp")
        if sheet.startswith("cast_traveller_expr"):
            # drop printed motion lines / specks that float free of the figure (a die-cut card is one piece)
            im = np.array(Image.open(src).convert("RGBA"))
            lab, n = components(im[..., 3] > 24)
            if n > 1:
                sizes = np.bincount(lab.ravel())[1:]
                main = 1 + int(np.argmax(sizes))
                for i in range(1, n + 1):
                    if i != main and sizes[i - 1] < 0.03 * sizes.max():
                        im[lab == i, 3] = 0
            Image.fromarray(im).save(dst, "WEBP", lossless=True, quality=100, method=6)
        else:
            shutil.copyfile(src, dst)
        w, h = Image.open(dst).size
        e = {"id": cid, "path": f"art/cast/{cid}.webp", "sheet": sheet, "category": "cast", "role": role,
             "variant": var, "label": label, "height_units": hu, "cross_slot": False, "biome": "any", "season": "any",
             "tags": tags, "px": [w, h], "hanging": role in ("sun", "wind")}
        if rigged:
            e["rig"] = "art/cast/rig/rig.json"
            e["skin"] = "traveller"
            e["parts"] = {p: f"art/cast/rig/{cid}_{p}.png" for p in RIG_PARTS}
            if cid == "cast_traveller_coat_open_fan":
                e["parts"]["fan"] = f"art/cast/rig/{cid}_fan.png"
        else:
            e["parts"] = {}
        cat.append(e)
    json.dump(cat, open(os.path.join(OUT, "catalog.json"), "w"), ensure_ascii=False, indent=1)
    print(len(cat), "cast cards ->", os.path.join(OUT, "catalog.json"))
